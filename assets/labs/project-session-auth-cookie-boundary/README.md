# Project session auth and cookie boundary lab

This lab is a small, standard-library Python model of login, server-side sessions, Cookie flags, CSRF checks, role checks, logout, and session expiry. It is meant to make the application boundary visible: the browser sends an opaque session id, while the server keeps the identity, role, CSRF token, revocation state, and expiry time.

## Run

```bash
./run_lab.sh
```

Expected stable markers include:

```text
LOGIN_STATUS=200
PASSWORD_STORED_PLAINTEXT=no
COOKIE_HTTPONLY=yes
COOKIE_SAMESITE_LAX=yes
SESSION_ID_NOT_USERNAME=yes
FORGED_COOKIE_REJECTED=yes
CSRF_REQUIRED=yes
CSRF_ACCEPTED=yes
USER_ADMIN_FORBIDDEN=yes
ADMIN_ALLOWED=yes
LOGOUT_REVOKED=yes
EXPIRY_REJECTED=yes
RUN_STATUS=ok
session_auth_lab_status=ok
```

The runner writes local evidence under `reports/`:

- `session_auth_probe.json`: machine-readable check results.
- `session_auth_report.md`: short human-readable report.
- `session_events.jsonl`: event log without password values.

`reports/` is generated output and is intentionally not part of the public package.

## What this proves

- The stored password material is a salted PBKDF2 verifier, not the plaintext password.
- A Cookie contains an opaque session id; a forged `sid=alice` value is rejected because the server has no matching session.
- The Cookie header includes `HttpOnly`, `SameSite=Lax`, `Secure`, `Path=/`, and `Max-Age` attributes.
- A state-changing request requires the per-session `X-CSRF-Token`.
- Admin authorization is decided from the server-side user record.
- Logout and expiry both invalidate a previously usable session.

## What this does not prove

This is not a complete production identity system. It does not implement account recovery, MFA, rate limiting, audit retention, distributed session storage, OAuth/OIDC, reverse-proxy TLS termination, or real browser behavior. Those are later layers; this lab isolates the core request boundary that a beginner must understand first.
