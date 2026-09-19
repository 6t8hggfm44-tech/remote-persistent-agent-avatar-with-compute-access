"""Explicit local memory, report snapshots, and bounded project references.

This module never fetches a URL, scans arbitrary paths, imports an external
repository, or treats source text as executable instructions.
"""

import hashlib
import json
import re
import uuid
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .store import StoreError, timestamp, validate_text


MEMORY_TEXT_BYTES = 6000
REPORT_TEXT_BYTES = 8000
PROJECT_TEXT_BYTES = 4000
MAX_CONTEXT_MEMORIES = 8
MAX_CONTEXT_PROJECT_DOCUMENTS = 3
MAX_PROJECT_FILE_BYTES = 128 * 1024
PROJECT_FILES = (
    "README.md",
    "docs/01-system-design.md",
    "docs/02-backend-workflow.md",
    "docs/03-workstation-workflow.md",
    "docs/04-avatar-project.md",
    "docs/05-integration-contracts.md",
    "docs/07-validation-and-operations.md",
    "docs/09-local-prototype.md",
    "docs/10-live-text-connection.md",
    "docs/11-memory-and-repository-conversations.md",
)
_STOP_WORDS = {"the", "and", "for", "that", "this", "with", "from", "what", "how", "can", "you", "are", "about", "please", "report", "project", "repo", "repository", "discuss", "tell", "summarize"}


def _digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _clip(content, limit):
    encoded = content.encode("utf-8")
    return encoded[:max(0, limit)].decode("utf-8", errors="ignore"), len(encoded) > limit


def _terms(content):
    return set(re.findall(r"[a-z0-9_]{3,}", content.lower())) - _STOP_WORDS


def _windows(content, query, max_windows=3):
    """Choose deterministic contiguous line ranges with exact 1-based bounds."""
    lines = content.splitlines() or [""]
    terms = _terms(query)
    ranked = sorted(((len(_terms(line) & terms), index) for index, line in enumerate(lines)), key=lambda pair: (-pair[0], pair[1]))
    if not ranked or ranked[0][0] == 0:
        return [(1, len(lines), None, terms)], 0
    ranges = []
    for score, index in ranked:
        if not score or len(ranges) >= max_windows:
            break
        start, end = max(0, index - 2), min(len(lines), index + 3)
        if any(start < old_end and end > old_start for old_start, old_end, _ in ranges):
            continue
        ranges.append((start, end, index))
    # Keep relevance order so a weaker earlier match cannot consume the budget
    # before the strongest evidence later in the document.
    return [(start + 1, end, index + 1, terms) for start, end, index in ranges], ranked[0][0]


def _fit_window(lines, start, end, anchor, terms, budget):
    """Fit a contiguous range while giving its matching line first priority."""
    partial_line = False
    if anchor is not None:
        while len("\n".join(lines[start - 1:end]).encode("utf-8")) > budget and (start < anchor or end > anchor):
            # Remove distant context before ever trimming the matched line.
            if start < anchor and (end == anchor or anchor - start >= end - anchor):
                start += 1
            else:
                end -= 1
    text = "\n".join(lines[start - 1:end])
    if anchor is not None and start == end and len(text.encode("utf-8")) > budget:
        match = next((match for match in re.finditer(r"[A-Za-z0-9_]{3,}", text) if match.group().lower() in terms), None)
        if match:
            raw = text.encode("utf-8")
            offset = max(0, len(text[:match.start()].encode("utf-8")) - budget // 3)
            text = raw[offset:offset + budget].decode("utf-8", errors="ignore")
            partial_line = True
    excerpt, clipped = _clip(text, budget)
    actual_end = min(end, start + (len(excerpt.splitlines()) or 1) - 1)
    return start, actual_end, excerpt, clipped, partial_line or (clipped and not excerpt.endswith("\n"))


class Knowledge:
    def __init__(self, store, project_root=None):
        self.store = store
        self.project_root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parent.parent
        # Store's idempotent migration owns the tables, including when multiple
        # Knowledge instances are constructed by the server and model adapter.

    @staticmethod
    def _report_metadata(row):
        return {key: row[key] for key in ("id", "title", "source_name", "source_url", "report_date", "sha256", "created_at")}

    def library(self):
        with self.store._connection() as connection:
            connection.execute("BEGIN")
            memories = [dict(row) for row in connection.execute("SELECT * FROM memories ORDER BY updated_at DESC,id")]
            reports = [self._report_metadata(row) for row in connection.execute("SELECT id,title,source_name,source_url,report_date,sha256,created_at FROM reports ORDER BY report_date DESC,created_at DESC,id")]
            epoch = int(self.store._setting(connection, "knowledge_epoch"))
            connection.execute("COMMIT")
        return {"memories": memories, "reports": reports, "knowledge_epoch": epoch}

    def _invalidate(self, connection):
        epoch = int(self.store._setting(connection, "knowledge_epoch")) + 1
        connection.execute("UPDATE settings SET value=? WHERE key='knowledge_epoch'", (str(epoch),))
        for row in connection.execute("SELECT id,payload FROM tasks WHERE status IN ('queued','running')").fetchall():
            if json.loads(row["payload"]).get("provider", "preview") == "openai":
                connection.execute("UPDATE tasks SET status='cancelled',claim_token=NULL WHERE id=?", (row["id"],))

    def create_memory(self, title, content):
        title = validate_text(title, "Memory title", 120)
        content = validate_text(content, "Memory content", 1000)
        now = timestamp()
        memory = {"id": str(uuid.uuid4()), "title": title, "content": content, "created_at": now, "updated_at": now}
        with self.store._connection(write=True) as connection:
            if connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0] >= 80:
                raise StoreError("The local memory library is full (80 notes). Remove a note before adding another.", 409)
            connection.execute("INSERT INTO memories VALUES (?,?,?,?,?)", tuple(memory[key] for key in ("id", "title", "content", "created_at", "updated_at")))
            self._invalidate(connection)
        return memory

    def delete_memory(self, memory_id):
        with self.store._connection(write=True) as connection:
            if connection.execute("DELETE FROM memories WHERE id=?", (memory_id,)).rowcount == 0:
                raise StoreError("Memory not found.", 404)
            self._invalidate(connection)

    def create_report(self, title, source_name, source_url, report_date, content):
        title = validate_text(title, "Report title", 160)
        source_name = validate_text(source_name, "Source name", 80)
        source_url = validate_text(source_url, "Source URL", 500, True)
        # Validate without normalizing the snapshot: its digest and line numbers
        # must describe exactly the supplied Unicode text, including end lines.
        validate_text(content, "Report content", 60000)
        if len(content) > 60000 or any(ord(character) < 32 and character not in "\n\r\t" for character in content):
            raise StoreError("Report content must contain at most 60000 characters and no unsupported control characters.")
        if source_url:
            try:
                parsed = urlsplit(source_url)
                if parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None or any(character.isspace() for character in source_url):
                    raise ValueError
                parsed.port  # Reject malformed ports without contacting the host.
            except ValueError:
                raise StoreError("Source URL must be an HTTPS link without credentials, or blank.") from None
        try:
            if not isinstance(report_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date):
                raise ValueError
            date.fromisoformat(report_date)
        except ValueError:
            raise StoreError("Report date must be a valid date in YYYY-MM-DD format.") from None
        report = {"id": str(uuid.uuid4()), "title": title, "source_name": source_name, "source_url": source_url, "report_date": report_date, "content": content, "sha256": _digest(content), "created_at": timestamp()}
        with self.store._connection(write=True) as connection:
            if connection.execute("SELECT COUNT(*) FROM reports").fetchone()[0] >= 60:
                raise StoreError("The local report library is full (60 reports). Remove a report before adding another.", 409)
            connection.execute("INSERT INTO reports VALUES (?,?,?,?,?,?,?,?)", tuple(report[key] for key in ("id", "title", "source_name", "source_url", "report_date", "content", "sha256", "created_at")))
            self._invalidate(connection)
        return self._report_metadata(report)

    def get_report(self, report_id):
        with self.store._connection() as connection:
            report = connection.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if report is None:
            raise StoreError("Report not found.", 404)
        return dict(report)

    def delete_report(self, report_id):
        with self.store._connection(write=True) as connection:
            if connection.execute("DELETE FROM reports WHERE id=?", (report_id,)).rowcount == 0:
                raise StoreError("Report not found.", 404)
            self._invalidate(connection)

    def _project_documents(self, query):
        documents = []
        for relative_path in PROJECT_FILES:
            path = self.project_root / relative_path
            if any(part.is_symlink() for part in (path, *path.parents) if part != self.project_root.parent):
                continue
            if not path.resolve().is_relative_to(self.project_root) or not path.is_file():
                continue
            try:
                with path.open("rb") as source:
                    raw = source.read(MAX_PROJECT_FILE_BYTES + 1)
                if len(raw) > MAX_PROJECT_FILE_BYTES:
                    continue
                content = raw.decode("utf-8")
            except (OSError, UnicodeError):
                continue
            windows, score = _windows(content, query, max_windows=2)
            documents.append({"path": relative_path, "title": relative_path, "content": content, "sha256": hashlib.sha256(raw).hexdigest(), "windows": windows, "score": score})
        return sorted(documents, key=lambda item: -item["score"])

    @staticmethod
    def _add_excerpts(packet, content, windows, metadata, kind, prefix, budget):
        lines = content.splitlines() or [""]
        total_lines = len(lines)
        covered = 0
        index = sum(item["kind"] == kind for item in packet["excerpts"])
        for start, end, anchor, terms in windows:
            if budget <= 0:
                break
            start, actual_end, excerpt, clipped, partial = _fit_window(lines, start, end, anchor, terms, budget)
            if not excerpt:
                break
            used_lines = len(excerpt.splitlines()) or 1
            covered += used_lines
            truncated = clipped or partial or start != 1 or actual_end != total_lines or len(windows) != 1
            index += 1
            citation = "[{}{}]".format(prefix, index)
            source = dict(metadata, citation=citation, kind=kind, line_start=start, line_end=actual_end, truncated=truncated, partial_line=partial)
            packet["sources"].append(source)
            packet["excerpts"].append({"citation": citation, "kind": kind, "title": metadata["title"], "content": excerpt, "line_start": start, "line_end": actual_end, "truncated": truncated, "partial_line": partial})
            budget -= len(excerpt.encode("utf-8"))
        return budget, covered < total_lines or any(item["truncated"] for item in packet["excerpts"] if item["kind"] == kind)

    def context_for(self, task):
        payload = task.get("payload", {})
        with self.store._connection() as connection:
            connection.execute("BEGIN")
            epoch = self.store._setting(connection, "knowledge_epoch")
            if str(payload.get("knowledge_epoch", "0")) != epoch:
                raise StoreError("The reference library changed. Send a new message to use its current contents.", 409)
            if "claim_token" in task:
                row = connection.execute("SELECT status,claim_token FROM tasks WHERE id=?", (task["id"],)).fetchone()
                if row is None or row["status"] != "running" or row["claim_token"] != task["claim_token"]:
                    raise StoreError("This AI request is no longer active.", 409)
            memories = [dict(row) for row in connection.execute("SELECT * FROM memories ORDER BY updated_at DESC,id")]
            report = None
            if payload.get("report_id"):
                row = connection.execute("SELECT * FROM reports WHERE id=?", (payload["report_id"],)).fetchone()
                if row is None:
                    raise StoreError("The selected report is no longer available.", 409)
                report = dict(row)
            connection.execute("COMMIT")
        query = payload.get("content", "")
        terms = _terms(query)
        # Stable sorting preserves newest-first order when relevance is tied.
        memories = sorted(memories, key=lambda memory: -(2 * len(_terms(memory["title"]) & terms) + len(_terms(memory["content"]) & terms)))
        packet = {"memories": [], "excerpts": [], "sources": [], "truncated": {"memories": len(memories) > MAX_CONTEXT_MEMORIES, "report": False, "project": False}, "knowledge_epoch": epoch, "counts": {"memories_available": len(memories), "memories_included": 0, "project_documents_available": 0, "project_documents_included": 0}}
        remaining = MEMORY_TEXT_BYTES
        for memory in memories[:MAX_CONTEXT_MEMORIES]:
            title_bytes = len(memory["title"].encode("utf-8")) + 1
            if remaining <= title_bytes:
                packet["truncated"]["memories"] = True
                break
            content, clipped = _clip(memory["content"], remaining - title_bytes)
            if not content:
                packet["truncated"]["memories"] = True
                break
            citation = "[M{}]".format(len(packet["memories"]) + 1)
            packet["memories"].append({"id": memory["id"], "title": memory["title"], "content": content, "citation": citation, "updated_at": memory["updated_at"], "truncated": clipped})
            packet["sources"].append({"citation": citation, "kind": "memory", "id": memory["id"], "title": memory["title"], "updated_at": memory["updated_at"], "sha256": _digest(memory["content"]), "line_start": 1, "line_end": len(content.splitlines()) or 1, "truncated": clipped})
            remaining -= title_bytes + len(content.encode("utf-8"))
            packet["truncated"]["memories"] |= clipped
        packet["counts"]["memories_included"] = len(packet["memories"])
        if report:
            windows, _ = _windows(report["content"], query)
            _, truncated = self._add_excerpts(packet, report["content"], windows, self._report_metadata(report), "report", "R", REPORT_TEXT_BYTES)
            packet["truncated"]["report"] = truncated
        if payload.get("project_context", False):
            remaining = PROJECT_TEXT_BYTES
            documents = self._project_documents(query)
            packet["project_status"] = "available" if documents else "unavailable"
            packet["counts"]["project_documents_available"] = len(documents)
            packet["truncated"]["project"] = len(documents) > MAX_CONTEXT_PROJECT_DOCUMENTS
            for document in documents[:MAX_CONTEXT_PROJECT_DOCUMENTS]:
                if remaining <= 0:
                    packet["truncated"]["project"] = True
                    break
                metadata = {key: document[key] for key in ("title", "path", "sha256")}
                remaining, truncated = self._add_excerpts(packet, document["content"], document["windows"], metadata, "project", "P", remaining)
                packet["counts"]["project_documents_included"] += 1
                packet["truncated"]["project"] |= truncated
        else:
            packet["project_status"] = "not_requested"
        return packet
