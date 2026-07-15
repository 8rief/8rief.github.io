#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from session_auth_demo import AuthService, Request, extract_session_id


class ProbeClock:
    def __init__(self, now: int = 10_000) -> None:
        self.now = now

    def __call__(self) -> int:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += seconds


class ProbeTokens:
    def __init__(self) -> None:
        self.counts = {"salt": 0, "session": 0, "csrf": 0}

    def __call__(self, kind: str) -> str:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        if kind == "salt":
            return f"{self.counts[kind]:032x}"
        return f"probe-{kind}-{self.counts[kind]:02d}"


def bool_word(value: bool) -> str:
    return "yes" if value else "no"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)

    clock = ProbeClock()
    tokens = ProbeTokens()
    service = AuthService(ttl_seconds=120, now=clock, token_factory=tokens)
    alice = service.register_user("alice", "correct horse", role="user", email="alice@example.test")
    service.register_user("admin", "correct battery", role="admin", email="admin@example.test")

    login = service.handle(Request("POST", "/login", {}, {"username": "alice", "password": "correct horse"}))
    cookie = login.headers["Set-Cookie"]
    csrf = login.body["csrf_token"]
    session_id = extract_session_id(cookie)

    me = service.handle(Request("GET", "/me", {"Cookie": cookie}))
    forged = service.handle(Request("GET", "/me", {"Cookie": "sid=alice"}))
    csrf_missing = service.handle(Request("POST", "/email", {"Cookie": cookie}, {"email": "new@example.test"}))
    csrf_ok = service.handle(Request("POST", "/email", {"Cookie": cookie, "X-CSRF-Token": csrf}, {"email": "new@example.test"}))
    user_admin = service.handle(Request("GET", "/admin/report", {"Cookie": cookie}))
    admin_login = service.handle(Request("POST", "/login", {}, {"username": "admin", "password": "correct battery"}))
    admin_report = service.handle(Request("GET", "/admin/report", {"Cookie": admin_login.headers["Set-Cookie"]}))
    logout = service.handle(Request("POST", "/logout", {"Cookie": cookie}))
    after_logout = service.handle(Request("GET", "/me", {"Cookie": cookie}))
    expiring = service.handle(Request("POST", "/login", {}, {"username": "alice", "password": "correct horse"}))
    expiring_cookie = expiring.headers["Set-Cookie"]
    clock.advance(121)
    expired = service.handle(Request("GET", "/me", {"Cookie": expiring_cookie}))

    checks = {
        "login_status": int(login.status),
        "password_stored_plaintext": alice.password_hash == "correct horse",
        "cookie_httponly": "HttpOnly" in cookie,
        "cookie_samesite_lax": "SameSite=Lax" in cookie,
        "cookie_secure": "Secure" in cookie,
        "session_id_not_username": session_id not in {"alice", "admin", None},
        "me_status": int(me.status),
        "forged_cookie_status": int(forged.status),
        "forged_cookie_rejected": int(forged.status) == 401,
        "csrf_missing_status": int(csrf_missing.status),
        "csrf_required": int(csrf_missing.status) == 403,
        "csrf_ok_status": int(csrf_ok.status),
        "csrf_accepted": int(csrf_ok.status) == 200,
        "user_admin_status": int(user_admin.status),
        "user_admin_forbidden": int(user_admin.status) == 403,
        "admin_report_status": int(admin_report.status),
        "admin_allowed": int(admin_report.status) == 200,
        "logout_status": int(logout.status),
        "logout_revoked": int(after_logout.status) == 401 and after_logout.body["error"]["code"] == "revoked_session",
        "expiry_rejected": int(expired.status) == 401 and expired.body["error"]["code"] == "expired_session",
    }
    checks["run_status"] = "ok" if all(
        [
            checks["login_status"] == 200,
            not checks["password_stored_plaintext"],
            checks["cookie_httponly"],
            checks["cookie_samesite_lax"],
            checks["cookie_secure"],
            checks["session_id_not_username"],
            checks["forged_cookie_rejected"],
            checks["csrf_required"],
            checks["csrf_accepted"],
            checks["user_admin_forbidden"],
            checks["admin_allowed"],
            checks["logout_revoked"],
            checks["expiry_rejected"],
        ]
    ) else "failed"

    (reports / "session_auth_probe.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    write_jsonl(reports / "session_events.jsonl", service.events())
    report = "\n".join(
        [
            "# Session auth probe report",
            "",
            f"- Login status: {checks['login_status']}",
            f"- Password stored as plaintext: {bool_word(checks['password_stored_plaintext'])}",
            f"- Cookie flags: HttpOnly={bool_word(checks['cookie_httponly'])}, SameSite=Lax={bool_word(checks['cookie_samesite_lax'])}, Secure={bool_word(checks['cookie_secure'])}",
            f"- Session id differs from username: {bool_word(checks['session_id_not_username'])}",
            f"- Forged cookie rejected: {bool_word(checks['forged_cookie_rejected'])}",
            f"- CSRF required then accepted: {bool_word(checks['csrf_required'])}/{bool_word(checks['csrf_accepted'])}",
            f"- User/admin role boundary: user_forbidden={bool_word(checks['user_admin_forbidden'])}, admin_allowed={bool_word(checks['admin_allowed'])}",
            f"- Logout revoked old session: {bool_word(checks['logout_revoked'])}",
            f"- Expired session rejected: {bool_word(checks['expiry_rejected'])}",
            f"- Run status: {checks['run_status']}",
            "",
        ]
    )
    (reports / "session_auth_report.md").write_text(report, encoding="utf-8")

    print(f"LOGIN_STATUS={checks['login_status']}")
    print(f"PASSWORD_STORED_PLAINTEXT={bool_word(checks['password_stored_plaintext'])}")
    print(f"COOKIE_HTTPONLY={bool_word(checks['cookie_httponly'])}")
    print(f"COOKIE_SAMESITE_LAX={bool_word(checks['cookie_samesite_lax'])}")
    print(f"COOKIE_SECURE={bool_word(checks['cookie_secure'])}")
    print(f"SESSION_ID_NOT_USERNAME={bool_word(checks['session_id_not_username'])}")
    print(f"FORGED_COOKIE_REJECTED={bool_word(checks['forged_cookie_rejected'])}")
    print(f"CSRF_REQUIRED={bool_word(checks['csrf_required'])}")
    print(f"CSRF_ACCEPTED={bool_word(checks['csrf_accepted'])}")
    print(f"USER_ADMIN_FORBIDDEN={bool_word(checks['user_admin_forbidden'])}")
    print(f"ADMIN_ALLOWED={bool_word(checks['admin_allowed'])}")
    print(f"LOGOUT_REVOKED={bool_word(checks['logout_revoked'])}")
    print(f"EXPIRY_REJECTED={bool_word(checks['expiry_rejected'])}")
    print(f"RUN_STATUS={checks['run_status']}")
    return 0 if checks["run_status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
