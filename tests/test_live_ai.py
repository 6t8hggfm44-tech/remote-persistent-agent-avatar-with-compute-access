"""Offline tests for the bounded live-AI adapter and local HTTP integration.

Every LiveAI instance uses an injected transport with synthetic credentials.
No test calls OpenAI or any other paid or external service.
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import uuid

from app.openai_provider import LiveAI, ProviderError
from app.store import DEFAULT_PERSONA, Store


SYNTHETIC_KEY = "sk-test-" + "x" * 48
OMIT = object()


def completed_response(text="Synthetic live response"):
    return {
        "status": "completed",
        "output": [{
            "type": "message", "role": "assistant",
            "content": [{"type": "output_text", "text": text}],
        }],
        "usage": {
            "input_tokens": 100, "output_tokens": 20,
            "input_tokens_details": {"cached_tokens": 0},
        },
    }


def task_fixture(content="Synthetic current message", persona=None):
    return {
        "id": str(uuid.uuid4()), "kind": "mock_reply", "provider": "openai",
        "payload": {
            "content": content, "persona": persona or dict(DEFAULT_PERSONA), "epoch": "0",
        },
    }


def history_fixture(content="Synthetic current message"):
    return [{"role": "user", "content": content, "provider": "openai"}]


class LiveProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="presence-ai-test-")
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.calls = []
        self.calls_lock = threading.Lock()

    def transport(self, body, key):
        with self.calls_lock:
            self.calls.append((body, key))
        return completed_response()

    def manager(self, budget="1", transport=None):
        return LiveAI(self.store, budget_usd=budget, transport=transport or self.transport)

    def assert_key_not_saved(self, ai):
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(ai.public_state()))
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(self.store.get_state()))
        for path in Path(self.temp.name).rglob("*"):
            if path.is_file():
                self.assertNotIn(SYNTHETIC_KEY.encode(), path.read_bytes(), path.name)

    def test_connection_is_local_only_and_never_persists_the_key(self):
        ai = self.manager()
        self.assertFalse(ai.public_state()["connected"])
        self.assertFalse(ai.public_state()["can_send"])
        ai.connect(SYNTHETIC_KEY)
        state = ai.public_state()
        self.assertTrue(state["connected"])
        self.assertFalse(state["verified"])
        self.assertTrue(state["can_send"])
        self.assertEqual(self.calls, [])
        self.assert_key_not_saved(ai)
        reopened = self.manager()
        self.assertFalse(reopened.public_state()["connected"])
        self.assertFalse(reopened.public_state()["can_send"])
        ai.disconnect()
        self.assertFalse(ai.public_state()["connected"])
        self.assert_key_not_saved(ai)

    def test_invalid_credentials_are_rejected_without_transport_or_echo(self):
        ai = self.manager()
        for key in (None, "", "plain-text-not-a-key", "sk-short", 7):
            with self.subTest(key=type(key).__name__):
                with self.assertRaises(ProviderError) as error:
                    ai.connect(key)
                self.assertNotIn("plain-text-not-a-key", str(error.exception))
                self.assertFalse(ai.public_state()["connected"])
        self.assertEqual(self.calls, [])

    def test_calls_require_both_an_ephemeral_key_and_explicit_budget(self):
        no_budget = self.manager(budget=None)
        no_budget.connect(SYNTHETIC_KEY)
        with self.assertRaises(ProviderError):
            no_budget.generate(task_fixture(), history_fixture())
        self.assertFalse(no_budget.public_state()["can_send"])
        with tempfile.TemporaryDirectory(prefix="presence-ai-no-key-") as directory:
            no_key = LiveAI(Store(directory), budget_usd="1", transport=self.transport)
            with self.assertRaises(ProviderError):
                no_key.generate(task_fixture(), history_fixture())
        self.assertEqual(self.calls, [])

    def test_concurrent_reservations_enforce_the_exact_persistent_budget(self):
        ai = self.manager()
        ai.connect(SYNTHETIC_KEY)

        def attempt(_):
            try:
                ai.generate(task_fixture(), history_fixture())
                return True
            except ProviderError:
                return False

        with ThreadPoolExecutor(max_workers=12) as executor:
            results = list(executor.map(attempt, range(60)))
        self.assertEqual(sum(results), 50)
        self.assertEqual(len(self.calls), 50)
        state = ai.public_state()
        self.assertEqual(Decimal(str(state["budget_limit_usd"])), Decimal("1"))
        self.assertEqual(Decimal(str(state["reserved_usd"])), Decimal("1"))
        self.assertEqual(Decimal(str(state["remaining_usd"])), Decimal("0"))
        self.assertFalse(state["can_send"])
        self.assertGreater(state["estimated_cost_usd"], 0)
        self.assertLess(state["estimated_cost_usd"], state["reserved_usd"])

        reopened = self.manager()
        reopened.connect(SYNTHETIC_KEY)
        with self.assertRaises(ProviderError):
            reopened.generate(task_fixture(), history_fixture())
        self.assertEqual(len(self.calls), 50)
        self.assertEqual(Decimal(str(reopened.public_state()["reserved_usd"])), Decimal("1"))
        self.assert_key_not_saved(reopened)

    def test_transport_failure_is_redacted_reserved_and_not_retried(self):
        def broken_transport(body, key):
            self.calls.append((body, key))
            raise RuntimeError("Synthetic upstream error leaked " + key)

        ai = self.manager(transport=broken_transport)
        ai.connect(SYNTHETIC_KEY)
        task = task_fixture()
        with self.assertRaises(ProviderError) as error:
            ai.generate(task, history_fixture())
        self.assertNotIn(SYNTHETIC_KEY, str(error.exception))
        self.assertNotIn("Synthetic upstream error", str(error.exception))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(Decimal(str(ai.public_state()["reserved_usd"])), Decimal("0.02"))
        self.assertFalse(ai.public_state()["verified"])
        with self.assertRaises(ProviderError):
            ai.generate(task, history_fixture())
        reopened = self.manager(transport=broken_transport)
        reopened.connect(SYNTHETIC_KEY)
        with self.assertRaises(ProviderError):
            reopened.generate(task, history_fixture())
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(Decimal(str(reopened.public_state()["reserved_usd"])), Decimal("0.02"))
        self.assert_key_not_saved(ai)

    def test_persona_context_and_fixed_api_profile_are_sent_without_credentials(self):
        ai = self.manager()
        ai.connect(SYNTHETIC_KEY)
        persona = {**DEFAULT_PERSONA, "name": "Synthetic Aster", "instructions": "Synthetic persona note 492"}
        history = [
            {"role": "user", "content": "Earlier live context 893", "provider": "openai"},
            {"role": "assistant", "content": "Earlier live answer 284", "provider": "openai"},
            *history_fixture(),
        ]
        self.assertEqual(ai.generate(task_fixture(persona=persona), history), "Synthetic live response")
        self.assertEqual(len(self.calls), 1)
        body, key = self.calls[0]
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.assertEqual(key, SYNTHETIC_KEY)
        self.assertNotIn(SYNTHETIC_KEY.encode(), encoded)
        self.assertIn(b"Synthetic Aster", encoded)
        self.assertIn(b"Synthetic persona note 492", encoded)
        self.assertIn(b"Earlier live context 893", encoded)
        self.assertIn(b"Earlier live answer 284", encoded)
        self.assertIn(b"Synthetic current message", encoded)
        self.assertEqual(body["model"], "gpt-5.6-luna")
        self.assertIs(body["store"], False)
        self.assertEqual(body["reasoning"]["effort"], "none")
        self.assertLessEqual(body["max_output_tokens"], 1000)
        self.assertGreater(body["max_output_tokens"], 0)
        self.assertFalse(body.get("tools"))
        self.assertLessEqual(len(encoded), 30000)
        self.assertTrue(ai.public_state()["verified"])

    def test_oversized_utf8_context_never_dispatches_an_oversized_request(self):
        ai = self.manager()
        ai.connect(SYNTHETIC_KEY)
        history = [{"role": "user", "content": "\U0001f642" * 4000, "provider": "openai"} for _ in range(20)]
        history.extend(history_fixture())
        try:
            ai.generate(task_fixture(), history)
        except ProviderError:
            pass
        for body, _ in self.calls:
            self.assertLessEqual(len(json.dumps(body, ensure_ascii=False).encode("utf-8")), 30000)
        self.assertLessEqual(len(self.calls), 1)

    def test_malformed_incomplete_or_unbounded_output_fails_safely(self):
        fixtures = (
            {},
            {"status": "completed", "output": []},
            {"status": "completed", "output": "invalid"},
            {**completed_response(), "status": "incomplete"},
            completed_response("x" * 300000),
        )
        for response in fixtures:
            with self.subTest(shape=str(response)[:100]):
                self.calls.clear()

                def malformed_transport(body, key):
                    self.calls.append((body, key))
                    return response

                ai = self.manager(transport=malformed_transport)
                ai.connect(SYNTHETIC_KEY)
                with self.assertRaises(ProviderError) as error:
                    ai.generate(task_fixture(), history_fixture())
                self.assertNotIn(SYNTHETIC_KEY, str(error.exception))
                self.assertEqual(len(self.calls), 1)

    def test_restart_fails_live_work_instead_of_repeating_a_possibly_billed_call(self):
        for claim_before_restart in (False, True):
            with self.subTest(was_running=claim_before_restart):
                with tempfile.TemporaryDirectory(prefix="presence-ai-recovery-") as directory:
                    store = Store(directory)
                    task_id = store.enqueue_message("Synthetic interrupted live call", str(uuid.uuid4()), provider="openai")
                    if claim_before_restart:
                        self.assertEqual(store.claim_next_task()["id"], task_id)
                    recovered = Store(directory)
                    recovered.recover_pending()
                    state = recovered.get_state()
                    task = next(item for item in state["tasks"] if item["id"] == task_id)
                    self.assertEqual(task["status"], "failed")
                    self.assertTrue(task["result"])
                    self.assertIsNone(recovered.claim_next_task())
                    self.assertEqual(len(state["messages"]), 1)


class LiveHTTPTests(unittest.TestCase):
    def setUp(self):
        from app.server import create_server, start_worker

        self.temp = tempfile.TemporaryDirectory(prefix="presence-live-http-")
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        self.calls = []
        self.started = threading.Event()
        self.release = threading.Event()
        self.block_transport = False
        self.fail_transport = False
        self.ai = LiveAI(self.store, budget_usd="1", transport=self.transport)
        self.server = create_server(self.store, port=0, ai=self.ai)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.worker = start_worker(self.store, delay=0.01, ai=self.ai)
        self.addCleanup(self.shutdown)
        self.port = self.server.server_address[1]
        self.token = self.server.session_token

    def shutdown(self):
        self.release.set()
        self.worker.stop()
        self.worker.join(timeout=3)
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=3)

    def transport(self, body, key):
        self.calls.append((body, key))
        self.started.set()
        if self.fail_transport:
            raise RuntimeError("Synthetic transport failure with secret " + key)
        if self.block_transport and not self.release.wait(timeout=5):
            raise RuntimeError("Synthetic test transport timed out")
        return completed_response()

    def request(self, method, path, payload=OMIT, *, token=OMIT, origin=OMIT):
        headers = {"Host": f"127.0.0.1:{self.port}"}
        body = None
        if payload is not OMIT:
            if path == "/api/messages":
                state = self.state()
                payload = {"conversation_epoch": state["conversation_epoch"],
                           "provider": "openai" if self.ai.public_state()["connected"] else "preview",
                           **payload}
            body = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        if method == "POST":
            if token is OMIT:
                token = self.token
            if token is not None:
                headers["X-Session-Token"] = token
            if origin is OMIT:
                origin = f"http://127.0.0.1:{self.port}"
        if origin is not OMIT:
            headers["Origin"] = origin
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(method, path, body, headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def state(self):
        status, state = self.request("GET", "/api/state")
        self.assertEqual(status, 200)
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(state))
        return state

    def post(self, path, payload):
        status, response = self.request("POST", path, payload)
        self.assertIn(status, (200, 201, 202), response)
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(response))
        return response

    def send(self, content, **fields):
        return self.post("/api/messages", {"content": content, "request_id": str(uuid.uuid4()), **fields})["task_id"]

    def wait_task(self, task_id, expected="completed"):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = self.state()
            task = next(item for item in state["tasks"] if item["id"] == task_id)
            if task["status"] == expected:
                return state
            time.sleep(0.01)
        self.fail("Task did not reach {}: {}".format(expected, task))

    def connect(self):
        self.post("/api/connection", {"api_key": SYNTHETIC_KEY})
        self.assertTrue(self.ai.public_state()["connected"])

    def test_live_flow_excludes_preview_history_and_persists_provider_labels(self):
        preview = self.send("PREVIEW_ONLY_MARKER_723")
        self.wait_task(preview)
        self.connect()
        self.assertEqual(self.calls, [])
        first = self.send("LIVE_HISTORY_MARKER_419")
        self.wait_task(first)
        second = self.send("CURRENT_LIVE_MARKER_502")
        state = self.wait_task(second)
        self.assertEqual(len(self.calls), 2)
        request_body = json.dumps(self.calls[-1][0])
        self.assertNotIn("PREVIEW_ONLY_MARKER_723", request_body)
        self.assertIn("LIVE_HISTORY_MARKER_419", request_body)
        self.assertIn("CURRENT_LIVE_MARKER_502", request_body)
        self.assertIn("Synthetic live response", request_body)
        live_messages = [message for message in state["messages"] if message["provider"] == "openai"]
        self.assertEqual(len(live_messages), 4)
        self.assertEqual(sum(message["role"] == "assistant" for message in live_messages), 2)
        self.assertTrue(self.ai.public_state()["verified"])
        for path in Path(self.temp.name).rglob("*"):
            if path.is_file():
                self.assertNotIn(SYNTHETIC_KEY.encode(), path.read_bytes(), path.name)

    def test_connection_endpoints_require_session_and_same_origin(self):
        for options in ({"token": None}, {"token": "incorrect"}, {"origin": "https://attacker.invalid"}):
            with self.subTest(options=options):
                status, response = self.request("POST", "/api/connection", {"api_key": SYNTHETIC_KEY}, **options)
                self.assertEqual(status, 403)
                self.assertNotIn(SYNTHETIC_KEY, json.dumps(response))
                self.assertFalse(self.ai.public_state()["connected"])
        self.connect()
        for options in ({"token": None}, {"origin": "https://attacker.invalid"}):
            status, _ = self.request("POST", "/api/connection/disconnect", {}, **options)
            self.assertEqual(status, 403)
            self.assertTrue(self.ai.public_state()["connected"])
        self.assertEqual(self.calls, [])

    def test_cross_tab_provider_drift_rejects_before_persisting_or_calling(self):
        self.connect()
        before = self.state()
        status, _ = self.request("POST", "/api/messages", {
            "content": "Stale preview tab", "request_id": str(uuid.uuid4()), "provider": "preview",
        })
        self.assertEqual(status, 409)
        self.assertEqual(self.state()["messages"], before["messages"])
        self.assertEqual(self.state()["tasks"], before["tasks"])
        self.post("/api/connection/disconnect", {})
        status, _ = self.request("POST", "/api/messages", {
            "content": "Stale live tab", "request_id": str(uuid.uuid4()), "provider": "openai",
        })
        self.assertEqual(status, 409)
        self.assertEqual(self.state()["messages"], [])
        self.assertEqual(self.calls, [])

    def test_only_one_live_request_can_be_pending(self):
        self.block_transport = True
        self.connect()
        first = self.send("Synthetic pending live call")
        self.assertTrue(self.started.wait(timeout=3))
        status, _ = self.request("POST", "/api/messages", {
            "content": "Second call must be rejected", "request_id": str(uuid.uuid4()),
        })
        self.assertEqual(status, 409)
        self.assertEqual(len(self.state()["messages"]), 1)
        self.assertEqual(len(self.calls), 1)
        self.release.set()
        self.wait_task(first)

    def test_invalid_reconnect_does_not_cancel_the_current_paid_request(self):
        self.block_transport = True
        self.connect()
        live_task = self.send("Synthetic valid current connection")
        self.assertTrue(self.started.wait(timeout=3))
        status, _ = self.request("POST", "/api/connection", {"api_key": "invalid-pasted-key"})
        self.assertEqual(status, 400)
        self.assertTrue(self.ai.public_state()["connected"])
        self.assertEqual(next(task for task in self.state()["tasks"] if task["id"] == live_task)["status"], "running")
        self.release.set()
        self.wait_task(live_task)
        self.assertEqual(len(self.calls), 1)

    def test_provider_failure_is_safe_in_task_state_and_never_retried(self):
        self.fail_transport = True
        self.connect()
        live_task = self.send("Synthetic transport failure test")
        state = self.wait_task(live_task, expected="failed")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(state["messages"]), 1)
        self.assertNotIn(SYNTHETIC_KEY, json.dumps(state))
        self.assertNotIn("Synthetic transport failure with secret", json.dumps(state))
        self.assertEqual(Decimal(str(self.ai.public_state()["reserved_usd"])), Decimal("0.02"))

    def test_disconnect_prevents_a_late_live_reply_from_being_published(self):
        self.block_transport = True
        self.connect()
        live_task = self.send("Synthetic live disconnect test")
        self.assertTrue(self.started.wait(timeout=3))
        self.post("/api/connection/disconnect", {})
        self.release.set()
        preview = self.send("Synthetic preview after disconnect")
        state = self.wait_task(preview)
        self.assertEqual(next(task for task in state["tasks"] if task["id"] == live_task)["status"], "cancelled")
        self.assertFalse(any(message["role"] == "assistant" and message["provider"] == "openai" for message in state["messages"]))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(Decimal(str(self.ai.public_state()["reserved_usd"])), Decimal("0.02"))

    def test_reset_fences_late_live_output(self):
        self.block_transport = True
        self.connect()
        live_task = self.send("Synthetic cancelled live turn")
        self.assertTrue(self.started.wait(timeout=3))
        self.post("/api/conversation/reset", {})
        self.release.set()
        fresh = self.send("Synthetic fresh live turn")
        state = self.wait_task(fresh)
        self.assertEqual(next(task for task in state["tasks"] if task["id"] == live_task)["status"], "cancelled")
        self.assertEqual(len(state["messages"]), 2)
        self.assertEqual(sum(message["role"] == "assistant" for message in state["messages"]), 1)
        self.assertEqual(len(self.calls), 2)

    def test_cancel_fences_late_live_output(self):
        self.block_transport = True
        self.connect()
        live_task = self.send("Synthetic cancelled live turn")
        self.assertTrue(self.started.wait(timeout=3))
        self.post(f"/api/tasks/{live_task}/cancel", {})
        self.release.set()
        fresh = self.send("Synthetic new live turn after cancellation")
        state = self.wait_task(fresh)
        self.assertEqual(next(task for task in state["tasks"] if task["id"] == live_task)["status"], "cancelled")
        self.assertEqual(len(state["messages"]), 3)
        self.assertEqual(sum(message["role"] == "assistant" for message in state["messages"]), 1)
        self.assertEqual(len(self.calls), 2)


if __name__ == "__main__":
    unittest.main()
