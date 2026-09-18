"""HTTP integration tests for the local, synthetic-data-only prototype.

Run from the repository root with ``python3 -m unittest discover -s tests -v``.
Every test launches the real server with its own temporary private state store;
no account, remote service, API key, or third-party package is used.
"""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
OMIT = object()


class LocalAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="remote-agent-test-")
        self.data_dir = Path(self.temp.name) / "state"
        self.process = None
        self.log = tempfile.TemporaryFile(mode="w+b")
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.log.close)
        self.addCleanup(self.stop_server)
        self.start_server(no_worker=True)

    def start_server(self, *, no_worker=False, worker_delay=0.2):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            self.port = listener.getsockname()[1]
        command = [
            sys.executable, "-B", "-m", "app.server", "--port", str(self.port),
            "--data-dir", str(self.data_dir), "--worker-delay", str(worker_delay),
        ]
        if no_worker:
            command.append("--no-worker")
        self.process = subprocess.Popen(
            command, cwd=ROOT, stdout=self.log, stderr=subprocess.STDOUT,
        )
        self.token = None
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.log.seek(0)
                self.fail("Server exited during startup:\n" + self.log.read().decode())
            try:
                status, state, _ = self.request("GET", "/api/state")
                if status == 200:
                    self.token = state["session_token"]
                    return
            except (OSError, http.client.HTTPException):
                pass
            time.sleep(0.02)
        self.fail("Local server did not become ready")

    def stop_server(self, *, crash=False):
        if self.process is not None:
            if crash:
                self.process.kill()
            else:
                self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
            self.process = None

    def restart_server(self, *, no_worker=False, worker_delay=0.2, crash=False):
        self.stop_server(crash=crash)
        self.start_server(no_worker=no_worker, worker_delay=worker_delay)

    def request(self, method, path, payload=OMIT, *, token=OMIT,
                origin=OMIT, host=None, content_type="application/json", raw=None):
        if method == "POST" and path == "/api/messages" and isinstance(payload, dict):
            state = self.state()
            payload = {
                "conversation_epoch": state["conversation_epoch"],
                "provider": "openai" if state["connection"]["connected"] else "preview",
                **payload,
            }
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        if method != "GET":
            value = self.token if token is OMIT else token
            if value is not None:
                headers["X-Session-Token"] = value
            headers["Content-Type"] = content_type
            if origin is OMIT:
                origin = f"http://127.0.0.1:{self.port}"
        if origin is not OMIT and origin is not None:
            headers["Origin"] = origin
        body = raw
        if payload is not OMIT:
            body = json.dumps(payload).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            data = response.read()
            response_headers = dict(response.getheaders())
            if "application/json" in response_headers.get("Content-Type", ""):
                data = json.loads(data)
            return response.status, data, response_headers
        finally:
            connection.close()

    def state(self):
        status, state, _ = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        return state

    def post_ok(self, path, payload):
        status, response, _ = self.request("POST", path, payload)
        self.assertIn(status, (200, 201, 202), response)
        return response

    def send_message(self, content="Synthetic test message", request_id=None):
        return self.post_ok("/api/messages", {
            "content": content, "request_id": request_id or str(uuid.uuid4()),
        })

    def wait_for(self, predicate, *, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self.state()
            if predicate(state):
                return state
            time.sleep(0.02)
        self.fail("Condition not reached; latest state: " + repr(state))

    @staticmethod
    def task(state, task_id):
        return next(item for item in state["tasks"] if item["id"] == task_id)

    @staticmethod
    def replies(state):
        return [item for item in state["messages"] if item["role"] == "assistant"]

    def assert_rejected(self, path, payload=OMIT, **kwargs):
        status, _, _ = self.request("POST", path, payload, **kwargs)
        self.assertGreaterEqual(status, 400)
        self.assertLess(status, 500)

    def test_initial_state_is_explicitly_a_preview(self):
        state = self.state()
        self.assertEqual(state["mode"], "preview")
        self.assertTrue(state["session_token"])
        self.assertIs(type(state["conversation_epoch"]), int)
        self.assertIsInstance(state["persona"], dict)
        self.assertIsInstance(state["capabilities"], dict)
        self.assertTrue(all(value is False for value in state["capabilities"].values()))
        self.assertEqual(state["messages"], [])
        self.assertEqual(state["tasks"], [])

    def test_persona_persists_and_invalid_updates_do_not_replace_it(self):
        persona = dict(self.state()["persona"])
        persona.update({
            "name": "Aster", "role": "Synthetic local assistant",
            "instructions": "Keep synthetic examples brief and explicit.",
        })
        response = self.post_ok("/api/persona", persona)
        self.assertEqual(response["persona"], persona)
        self.restart_server(no_worker=True)
        self.assertEqual(self.state()["persona"], persona)
        for field, value in (
            ("name", ""), ("name", "x" * 41), ("role", "x" * 121),
            ("instructions", "x" * 2001), ("tone", "unsupported-tone"),
            ("response_length", "unsupported-length"), ("name", ["Aster"]),
        ):
            with self.subTest(field=field, value=repr(value)[:60]):
                invalid = dict(persona)
                invalid[field] = value
                self.assert_rejected("/api/persona", invalid)
                self.assertEqual(self.state()["persona"], persona)
        self.assert_rejected("/api/persona", {**persona, "permissions": "all"})
        self.assertEqual(self.state()["persona"], persona)

    def test_retry_is_idempotent_even_with_concurrent_requests(self):
        request_id = str(uuid.uuid4())
        payload = {"content": "Synthetic duplicate request", "request_id": request_id}
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(
                lambda _: self.request("POST", "/api/messages", payload), range(4),
            ))
        for status, response, _ in responses:
            self.assertIn(status, (200, 201, 202), response)
        task_ids = {response["task_id"] for _, response, _ in responses}
        self.assertEqual(len(task_ids), 1)
        self.assertEqual(len(self.state()["messages"]), 1)
        self.assertEqual(len(self.state()["tasks"]), 1)
        changed = {"content": "Changed content must not reuse an ID", "request_id": request_id}
        status, _, _ = self.request("POST", "/api/messages", changed)
        self.assertEqual(status, 409)
        self.restart_server()
        state = self.wait_for(lambda value: len(self.replies(value)) == 1)
        self.assertEqual(len(state["messages"]), 2)
        status, retry, _ = self.request("POST", "/api/messages", payload)
        self.assertIn(status, (200, 201, 202))
        self.assertIn(retry["task_id"], task_ids)
        self.assertEqual(len(self.state()["messages"]), 2)

    def test_queued_message_and_draft_survive_restart_and_complete(self):
        message = self.send_message("A synthetic message retained across restart")
        draft = self.post_ok("/api/tasks", {"title": "Synthetic draft", "kind": "draft"})
        before = self.state()
        self.assertEqual(self.task(before, message["task_id"])["status"], "queued")
        self.assertEqual(self.task(before, draft["task_id"])["status"], "queued")
        self.restart_server(crash=True)
        state = self.wait_for(lambda value: all(
            item["status"] == "completed" for item in value["tasks"]
        ))
        self.assertEqual({item["id"] for item in before["tasks"]},
                         {item["id"] for item in state["tasks"]})
        self.assertEqual(len(self.replies(state)), 1)
        self.assertTrue(self.task(state, draft["task_id"])["result"])
        self.restart_server()
        self.assertEqual(self.state()["messages"], state["messages"])
        self.assertEqual(self.state()["tasks"], state["tasks"])

    def test_crashed_running_message_recovers_without_duplicate_reply(self):
        self.restart_server(worker_delay=1)
        response = self.send_message("Synthetic recovery test")
        task_id = response["task_id"]
        self.wait_for(lambda value: self.task(value, task_id)["status"] == "running")
        self.restart_server(crash=True)
        state = self.wait_for(lambda value: self.task(value, task_id)["status"] == "completed")
        self.assertEqual(len(self.replies(state)), 1)
        self.restart_server()
        self.assertEqual(len(self.replies(self.state())), 1)

    def test_second_process_cannot_take_over_the_same_state_directory(self):
        self.send_message("Synthetic single-owner test")
        before = self.state()
        second = subprocess.Popen([
            sys.executable, "-B", "-m", "app.server", "--port", "0",
            "--data-dir", str(self.data_dir), "--no-worker",
        ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        try:
            output, _ = second.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            second.kill()
            second.communicate(timeout=3)
            self.fail("A second process incorrectly started with the same state directory")
        self.assertNotEqual(second.returncode, 0, output.decode())
        self.assertIn("already in use", output.decode())
        self.assertEqual(self.state(), before)

    def test_cancel_running_reply_prevents_late_publication(self):
        self.restart_server(worker_delay=0.4)
        response = self.send_message("Synthetic cancellation test")
        task_id = response["task_id"]
        self.wait_for(lambda value: self.task(value, task_id)["status"] == "running")
        self.post_ok(f"/api/tasks/{task_id}/cancel", {})
        time.sleep(0.6)
        state = self.state()
        self.assertEqual(self.task(state, task_id)["status"], "cancelled")
        self.assertEqual(self.replies(state), [])
        self.post_ok(f"/api/tasks/{task_id}/cancel", {})
        self.restart_server()
        self.assertEqual(self.replies(self.state()), [])
        self.assertEqual(self.task(self.state(), task_id)["status"], "cancelled")

    def test_reset_cancels_running_and_queued_replies_without_late_resurrection(self):
        self.restart_server(worker_delay=0.4)
        request_id = str(uuid.uuid4())
        first = self.send_message("Synthetic reset test", request_id=request_id)
        first_id = first["task_id"]
        self.wait_for(lambda value: self.task(value, first_id)["status"] == "running")
        second = self.send_message("Another queued synthetic reset test")
        self.post_ok("/api/conversation/reset", {})
        self.assertEqual(self.state()["messages"], [])
        time.sleep(0.6)
        state = self.state()
        self.assertEqual(state["messages"], [])
        for task_id in (first_id, second["task_id"]):
            self.assertEqual(self.task(state, task_id)["status"], "cancelled")
        retry = self.send_message("Synthetic reset test", request_id=request_id)
        self.assertEqual(retry["task_id"], first_id)
        self.assertEqual(self.state()["messages"], [])
        self.restart_server()
        self.assertEqual(self.state()["messages"], [])
        fresh = self.send_message("A new conversation after reset")
        state = self.wait_for(lambda value: self.task(value, fresh["task_id"])["status"] == "completed")
        self.assertEqual(len(state["messages"]), 2)
        self.assertEqual(len(self.replies(state)), 1)

    def test_reset_removes_completed_reply_text_from_public_state(self):
        self.restart_server()
        marker = "Synthetic text to clear 57c0bdb4"
        response = self.send_message(marker)
        self.wait_for(lambda value: self.task(value, response["task_id"])["status"] == "completed")
        self.post_ok("/api/conversation/reset", {})
        state = self.state()
        self.assertEqual(state["messages"], [])
        self.assertNotIn(marker, json.dumps(state))
        self.restart_server()
        self.assertNotIn(marker, json.dumps(self.state()))

    def test_late_http_send_from_before_reset_cannot_resurrect_a_conversation(self):
        old_epoch = self.state()["conversation_epoch"]
        existing_request_id = str(uuid.uuid4())
        accepted = self.send_message("Synthetic accepted message", request_id=existing_request_id)
        delayed_payload = {
            "content": "Synthetic delayed request from before reset",
            "request_id": str(uuid.uuid4()),
            "conversation_epoch": old_epoch,
        }
        self.post_ok("/api/conversation/reset", {})
        cleared = self.state()
        self.assertGreater(cleared["conversation_epoch"], old_epoch)
        status, _, _ = self.request("POST", "/api/messages", delayed_payload)
        self.assertEqual(status, 409)
        self.assertEqual(self.state(), cleared)

        # A retry of an already accepted request can return its existing receipt
        # even with the old epoch, without creating a new message or task.
        retry = self.post_ok("/api/messages", {
            "content": "Synthetic accepted message",
            "request_id": existing_request_id,
            "conversation_epoch": old_epoch,
        })
        self.assertEqual(retry["task_id"], accepted["task_id"])
        self.assertEqual(self.state(), cleared)
        self.send_message("Synthetic message from the current conversation")
        current = self.state()
        self.assertEqual(len(current["messages"]), 1)
        self.assertEqual(len(current["tasks"]), len(cleared["tasks"]) + 1)

    def test_missing_or_wrong_session_token_cannot_mutate_state(self):
        payload = {"content": "Must not be accepted", "request_id": str(uuid.uuid4())}
        self.assert_rejected("/api/messages", payload, token=None)
        self.assert_rejected("/api/messages", payload, token="invalid-token")
        self.assert_rejected("/api/messages", payload, token="invalid-\u00e9-token")
        self.assertEqual(self.state()["messages"], [])
        self.assertEqual(self.state()["tasks"], [])

    def test_remote_origins_and_rebound_hosts_cannot_access_or_mutate_state(self):
        payload = {"content": "Must not be accepted", "request_id": str(uuid.uuid4())}
        for origin in ("https://attacker.invalid", "null", "http://127.0.0.1:1"):
            with self.subTest(origin=origin):
                self.assert_rejected("/api/messages", payload, origin=origin)
                status, _, _ = self.request("GET", "/api/state", origin=origin)
                self.assertGreaterEqual(status, 400)
                self.assertLess(status, 500)
        for host in ("attacker.invalid", f"127.0.0.1.attacker.invalid:{self.port}",
                     f"localhost.attacker.invalid:{self.port}"):
            with self.subTest(host=host):
                status, _, _ = self.request("GET", "/api/state", host=host)
                self.assertGreaterEqual(status, 400)
                self.assertLess(status, 500)
                self.assert_rejected("/api/messages", payload, host=host)
        self.assertEqual(self.state()["messages"], [])

    def test_old_session_token_is_invalid_after_restart(self):
        old_token = self.token
        self.restart_server(no_worker=True)
        self.assertNotEqual(old_token, self.token)
        self.assert_rejected("/api/messages", {
            "content": "Old token", "request_id": str(uuid.uuid4()),
        }, token=old_token)

    def test_json_and_input_validation_rejects_without_partial_writes(self):
        for raw in (b"{broken", b"[]", b"null", b"12"):
            with self.subTest(raw=raw):
                self.assert_rejected("/api/messages", raw=raw)
        self.assert_rejected("/api/messages", raw=b"{}", content_type="text/plain")
        self.assert_rejected("/api/messages", raw=json.dumps({
            "content": "Missing conversation epoch", "request_id": str(uuid.uuid4()),
        }).encode("utf-8"))
        status, _, _ = self.request("POST", "/api/messages", raw=b" " * 17000)
        self.assertEqual(status, 413)
        for payload in (
            {"content": "", "request_id": str(uuid.uuid4())},
            {"content": "   ", "request_id": str(uuid.uuid4())},
            {"content": "x" * 4001, "request_id": str(uuid.uuid4())},
            {"content": 123, "request_id": str(uuid.uuid4())},
            {"content": "Hello", "request_id": ""},
            {"content": "Hello", "request_id": str(uuid.uuid4()), "execute": "anything"},
            {"content": "Hello", "request_id": str(uuid.uuid4()), "conversation_epoch": None},
            {"content": "Hello", "request_id": str(uuid.uuid4()), "conversation_epoch": True},
            {"content": "Hello", "request_id": str(uuid.uuid4()), "conversation_epoch": "0"},
        ):
            with self.subTest(payload=repr(payload)[:100]):
                self.assert_rejected("/api/messages", payload)
        for payload in (
            {"title": "", "kind": "draft"},
            {"title": "x" * 201, "kind": "draft"},
            {"title": "Unapproved operation", "kind": "shell"},
            {"title": "Unapproved operation", "kind": "draft", "command": "anything"},
        ):
            with self.subTest(payload=repr(payload)[:100]):
                self.assert_rejected("/api/tasks", payload)
        self.assertEqual(self.state()["messages"], [])
        self.assertEqual(self.state()["tasks"], [])

    def test_private_files_and_path_traversal_are_not_served(self):
        for path in ("/AGENTS.md", "/app/server.py", "/state.sqlite3",
                     "/data/state.sqlite3", "/../README.md", "/%2e%2e/README.md",
                     "/static/../app/server.py", "/static/%2e%2e/app/server.py"):
            with self.subTest(path=path):
                status, _, _ = self.request("GET", path)
                self.assertEqual(status, 404)


class StoreRecoveryTests(unittest.TestCase):
    def test_stale_worker_claim_cannot_publish_after_recovery(self):
        # The public store hooks let us model a late result from the old worker
        # precisely, without timing a second live process against its successor.
        from app.store import Store

        with tempfile.TemporaryDirectory(prefix="remote-agent-claim-test-") as directory:
            store = Store(directory)
            task_id = store.enqueue_message("Synthetic stale-worker test", str(uuid.uuid4()))
            stale_claim = store.claim_next_task()
            restarted_store = Store(directory)
            self.assertEqual(restarted_store.recover_pending(), 1)
            current_claim = restarted_store.claim_next_task()
            self.assertEqual(stale_claim["id"], current_claim["id"])
            self.assertFalse(store.complete_task(stale_claim, "Stale reply must never appear"))
            self.assertEqual(len(restarted_store.get_state()["messages"]), 1)
            self.assertTrue(restarted_store.complete_task(current_claim, "Current synthetic reply"))
            self.assertFalse(restarted_store.complete_task(current_claim, "Duplicate synthetic reply"))
            state = restarted_store.get_state()
            self.assertEqual(len(state["messages"]), 2)
            self.assertEqual(state["messages"][-1]["content"], "Current synthetic reply")
            self.assertEqual(LocalAppTests.task(state, task_id)["status"], "completed")


if __name__ == "__main__":
    unittest.main()
