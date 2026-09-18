"""Run with python3 -m app.server. This is a loopback-only local preview.

No production authentication is provided. The per-process session token plus
Host/Origin checks mitigate browser cross-site writes; they do not restrict
other software already running as the local user. Do not expose via a tunnel.
"""

import argparse
import hmac
import json
import mimetypes
import os
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from . import __version__
from .mock_provider import make_draft, make_reply
from .openai_provider import LiveAI, ProviderError
from .store import Store, StoreError


MAX_BODY = 16 * 1024
STATIC_DIRECTORY = Path(__file__).parent / "static"
STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/styles.css": "styles.css",
    "/style.css": "style.css",
    "/favicon.svg": "favicon.svg",
}


class Worker(threading.Thread):
    def __init__(self, store, delay=0.7, ai=None):
        super().__init__(name="local-preview-worker", daemon=True)
        self.store = store
        self.ai = ai if ai is not None else LiveAI(store)
        self.delay = max(0, delay)
        self._stopping = threading.Event()

    def stop(self):
        self._stopping.set()

    def run(self):
        while not self._stopping.is_set():
            task = self.store.claim_next_task()
            if task is None:
                self._stopping.wait(0.1)
                continue
            if self._stopping.wait(self.delay):
                break  # Recovery retries local work only; live work is failed.
            try:
                if not self.store.is_task_active(task):
                    continue
                payload = task["payload"]
                if payload.get("provider", "preview") == "openai":
                    result = self.ai.generate(task, self.store.get_reply_context(task))
                elif task["kind"] == "mock_reply":
                    result = make_reply(payload["content"], payload["persona"])
                else:
                    result = make_draft(task["title"], payload["persona"])
                self.store.complete_task(task, result)
            except ProviderError as error:
                self.store.fail_task(task, message=str(error))
            except Exception:
                self.store.fail_task(task)


def start_worker(store, delay=0.7, ai=None):
    store.recover_pending()
    worker = Worker(store, delay, ai)
    worker.start()
    return worker


class PreviewServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, store, port, ai=None):
        self.store = store
        self.connection_lock = threading.RLock()
        self.session_token = secrets.token_urlsafe(32)
        # Keep one server/worker owner per data directory. OS-held locks release
        # on a crash, so recovery never steals claims from a live app instance.
        self._instance_lock = open(store.data_dir / ".preview.lock", "a+b")
        try:
            os.chmod(store.data_dir / ".preview.lock", 0o600)
            if os.name == "posix":
                import fcntl
                fcntl.flock(self._instance_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            elif os.name == "nt":
                import msvcrt
                self._instance_lock.seek(0, os.SEEK_END)
                if self._instance_lock.tell() == 0:
                    self._instance_lock.write(b"0")
                    self._instance_lock.flush()
                self._instance_lock.seek(0)
                msvcrt.locking(self._instance_lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                raise RuntimeError("This platform does not support the preview’s exclusive data lock.")
        except OSError as error:
            self._instance_lock.close()
            raise RuntimeError("The data directory is already in use or cannot be locked. Close the other preview, or choose a different --data-dir.") from error
        except Exception:
            self._instance_lock.close()
            raise
        try:
            self.ai = ai if ai is not None else LiveAI(store)
            super().__init__(("127.0.0.1", port), Handler)
        except Exception:
            self._instance_lock.close()
            raise

    def server_close(self):
        try:
            super().server_close()
        finally:
            self._instance_lock.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalPreview/" + __version__
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format_string, *args):
        # Avoid logging messages, persona text, tokens, or request paths.
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "microphone=(), camera=(), geolocation=()")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        super().end_headers()

    def _json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status, message):
        self._json(status, {"error": message})

    def _check_host_and_origin(self):
        if not self.path.startswith("/") or self.path.startswith("//"):
            raise StoreError("Use a local request path.")
        port = self.server.server_address[1]
        hosts = {"127.0.0.1:{}".format(port), "localhost:{}".format(port)}
        if port == 80:
            hosts.update({"127.0.0.1", "localhost"})
        host_values = self.headers.get_all("Host", [])
        if len(host_values) != 1 or host_values[0] not in hosts:
            raise StoreError("Only the local preview address is allowed.", 403)
        origins = self.headers.get_all("Origin", [])
        if origins and (len(origins) != 1 or origins[0] != "http://" + host_values[0]):
            raise StoreError("Cross-origin requests are not allowed.", 403)
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise StoreError("Cross-site requests are not allowed.", 403)

    def _read_payload(self):
        tokens = self.headers.get_all("X-Session-Token", [])
        if len(tokens) != 1 or not hmac.compare_digest(tokens[0].encode("utf-8"), self.server.session_token.encode("ascii")):
            raise StoreError("Refresh the page to obtain a valid local session token.", 403)
        if self.headers.get_content_type() != "application/json":
            raise StoreError("Use application/json for local API requests.", 415)
        if self.headers.get("Transfer-Encoding"):
            raise StoreError("Chunked requests are not supported.", 400)
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            raise StoreError("Provide a valid Content-Length.", 411)
        if len(lengths[0]) > 8:
            raise StoreError("Request is too large (maximum 16 KiB).", 413)
        length = int(lengths[0])
        if length > MAX_BODY:
            raise StoreError("Request is too large (maximum 16 KiB).", 413)
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                raise StoreError("Request body is incomplete.")
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise StoreError("Provide a valid JSON object.")
        if not isinstance(payload, dict):
            raise StoreError("Provide a JSON object.")
        return payload

    @staticmethod
    def _fields(payload, expected):
        if set(payload) != set(expected):
            raise StoreError("Expected exactly these fields: {}.".format(", ".join(expected)))

    def do_GET(self):
        try:
            self._check_host_and_origin()
            path = urlsplit(self.path).path
            if path == "/api/state":
                state = self.server.store.get_state()
                connection = self.server.ai.public_state()
                state["connection"] = connection
                state["mode"] = "live" if connection["connected"] else "preview"
                state["capabilities"]["ai"] = connection["connected"]
                state["session_token"] = self.server.session_token
                self._json(200, state)
            elif path == "/health":
                healthy = self.server.store.health()
                connection = self.server.ai.public_state()
                self._json(200 if healthy else 503, {"status": "ok" if healthy else "error", "version": __version__, "database": "ok" if healthy else "error", "mode": "live" if connection["connected"] else "preview", "ai_connected": connection["connected"], "ai_verified": connection["verified"]})
            elif path in STATIC_FILES:
                file_path = STATIC_DIRECTORY / STATIC_FILES[path]
                if not file_path.is_file() or file_path.is_symlink():
                    self._error(404, "File not found.")
                    return
                content = file_path.read_bytes()
                content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", content_type + ("; charset=utf-8" if content_type.startswith("text/") or content_type == "application/javascript" else ""))
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            else:
                self._error(404, "Not found.")
        except StoreError as error:
            self._error(error.status, str(error))
        except (sqlite3.Error, OSError):
            self._error(503, "The local preview could not read its data.")

    def do_POST(self):
        try:
            self._check_host_and_origin()
            payload = self._read_payload()
            path = urlsplit(self.path).path
            if path == "/api/persona":
                self._json(200, {"persona": self.server.store.update_persona(payload)})
            elif path == "/api/messages":
                self._fields(payload, ("content", "request_id", "conversation_epoch", "provider"))
                if type(payload["conversation_epoch"]) is not int:
                    raise StoreError("conversation_epoch must be an integer.")
                with self.server.connection_lock:
                    connection = self.server.ai.public_state()
                    provider = "openai" if connection["connected"] else "preview"
                    if payload["provider"] != provider:
                        raise StoreError("The AI connection changed. Review the current mode before sending your message again.", 409)
                    task_id = self.server.store.enqueue_message(payload["content"], payload["request_id"], payload["conversation_epoch"], provider=provider, live_can_send=connection["can_send"])
                self._json(202, {"task_id": task_id})
            elif path == "/api/connection":
                self._fields(payload, ("api_key",))
                with self.server.connection_lock:
                    connection = self.server.ai.connect(payload["api_key"])
                self._json(200, {"connection": connection})
            elif path == "/api/connection/disconnect":
                self._fields(payload, ())
                with self.server.connection_lock:
                    connection = self.server.ai.disconnect()
                self._json(200, {"connection": connection})
            elif path == "/api/tasks":
                self._fields(payload, ("title", "kind"))
                self._json(202, {"task_id": self.server.store.enqueue_task(payload["title"], payload["kind"])})
            elif path.startswith("/api/tasks/") and path.endswith("/cancel") and len(path.split("/")) == 5:
                self._fields(payload, ())
                task_id = path.split("/")[3]
                self._json(200, {"task": self.server.store.cancel_task(task_id)})
            elif path == "/api/conversation/reset":
                self._fields(payload, ())
                self.server.store.reset_conversation()
                self._json(200, {"ok": True})
            else:
                self._error(404, "Not found.")
        except StoreError as error:
            self._error(error.status, str(error))
        except ProviderError as error:
            self._error(400, str(error))
        except (sqlite3.Error, OSError):
            self._error(503, "The local preview could not save its data.")


def create_server(store, port=8765, ai=None):
    """Return a server bound only to 127.0.0.1; port=0 chooses a test port."""
    return PreviewServer(store, port, ai)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Start Presence locally, with optional budget-limited AI text.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "runtime-data")
    parser.add_argument("--no-worker", action="store_true", help="Keep tasks queued; useful for tests.")
    parser.add_argument("--worker-delay", type=float, default=0.7, help="Local preview delay in seconds.")
    parser.add_argument("--test-budget-usd", default=None, help="Explicitly authorized total API test allowance in USD; persisted locally.")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("Port must be between 0 and 65535.")
    if not 0 <= args.worker_delay <= 60:
        parser.error("Worker delay must be between 0 and 60 seconds.")
    store = Store(args.data_dir)
    server = None
    try:
        # Lock and bind before applying an allowance: a failed second instance
        # must not change the already-running app's spending limit.
        server = create_server(store, args.port)
        ai = server.ai if args.test_budget_usd is None else LiveAI(store, budget_usd=args.test_budget_usd)
        server.ai = ai
    except (ProviderError, RuntimeError) as error:
        if server:
            server.server_close()
        parser.exit(1, str(error) + "\n")
    except OSError:
        if server:
            server.server_close()
        parser.exit(1, "The local preview could not open its port. Close the existing preview or choose another --port.\n")
    worker = None if args.no_worker else start_worker(store, args.worker_delay, ai)
    print("Local preview ready: http://127.0.0.1:{}".format(server.server_address[1]), flush=True)
    print("Starts in scripted preview. Connect an API key in the app for budget-limited AI text. Voice, avatar, EA, and external tools remain disconnected.", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        if worker:
            worker.stop()
            worker.join(timeout=2)
        server.server_close()


if __name__ == "__main__":
    main()
