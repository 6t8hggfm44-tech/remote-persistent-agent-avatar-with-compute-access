"""SQLite persistence and atomic transitions for the bounded local preview."""

import hashlib
import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_PERSONA = {
    "name": "Companion",
    "role": "A thoughtful companion for ideas, plans, and creative work.",
    "tone": "warm",
    "response_length": "balanced",
    "instructions": "Be helpful, clear, and candid. Ask when something important is unclear.",
}


class StoreError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def validate_text(value, label, limit, allow_empty=False):
    if not isinstance(value, str):
        raise StoreError("{} must be text.".format(label))
    value = value.strip()
    if (not value and not allow_empty) or len(value) > limit:
        raise StoreError("{} must contain {}–{} characters.".format(label, 0 if allow_empty else 1, limit))
    if any(ord(character) < 32 and character not in "\n\r\t" for character in value):
        raise StoreError("{} contains unsupported control characters.".format(label))
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise StoreError("{} contains invalid Unicode characters.".format(label))
    return value


def validate_persona(persona):
    if not isinstance(persona, dict) or set(persona) != set(DEFAULT_PERSONA):
        raise StoreError("Provide exactly name, role, tone, response_length, and instructions.")
    result = {
        "name": validate_text(persona["name"], "Name", 40),
        "role": validate_text(persona["role"], "Role", 120),
        "instructions": validate_text(persona["instructions"], "Instructions", 2000, True),
        "tone": persona["tone"],
        "response_length": persona["response_length"],
    }
    if result["tone"] not in ("warm", "direct", "thoughtful", "playful"):
        raise StoreError("Choose a supported tone.")
    if result["response_length"] not in ("short", "balanced", "detailed"):
        raise StoreError("Choose a supported response length.")
    return result


class Store:
    """One short-lived connection per transaction; safe across server threads.

    Data stays in data_dir/state.sqlite3. A task's persona and conversation
    generation are captured when queued. Cancellation and completion compete
    in transactions; only the winner can change state or publish a response.
    """

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.data_dir / "state.sqlite3"
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued','running','completed','cancelled','failed')),
                    kind TEXT NOT NULL CHECK(kind IN ('mock_reply','draft')),
                    created_at TEXT NOT NULL,
                    result TEXT,
                    payload TEXT NOT NULL,
                    request_id TEXT UNIQUE,
                    claim_token TEXT
                );
                CREATE TABLE IF NOT EXISTS messages (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    provider TEXT NOT NULL DEFAULT 'preview' CHECK(provider IN ('preview','openai')),
                    UNIQUE(task_id, role)
                );
                CREATE INDEX IF NOT EXISTS pending_tasks ON tasks(status, created_at);
            """)
            connection.execute("INSERT OR IGNORE INTO settings VALUES ('persona', ?)", (json.dumps(DEFAULT_PERSONA),))
            connection.execute("INSERT OR IGNORE INTO settings VALUES ('conversation_epoch', '0')")
        with self._connection(write=True) as connection:
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(messages)")}
            if "provider" not in columns:
                connection.execute("ALTER TABLE messages ADD COLUMN provider TEXT NOT NULL DEFAULT 'preview' CHECK(provider IN ('preview','openai'))")
        os.chmod(self.path, 0o600)

    @contextmanager
    def _connection(self, write=False):
        connection = sqlite3.connect(str(self.path), timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA secure_delete=ON")
        try:
            if write:
                connection.execute("BEGIN IMMEDIATE")
            yield connection
            if write:
                connection.execute("COMMIT")
        except Exception:
            if write and connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @staticmethod
    def _setting(connection, key):
        return connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()[0]

    @staticmethod
    def _task(row):
        task = {key: row[key] for key in ("id", "title", "status", "kind", "created_at", "result")}
        task["provider"] = json.loads(row["payload"]).get("provider", "preview")
        return task

    def health(self):
        with self._connection() as connection:
            return connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    def get_state(self):
        with self._connection() as connection:
            connection.execute("BEGIN")
            persona = json.loads(self._setting(connection, "persona"))
            conversation_epoch = int(self._setting(connection, "conversation_epoch"))
            messages = [dict(row) for row in connection.execute(
                "SELECT id, role, content, created_at, provider FROM messages ORDER BY sequence")]
            tasks = [self._task(row) for row in connection.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC, rowid DESC")]
            connection.execute("COMMIT")
        return {
            "persona": persona,
            "conversation_epoch": conversation_epoch,
            "messages": messages,
            "tasks": tasks,
            "mode": "preview",
            "capabilities": {"ai": False, "voice": False, "avatar": False, "ea": False},
        }

    def update_persona(self, persona):
        persona = validate_persona(persona)
        with self._connection(write=True) as connection:
            connection.execute("UPDATE settings SET value = ? WHERE key = 'persona'", (json.dumps(persona),))
        return persona

    def enqueue_message(self, content, request_id, conversation_epoch=None, provider="preview", live_can_send=True):
        content = validate_text(content, "Message", 4000)
        if provider not in ("preview", "openai"):
            raise StoreError("Unsupported reply provider.")
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if not isinstance(request_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", request_id):
            raise StoreError("request_id must be 8–128 letters, numbers, underscores, or hyphens.")
        with self._connection(write=True) as connection:
            previous = connection.execute("SELECT id, payload FROM tasks WHERE request_id = ?", (request_id,)).fetchone()
            if previous:
                old_payload = json.loads(previous["payload"])
                old_hash = old_payload.get("content_hash") or hashlib.sha256(old_payload["content"].encode("utf-8")).hexdigest()
                if old_hash != content_hash:
                    raise StoreError("This request_id was already used for a different message.", 409)
                if old_payload.get("provider", "preview") != provider:
                    raise StoreError("This request_id was already used with a different reply provider.", 409)
                return previous["id"]
            current_epoch = int(self._setting(connection, "conversation_epoch"))
            if conversation_epoch is not None and (type(conversation_epoch) is not int or conversation_epoch != current_epoch):
                raise StoreError("This conversation changed. Refresh and resend your message if you still want to send it.", 409)
            if provider == "openai":
                if not live_can_send:
                    raise StoreError("The local API test allowance cannot cover another reply. Increase the authorized allowance before continuing.", 403)
                pending = connection.execute("SELECT payload FROM tasks WHERE kind='mock_reply' AND status IN ('queued','running')")
                if any(json.loads(row["payload"]).get("provider", "preview") == "openai" for row in pending):
                    raise StoreError("Wait for the current AI reply to finish, or cancel it before sending another message.", 409)
            task_id = str(uuid.uuid4())
            now = timestamp()
            payload = {
                "content": content,
                "content_hash": content_hash,
                "persona": json.loads(self._setting(connection, "persona")),
                "epoch": self._setting(connection, "conversation_epoch"),
                "provider": provider,
            }
            connection.execute(
                "INSERT INTO tasks (id,title,status,kind,created_at,payload,request_id) VALUES (?,?,'queued','mock_reply',?,?,?)",
                (task_id, "AI reply" if provider == "openai" else "Preview reply", now, json.dumps(payload), request_id),
            )
            connection.execute(
                "INSERT INTO messages (id,role,content,created_at,task_id,provider) VALUES (?,'user',?,?,?,?)",
                (str(uuid.uuid4()), content, now, task_id, provider),
            )
            return task_id

    def enqueue_task(self, title, kind="draft"):
        title = validate_text(title, "Task title", 200)
        if kind != "draft":
            raise StoreError("Only the local draft task is supported.")
        with self._connection(write=True) as connection:
            task_id = str(uuid.uuid4())
            payload = {"persona": json.loads(self._setting(connection, "persona"))}
            connection.execute(
                "INSERT INTO tasks (id,title,status,kind,created_at,payload) VALUES (?,?,'queued','draft',?,?)",
                (task_id, title, timestamp(), json.dumps(payload)),
            )
        return task_id

    def cancel_task(self, task_id):
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise StoreError("Task not found.", 404)
            if row["status"] in ("queued", "running"):
                connection.execute("UPDATE tasks SET status='cancelled', claim_token=NULL WHERE id=?", (task_id,))
            return self._task(connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())

    def reset_conversation(self):
        with self._connection(write=True) as connection:
            connection.execute("UPDATE tasks SET status='cancelled', claim_token=NULL WHERE kind='mock_reply' AND status IN ('queued','running')")
            connection.execute("DELETE FROM messages")
            # Keep request identifiers and fingerprints so stale retries cannot
            # resurrect a cleared conversation, but remove its active text rows.
            for row in connection.execute("SELECT id,payload FROM tasks WHERE kind='mock_reply'").fetchall():
                old_payload = json.loads(row["payload"])
                content_hash = old_payload.get("content_hash") or hashlib.sha256(old_payload.get("content", "").encode("utf-8")).hexdigest()
                redacted = {"content_hash": content_hash, "provider": old_payload.get("provider", "preview")}
                connection.execute("UPDATE tasks SET payload=?,result=NULL WHERE id=?", (json.dumps(redacted), row["id"]))
            epoch = int(self._setting(connection, "conversation_epoch")) + 1
            connection.execute("UPDATE settings SET value=? WHERE key='conversation_epoch'", (str(epoch),))

    def recover_pending(self):
        """Recover local work; never automatically repeat a possibly paid call."""
        with self._connection(write=True) as connection:
            changed = 0
            for row in connection.execute("SELECT id,status,payload FROM tasks WHERE status IN ('queued','running')").fetchall():
                if json.loads(row["payload"]).get("provider", "preview") == "openai":
                    connection.execute("UPDATE tasks SET status='failed',claim_token=NULL,result=? WHERE id=?", (
                        "Interrupted AI request was not retried; it may have been billed.", row["id"]))
                    changed += 1
                elif row["status"] == "running":
                    connection.execute("UPDATE tasks SET status='queued',claim_token=NULL WHERE id=?", (row["id"],))
                    changed += 1
            return changed

    def cancel_live_tasks(self):
        """Fence queued/in-flight live replies when the connection is removed."""
        with self._connection(write=True) as connection:
            cancelled = 0
            for row in connection.execute("SELECT id,payload FROM tasks WHERE status IN ('queued','running')").fetchall():
                if json.loads(row["payload"]).get("provider", "preview") == "openai":
                    connection.execute("UPDATE tasks SET status='cancelled',claim_token=NULL WHERE id=?", (row["id"],))
                    cancelled += 1
            return cancelled

    def is_task_active(self, task):
        with self._connection() as connection:
            row = connection.execute("SELECT status,claim_token,payload FROM tasks WHERE id=?", (task["id"],)).fetchone()
            if row is None or row["status"] != "running" or row["claim_token"] != task["claim_token"]:
                return False
            payload = json.loads(row["payload"])
            return "epoch" not in payload or payload["epoch"] == self._setting(connection, "conversation_epoch")

    def get_reply_context(self, task):
        """Return up to 12 prior live messages, followed by this task's user turn.

        Sequence bounds prevent later messages entering a queued request. The
        current conversation epoch and claim must still be active. Scripted
        preview messages are never included in a paid model request.
        """
        with self._connection() as connection:
            connection.execute("BEGIN")
            row = connection.execute("SELECT status,claim_token,payload FROM tasks WHERE id=?", (task["id"],)).fetchone()
            if row is None or row["status"] != "running" or row["claim_token"] != task["claim_token"]:
                raise StoreError("This AI request is no longer active.", 409)
            payload = json.loads(row["payload"])
            if payload.get("epoch") != self._setting(connection, "conversation_epoch"):
                raise StoreError("This conversation changed before the AI request started.", 409)
            current = connection.execute("SELECT sequence,role,content,provider FROM messages WHERE task_id=? AND role='user' AND provider='openai'", (task["id"],)).fetchone()
            if current is None:
                raise StoreError("This AI request has no current user message.", 409)
            earlier = connection.execute("SELECT role,content,provider FROM messages WHERE provider='openai' AND sequence<? ORDER BY sequence DESC LIMIT 12", (current["sequence"],)).fetchall()
            history = [dict(message) for message in reversed(earlier)]
            history.append({key: current[key] for key in ("role", "content", "provider")})
            connection.execute("COMMIT")
            return history

    def claim_next_task(self):
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM tasks WHERE status='queued' ORDER BY created_at, rowid LIMIT 1").fetchone()
            if row is None:
                return None
            task = dict(row)
            task["claim_token"] = str(uuid.uuid4())
            task["status"] = "running"
            task["payload"] = json.loads(task["payload"])
            connection.execute("UPDATE tasks SET status='running',claim_token=? WHERE id=?", (task["claim_token"], task["id"]))
            return task

    def complete_task(self, task, result):
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id=?", (task["id"],)).fetchone()
            if row is None or row["status"] != "running" or row["claim_token"] != task["claim_token"]:
                return False
            payload = json.loads(row["payload"])
            if row["kind"] == "mock_reply":
                if payload["epoch"] != self._setting(connection, "conversation_epoch"):
                    connection.execute("UPDATE tasks SET status='cancelled',claim_token=NULL WHERE id=?", (task["id"],))
                    return False
                connection.execute(
                    "INSERT INTO messages (id,role,content,created_at,task_id,provider) VALUES (?,'assistant',?,?,?,?)",
                    (str(uuid.uuid4()), result, timestamp(), task["id"], payload.get("provider", "preview")),
                )
            connection.execute("UPDATE tasks SET status='completed',result=?,claim_token=NULL WHERE id=?", (result, task["id"]))
            return True

    def fail_task(self, task, message="The local task could not finish."):
        with self._connection(write=True) as connection:
            connection.execute(
                "UPDATE tasks SET status='failed',result=?,claim_token=NULL WHERE id=? AND status='running' AND claim_token=?",
                (message, task["id"], task["claim_token"]),
            )
