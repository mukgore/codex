"""Loopback-only integration checks for the local G4 replay service.

These tests exercise the actual source HTML scoring/gate functions through the
isolated Node bridge. They do not launch a browser, camera, or external service,
and they make no human-performance or held-out-generalization claim.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection
from http.cookies import SimpleCookie
import json
from pathlib import Path
import re
import threading
import unittest

from .actual import ActualEvaluator
from .server import CHALLENGE_TTL_SECONDS, LabService, create_server
from .validation import validate_frames


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "g4-handcaptcha-source"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class LoopbackClient:
    """Minimal HTTP client pinned to IPv4 loopback; it never uses proxies."""

    def __init__(self, port: int, cookie: str | None = None) -> None:
        self.port = port
        self.cookie = cookie

    def request(
        self,
        method: str,
        path: str,
        payload: object | None = None,
        *,
        raw_body: bytes | None = None,
        host: str | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        headers = {"Host": host or f"127.0.0.1:{self.port}"}
        body = raw_body
        if method == "POST":
            headers["Content-Type"] = "application/json"
            body = body if body is not None else json.dumps(payload).encode("utf-8")
        if self.cookie is not None:
            headers["Cookie"] = self.cookie
        conn = HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            return response.status, {k.lower(): v for k, v in response.getheaders()}, response.read()
        finally:
            conn.close()

    def post_json(self, path: str, payload: object) -> tuple[int, dict[str, str], dict]:
        status, headers, body = self.request("POST", path, payload)
        return status, headers, json.loads(body) if body else {}

    def get(self, path: str, *, host: str | None = None) -> tuple[int, dict[str, str], bytes]:
        return self.request("GET", path, host=host)


class G4ServerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SOURCE_ROOT.is_dir():
            raise unittest.SkipTest(f"local source checkout is unavailable: {SOURCE_ROOT.name}")
        cls.evaluator = ActualEvaluator(SOURCE_ROOT)
        if not cls.evaluator.sources:
            cls.evaluator.close()
            raise RuntimeError("actual source evaluator loaded no known sources")
        # A single deterministic source is used for every issued challenge.
        cls.source_key = sorted(cls.evaluator.sources)[0]

    @classmethod
    def tearDownClass(cls) -> None:
        evaluator = getattr(cls, "evaluator", None)
        if evaluator is not None:
            evaluator.close()

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.service = LabService(
            self.evaluator,
            clock=self.clock,
            ttl=CHALLENGE_TTL_SECONDS,
            source_order=[self.source_key],
        )
        self.httpd = create_server(self.service)
        self.assertEqual(self.httpd.server_address[0], "127.0.0.1")
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_port
        self.client = LoopbackClient(self.port)

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive(), "loopback HTTP server did not stop")

    def new_session(self) -> LoopbackClient:
        status, headers, body = self.client.post_json("/api/session", {})
        self.assertEqual(status, 200, body)
        self.assertTrue(body.get("session_created"))
        cookie_header = headers.get("set-cookie")
        self.assertIsNotNone(cookie_header)
        parsed = SimpleCookie()
        parsed.load(cookie_header)
        self.assertIn("g4_session", parsed)
        return LoopbackClient(self.port, f"g4_session={parsed['g4_session'].value}")

    def issue_challenge(self, client: LoopbackClient) -> dict:
        status, _, body = client.post_json("/api/challenge", {})
        self.assertEqual(status, 200, body)
        self.assertEqual(body.get("input_channel"), "offline_landmark_replay")
        self.assertEqual(body.get("media_url"), f"/media/{body.get('challenge_id')}")
        return body

    def exact_replay(self) -> list[dict]:
        # Uses the existing local source landmark input and actual HTML evaluator.
        return self.evaluator.frames(self.source_key)

    def _submit(self, client: LoopbackClient, challenge_id: str, frames: list[dict]):
        return client.post_json(
            "/api/submit", {"challenge_id": challenge_id, "frames": frames}
        )

    def test_public_page_app_and_media_are_local_only(self) -> None:
        page_status, page_headers, page = self.client.get("/")
        app_status, app_headers, app = self.client.get("/app.js")
        self.assertEqual(page_status, 200)
        self.assertEqual(app_status, 200)
        self.assertIn("text/html", page_headers["content-type"])
        self.assertIn("text/javascript", app_headers["content-type"])
        page_text, app_text = page.decode("utf-8"), app.decode("utf-8")
        self.assertIn("/app.js", page_text)
        self.assertIn("/api/session", app_text)
        self.assertIn("/api/challenge", app_text)
        self.assertIn("/api/submit", app_text)
        self.assertNotRegex(page_text + app_text, re.compile(r"https?://|//[\w.-]+/", re.I))
        self.assertNotIn("getUserMedia", page_text + app_text)
        self.assertNotIn("mediaDevices", page_text + app_text)
        self.assertIn("connect-src 'self'", page_headers["content-security-policy"])
        self.assertIn("media-src 'self'", page_headers["content-security-policy"])

        client = self.new_session()
        challenge = self.issue_challenge(client)
        media_status, media_headers, media = client.get(challenge["media_url"])
        self.assertEqual(media_status, 200)
        self.assertEqual(media_headers["content-type"], "video/mp4")
        self.assertGreater(len(media), 12)
        self.assertEqual(media[4:8], b"ftyp")

        for private_path in (
            "/manifest.json",
            "/pool_manifest.json",
            "/landmarks_base.json",
            "/custom01_landmarks.json",
        ):
            with self.subTest(path=private_path):
                status, _, _ = client.get(private_path)
                self.assertEqual(status, 404)

    def test_host_guard_and_challenge_requires_session_cookie(self) -> None:
        status, _, body = self.client.post_json("/api/challenge", {})
        self.assertEqual(status, 403, body)
        status, _, body = self.client.get("/", host=f"attacker.invalid:{self.port}")
        self.assertEqual(status, 403)
        self.assertIn(b"host_denied", body)

    def test_client_passed_or_score_fields_are_rejected(self) -> None:
        client = self.new_session()
        frames = self.exact_replay()
        for injected in ({"passed": True}, {"score": 1.0}):
            challenge = self.issue_challenge(client)
            payload = {"challenge_id": challenge["challenge_id"], "frames": frames, **injected}
            with self.subTest(field=next(iter(injected))):
                status, _, body = client.post_json("/api/submit", payload)
                self.assertEqual(status, 400, body)

    def test_known_source_exact_replay_uses_actual_gate_score_and_one_time_grant(self) -> None:
        client = self.new_session()
        challenge = self.issue_challenge(client)
        status, _, result = self._submit(client, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(status, 200, result)
        self.assertTrue(result["validation_pass"])
        self.assertTrue(result["gate_pass"], result)
        self.assertTrue(result["score_pass"], result)
        self.assertTrue(result["grant_id"])
        self.assertFalse(result["protected_action_allowed"])

        action_status, _, action = client.post_json(
            "/api/protected_action", {"grant_id": result["grant_id"]}
        )
        self.assertEqual(action_status, 200)
        self.assertTrue(action["protected_action_allowed"])
        self.assertEqual(action["protected_action_counter"], 1)

    def test_challenge_is_bound_to_its_session_and_replay_is_rejected(self) -> None:
        owner = self.new_session()
        other = self.new_session()
        challenge = self.issue_challenge(owner)

        media_status, _, _ = other.get(challenge["media_url"])
        self.assertEqual(media_status, 403)
        other_status, _, _ = self._submit(other, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(other_status, 403)

        status, _, result = self._submit(owner, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(status, 200, result)
        replay_status, _, _ = self._submit(owner, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(replay_status, 403)

        wrong_session_action, _, denied = other.post_json(
            "/api/protected_action", {"grant_id": result["grant_id"]}
        )
        self.assertEqual(wrong_session_action, 200)
        self.assertFalse(denied["protected_action_allowed"])
        owner_action, _, allowed = owner.post_json(
            "/api/protected_action", {"grant_id": result["grant_id"]}
        )
        self.assertEqual(owner_action, 200)
        self.assertTrue(allowed["protected_action_allowed"])
        reused_action, _, reused = owner.post_json(
            "/api/protected_action", {"grant_id": result["grant_id"]}
        )
        self.assertEqual(reused_action, 200)
        self.assertFalse(reused["protected_action_allowed"])

    def test_expired_challenge_and_grant_are_denied(self) -> None:
        client = self.new_session()
        challenge = self.issue_challenge(client)
        status, _, result = self._submit(client, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(status, 200, result)
        self.assertTrue(result["grant_id"])
        unsubmitted = self.issue_challenge(client)

        self.clock.now = CHALLENGE_TTL_SECONDS + 1
        expired_submit, _, _ = self._submit(client, challenge["challenge_id"], self.exact_replay())
        self.assertEqual(expired_submit, 403)
        expired_fresh_submit, _, _ = self._submit(
            client, unsubmitted["challenge_id"], self.exact_replay()
        )
        self.assertEqual(expired_fresh_submit, 403)
        expired_media, _, _ = client.get(unsubmitted["media_url"])
        self.assertEqual(expired_media, 403)
        expired_action, _, action = client.post_json(
            "/api/protected_action", {"grant_id": result["grant_id"]}
        )
        self.assertEqual(expired_action, 200)
        self.assertFalse(action["protected_action_allowed"])

    def test_invalid_frame_inputs_are_rejected_without_grants(self) -> None:
        client = self.new_session()
        valid_lm = [[float(i), 1.0] for i in range(21)]
        valid_lm[0] = [0.0, 0.0]
        valid_lm[9] = [1.0, 0.0]
        malformed_cases = {
            "boolean timestamp": [{"t_ms": True, "lm": valid_lm}],
            "boolean coordinate": [{"t_ms": 0, "lm": [[False, 0.0]] + valid_lm[1:]}],
            "wrong shape": [{"t_ms": 0, "lm": [[0.0, 0.0]] * 20}],
            "zero wrist scale": [{"t_ms": 0, "lm": [[0.0, 0.0]] * 21}],
            "duplicate timestamp": [
                {"t_ms": 0, "lm": valid_lm}, {"t_ms": 0, "lm": None}
            ],
            "nonmonotonic timestamp": [
                {"t_ms": 1, "lm": valid_lm}, {"t_ms": 0, "lm": None}
            ],
            "nonfinite coordinate": [
                {"t_ms": 0, "lm": [[float("inf"), 0.0]] + valid_lm[1:]}
            ],
        }
        for label, frames in malformed_cases.items():
            with self.subTest(case=label):
                challenge = self.issue_challenge(client)
                status, _, body = self._submit(client, challenge["challenge_id"], frames)
                self.assertEqual(status, 400, body)

        challenge = self.issue_challenge(client)
        payload = {"challenge_id": challenge["challenge_id"], "frames": [{"t_ms": 0, "lm": valid_lm}]}
        raw_nan = json.dumps(payload).replace('"t_ms": 0', '"t_ms": NaN').encode("utf-8")
        status, _, _ = client.request("POST", "/api/submit", raw_body=raw_nan)
        self.assertEqual(status, 400)

    def test_null_landmark_is_preserved_but_all_null_input_never_grants(self) -> None:
        client = self.new_session()
        challenge = self.issue_challenge(client)
        all_null = [{"t_ms": 0.0, "lm": None}, {"t_ms": 1.0, "lm": None}]
        self.assertIsNone(validate_frames(all_null)[0]["lm"])
        status, _, result = self._submit(client, challenge["challenge_id"], all_null)
        self.assertIn(status, (200, 400))
        if status == 200:
            self.assertTrue(result["validation_pass"])
            self.assertFalse(result["gate_pass"])
            self.assertFalse(result.get("grant_id"))
            action_status, _, action = client.post_json(
                "/api/protected_action", {"grant_id": result.get("grant_id")}
            )
            self.assertEqual(action_status, 400)
            self.assertFalse(action.get("protected_action_allowed", False))

    def test_concurrent_submit_and_grant_consumption_are_atomic(self) -> None:
        client = self.new_session()
        challenge = self.issue_challenge(client)
        frames = self.exact_replay()
        with ThreadPoolExecutor(max_workers=2) as pool:
            submitted = list(pool.map(
                lambda _: self._submit(client, challenge["challenge_id"], frames), range(2)
            ))
        statuses = sorted(item[0] for item in submitted)
        self.assertEqual(statuses, [200, 403])
        winner = next(item[2] for item in submitted if item[0] == 200)
        self.assertTrue(winner["grant_id"])

        def consume_once(_: int):
            return client.post_json(
                "/api/protected_action", {"grant_id": winner["grant_id"]}
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            actions = list(pool.map(consume_once, range(2)))
        self.assertTrue(all(status == 200 for status, _, _ in actions))
        self.assertEqual(sum(bool(body["protected_action_allowed"]) for _, _, body in actions), 1)
        self.assertEqual(self.service.protected_actions, 1)


if __name__ == "__main__":
    unittest.main()
