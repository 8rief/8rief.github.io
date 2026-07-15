#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
import sys
import time
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from typing import Any, Callable

PBKDF2_ITERATIONS = 120_000
SESSION_COOKIE = "sid"
USERNAME_RE = re.compile(r"^[a-z][a-z0-9_-]{2,31}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class User:
    username: str
    password_salt: str
    password_hash: str
    role: str
    email: str


@dataclass
class Session:
    session_id: str
    username: str
    csrf_token: str
    expires_at: int
    revoked: bool = False


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    headers: dict[str, str]
    json_body: dict[str, Any] | None = None


@dataclass(frozen=True)
class Response:
    status: int
    headers: dict[str, str]
    body: dict[str, Any] | None


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: Session


class AuthError(ValueError):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


TokenFactory = Callable[[str], str]
Clock = Callable[[], int]


def default_token_factory(kind: str) -> str:
    if kind == "salt":
        return secrets.token_hex(16)
    return secrets.token_urlsafe(32)


def hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return digest.hex()


def make_cookie(session_id: str, *, max_age: int) -> str:
    return f"{SESSION_COOKIE}={session_id}; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age={max_age}"


def clear_cookie() -> str:
    return f"{SESSION_COOKIE}=; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=0"


def extract_session_id(cookie_header: str | None) -> str | None:
    if not cookie_header:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header)
    except CookieError:
        return None
    morsel = cookie.get(SESSION_COOKIE)
    if morsel is None:
        return None
    value = morsel.value.strip()
    return value or None


def error_body(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


class AuthService:
    def __init__(
        self,
        *,
        ttl_seconds: int = 1_800,
        now: Clock | None = None,
        token_factory: TokenFactory | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self._now = now or (lambda: int(time.time()))
        self._token_factory = token_factory or default_token_factory
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}
        self._events: list[dict[str, Any]] = []

    def register_user(self, username: str, password: str, *, role: str = "user", email: str | None = None) -> User:
        username = validate_username(username)
        validate_password(password)
        if role not in {"user", "admin"}:
            raise ValueError("role must be user or admin")
        if username in self._users:
            raise ValueError(f"user {username} already exists")
        salt = self._token_factory("salt")
        user = User(
            username=username,
            password_salt=salt,
            password_hash=hash_password(password, salt),
            role=role,
            email=email or f"{username}@example.test",
        )
        self._users[username] = user
        self._record("user_registered", username=username, role=role)
        return user

    def verify_password(self, user: User, password: str) -> bool:
        candidate = hash_password(password, user.password_salt)
        return hmac.compare_digest(candidate, user.password_hash)

    def handle(self, request: Request) -> Response:
        method = request.method.upper()
        try:
            if method == "POST" and request.path == "/login":
                return self._login(request.json_body or {})
            if method == "GET" and request.path == "/me":
                context = self._authenticate(request.headers.get("Cookie"))
                return Response(HTTPStatus.OK, {}, {"user": public_user(context.user), "session_expires_at": context.session.expires_at})
            if method == "POST" and request.path == "/email":
                context = self._authenticate(request.headers.get("Cookie"))
                self._require_csrf(request, context.session)
                return self._change_email(context.user, request.json_body or {})
            if method == "GET" and request.path == "/admin/report":
                context = self._authenticate(request.headers.get("Cookie"))
                if context.user.role != "admin":
                    raise AuthError(HTTPStatus.FORBIDDEN, "forbidden", "this endpoint requires the admin role")
                self._record("admin_report_viewed", username=context.user.username)
                return Response(HTTPStatus.OK, {}, {"active_sessions": self.active_session_count(), "users": len(self._users)})
            if method == "POST" and request.path == "/logout":
                context = self._authenticate(request.headers.get("Cookie"))
                context.session.revoked = True
                self._record("session_revoked", username=context.user.username)
                return Response(HTTPStatus.OK, {"Set-Cookie": clear_cookie()}, {"status": "logged_out"})
            return Response(HTTPStatus.NOT_FOUND, {}, error_body("not_found", f"{method} {request.path} is not defined"))
        except AuthError as exc:
            self._record("request_rejected", path=request.path, code=exc.code, status=int(exc.status))
            return Response(exc.status, {}, error_body(exc.code, exc.message))

    def events(self) -> list[dict[str, Any]]:
        return [dict(event) for event in self._events]

    def active_session_count(self) -> int:
        now = self._now()
        return sum(1 for session in self._sessions.values() if not session.revoked and session.expires_at > now)

    def _login(self, body: dict[str, Any]) -> Response:
        username = body.get("username")
        password = body.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            raise AuthError(HTTPStatus.BAD_REQUEST, "bad_request", "username and password are required")
        user = self._users.get(username)
        if user is None or not self.verify_password(user, password):
            self._record("login_failed", username=username)
            raise AuthError(HTTPStatus.UNAUTHORIZED, "invalid_credentials", "username or password is incorrect")
        session_id = self._token_factory("session")
        csrf_token = self._token_factory("csrf")
        session = Session(
            session_id=session_id,
            username=username,
            csrf_token=csrf_token,
            expires_at=self._now() + self.ttl_seconds,
        )
        self._sessions[session_id] = session
        self._record("login_succeeded", username=username)
        return Response(
            HTTPStatus.OK,
            {"Set-Cookie": make_cookie(session_id, max_age=self.ttl_seconds)},
            {"user": public_user(user), "csrf_token": csrf_token, "expires_in": self.ttl_seconds},
        )

    def _authenticate(self, cookie_header: str | None) -> AuthContext:
        session_id = extract_session_id(cookie_header)
        if session_id is None:
            raise AuthError(HTTPStatus.UNAUTHORIZED, "missing_session", "request has no valid session cookie")
        session = self._sessions.get(session_id)
        if session is None:
            raise AuthError(HTTPStatus.UNAUTHORIZED, "invalid_session", "session id is not known by the server")
        if session.revoked:
            raise AuthError(HTTPStatus.UNAUTHORIZED, "revoked_session", "session has been logged out")
        if session.expires_at <= self._now():
            raise AuthError(HTTPStatus.UNAUTHORIZED, "expired_session", "session has expired")
        user = self._users.get(session.username)
        if user is None:
            raise AuthError(HTTPStatus.UNAUTHORIZED, "orphan_session", "session user no longer exists")
        return AuthContext(user=user, session=session)

    def _require_csrf(self, request: Request, session: Session) -> None:
        supplied = request.headers.get("X-CSRF-Token", "")
        if not supplied or not hmac.compare_digest(supplied, session.csrf_token):
            raise AuthError(HTTPStatus.FORBIDDEN, "csrf_required", "state-changing request must include the session CSRF token")

    def _change_email(self, user: User, body: dict[str, Any]) -> Response:
        email = body.get("email")
        if not isinstance(email, str) or not EMAIL_RE.match(email):
            raise AuthError(HTTPStatus.BAD_REQUEST, "bad_email", "email must look like name@example.test")
        user.email = email
        self._record("email_changed", username=user.username)
        return Response(HTTPStatus.OK, {}, {"user": public_user(user), "changed": True})

    def _record(self, event: str, **fields: Any) -> None:
        clean_fields = {key: value for key, value in fields.items() if key != "password"}
        self._events.append({"ts": self._now(), "event": event, **clean_fields})


def validate_username(username: str) -> str:
    if not isinstance(username, str) or not USERNAME_RE.match(username):
        raise ValueError("username must match [a-z][a-z0-9_-]{2,31}")
    return username


def validate_password(password: str) -> None:
    if not isinstance(password, str) or len(password) < 8:
        raise ValueError("password must have at least 8 characters")


def public_user(user: User) -> dict[str, str]:
    return {"username": user.username, "role": user.role, "email": user.email}


def response_to_json(response: Response) -> str:
    return json.dumps({"status": int(response.status), "headers": response.headers, "body": response.body}, ensure_ascii=False, sort_keys=True)


def demo_service() -> AuthService:
    service = AuthService()
    service.register_user("alice", "correct horse", role="user", email="alice@example.test")
    service.register_user("admin", "correct battery", role="admin", email="admin@example.test")
    return service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one session-auth teaching demo request")
    parser.add_argument("--username", default="alice")
    parser.add_argument("--password", default="correct horse")
    args = parser.parse_args(argv)
    service = demo_service()
    response = service.handle(Request("POST", "/login", {}, {"username": args.username, "password": args.password}))
    print(response_to_json(response))
    return 0 if response.status == HTTPStatus.OK else 1


if __name__ == "__main__":
    raise SystemExit(main())
