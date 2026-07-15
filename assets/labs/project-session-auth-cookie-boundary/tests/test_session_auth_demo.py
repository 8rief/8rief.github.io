from __future__ import annotations

import unittest

from session_auth_demo import AuthService, Request, extract_session_id


class DeterministicClock:
    def __init__(self, now: int = 1_000) -> None:
        self.now = now

    def __call__(self) -> int:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += seconds


class DeterministicTokens:
    def __init__(self) -> None:
        self.counts = {"salt": 0, "session": 0, "csrf": 0}

    def __call__(self, kind: str) -> str:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if kind == "salt":
            return f"{self.counts[kind]:032x}"
        return f"{kind}-{self.counts[kind]:02d}"


class SessionAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = DeterministicClock()
        self.tokens = DeterministicTokens()
        self.service = AuthService(ttl_seconds=60, now=self.clock, token_factory=self.tokens)
        self.alice = self.service.register_user("alice", "correct horse", role="user")
        self.admin = self.service.register_user("admin", "correct battery", role="admin")

    def login(self, username: str = "alice", password: str = "correct horse"):
        return self.service.handle(Request("POST", "/login", {}, {"username": username, "password": password}))

    def test_password_is_not_stored_in_plaintext_and_login_sets_cookie_flags(self) -> None:
        self.assertNotEqual(self.alice.password_hash, "correct horse")
        self.assertEqual(len(self.alice.password_salt), 32)
        response = self.login()
        self.assertEqual(response.status, 200)
        cookie = response.headers["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("Path=/", cookie)
        self.assertEqual(extract_session_id(cookie), "session-01")

    def test_cookie_points_to_server_side_session_not_username(self) -> None:
        response = self.login()
        me = self.service.handle(Request("GET", "/me", {"Cookie": response.headers["Set-Cookie"]}))
        self.assertEqual(me.status, 200)
        self.assertEqual(me.body["user"]["username"], "alice")

        forged = self.service.handle(Request("GET", "/me", {"Cookie": "sid=alice"}))
        self.assertEqual(forged.status, 401)
        self.assertEqual(forged.body["error"]["code"], "invalid_session")

    def test_state_changing_request_requires_per_session_csrf_token(self) -> None:
        response = self.login()
        cookie = response.headers["Set-Cookie"]
        rejected = self.service.handle(Request("POST", "/email", {"Cookie": cookie}, {"email": "new@example.test"}))
        self.assertEqual(rejected.status, 403)
        self.assertEqual(rejected.body["error"]["code"], "csrf_required")

        accepted = self.service.handle(
            Request(
                "POST",
                "/email",
                {"Cookie": cookie, "X-CSRF-Token": response.body["csrf_token"]},
                {"email": "new@example.test"},
            )
        )
        self.assertEqual(accepted.status, 200)
        self.assertEqual(accepted.body["user"]["email"], "new@example.test")

    def test_role_check_is_decided_from_server_side_user_record(self) -> None:
        user_login = self.login()
        user_report = self.service.handle(Request("GET", "/admin/report", {"Cookie": user_login.headers["Set-Cookie"]}))
        self.assertEqual(user_report.status, 403)

        admin_login = self.login("admin", "correct battery")
        admin_report = self.service.handle(Request("GET", "/admin/report", {"Cookie": admin_login.headers["Set-Cookie"]}))
        self.assertEqual(admin_report.status, 200)
        self.assertEqual(admin_report.body["users"], 2)

    def test_logout_and_expiry_invalidate_sessions(self) -> None:
        response = self.login()
        cookie = response.headers["Set-Cookie"]
        logout = self.service.handle(Request("POST", "/logout", {"Cookie": cookie}))
        self.assertEqual(logout.status, 200)
        self.assertIn("Max-Age=0", logout.headers["Set-Cookie"])
        after_logout = self.service.handle(Request("GET", "/me", {"Cookie": cookie}))
        self.assertEqual(after_logout.status, 401)
        self.assertEqual(after_logout.body["error"]["code"], "revoked_session")

        second = self.login()
        second_cookie = second.headers["Set-Cookie"]
        self.clock.advance(61)
        expired = self.service.handle(Request("GET", "/me", {"Cookie": second_cookie}))
        self.assertEqual(expired.status, 401)
        self.assertEqual(expired.body["error"]["code"], "expired_session")

    def test_bad_password_uses_generic_error_shape(self) -> None:
        response = self.login(password="wrong horse")
        self.assertEqual(response.status, 401)
        self.assertEqual(response.body["error"]["code"], "invalid_credentials")
        self.assertNotIn("password_hash", str(response.body))


if __name__ == "__main__":
    unittest.main()
