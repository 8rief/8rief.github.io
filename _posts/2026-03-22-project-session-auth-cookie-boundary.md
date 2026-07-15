---
layout: post
title: "项目登录、Cookie 与会话边界：用户状态怎么变成可测试证据"
date: 2026-03-22 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [project, http, cookie, session, csrf, auth, testing]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-session-auth-cookie-boundary/README.md`](/assets/labs/project-session-auth-cookie-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

很多 Web 项目一开始只有公开接口：列任务、建任务、改任务。下一步通常会出现一个需求：用户登录后只能看到自己的数据，管理员可以看报表，退出登录后旧请求失效。这个需求听起来是“登录功能”，落到工程里其实是几个状态边界要同时成立：密码怎么保存，浏览器下次请求带什么，服务器如何找到用户，状态修改为什么要多一个 CSRF token，权限判断从哪里来，旧会话何时失效。

本文用一个只依赖 Python 标准库的小实验把这些边界跑出来。实验代码在 [`/labs/#project-session-auth-cookie-boundary`](/labs/#project-session-auth-cookie-boundary)，也可以直接看公开包 [`README.md`](/assets/labs/project-session-auth-cookie-boundary/README.md) 和 [`run_lab.sh`](/assets/labs/project-session-auth-cookie-boundary/run_lab.sh)。

## 先把问题拆成状态流

一个登录请求不能只回答“用户名密码对不对”。它至少要建立这条链路：

```text
POST /login
  body: username + password
  server: 查用户记录，校验 password verifier
  server: 生成随机 session_id 和 csrf_token
  response: Set-Cookie: sid=<opaque>; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=1800

GET /me
  request: Cookie: sid=<opaque>
  server: 用 sid 查 server-side session
  server: 检查 revoked、expires_at、user record
  response: 当前用户的公开字段

POST /email
  request: Cookie: sid=<opaque> + X-CSRF-Token: <per-session token>
  server: 先认证 session，再校验 csrf_token，再修改 email
```

这里的关键词是 **opaque session id**。为什么需要单独的 session id：因为浏览器必须带回一个短标识来延续会话，但身份、角色和失效状态必须由服务器决定。Cookie 里放的是一个服务器能查询的随机标识，不放 `username=alice`，也不放 `role=admin`。用户是谁、角色是什么、什么时候过期、有没有退出，都由服务器保存的 session 和 user record 决定。

## 实验目标

这篇文章的目标很具体。跑完实验后，你应该能解释下面这些观察：

1. 密码不会以明文形式进入用户记录。
2. 登录成功会返回带属性的 `Set-Cookie`。
3. Cookie 里的 `sid` 只是随机会话标识，伪造 `sid=alice` 会失败。
4. `GET /me` 只需要 Cookie；`POST /email` 还需要 `X-CSRF-Token`。
5. 普通用户访问管理员报表返回 403，管理员返回 200。
6. logout 和 expiry 都能让旧 Cookie 失效。

这不是完整身份系统。账号恢复、MFA、限速、分布式 session 存储、OAuth/OIDC、TLS 终止和浏览器端真实 SameSite 行为都在后续层。现在先把一个初学者最容易混在一起的请求边界理清楚。

## 运行实验

在仓库里进入实验目录：

```bash
cd assets/labs/project-session-auth-cookie-boundary
bash run_lab.sh
```

成功时会看到类似输出：

```text
LOGIN_STATUS=200
PASSWORD_STORED_PLAINTEXT=no
COOKIE_HTTPONLY=yes
COOKIE_SAMESITE_LAX=yes
COOKIE_SECURE=yes
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

这些 marker 对应的是可检查行为，不是装饰性输出。`PASSWORD_STORED_PLAINTEXT=no` 说明用户记录里没有保存原始密码；`FORGED_COOKIE_REJECTED=yes` 说明服务端没有把 Cookie 字符串直接当用户身份；`CSRF_REQUIRED=yes` 说明状态修改请求比读取请求多一道 token 检查；`LOGOUT_REVOKED=yes` 和 `EXPIRY_REJECTED=yes` 说明会话生命周期不是只在浏览器里发生。

## 第一层：密码字段保存什么

用户表或用户记录里不能保存明文密码。实验里用 `hashlib.pbkdf2_hmac` 生成 password verifier，用 `hmac.compare_digest` 做恒定时间风格的比较：

```python
def hash_password(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120_000,
    )
    return digest.hex()


def verify_password(user: User, password: str) -> bool:
    candidate = hash_password(password, user.password_salt)
    return hmac.compare_digest(candidate, user.password_hash)
```

这段代码的设计点有三个：

- `salt` 每个用户不同，避免相同密码得到相同 verifier。
- `PBKDF2` 故意做很多轮，让离线猜密码成本变高。
- `compare_digest` 避免用普通字符串比较表达敏感值相等性。

实验没有声称 PBKDF2 是所有场景的最佳选择。真实系统还要考虑参数升级、专用 password hashing 算法、密码策略、泄漏检测和限速。这里先证明一个底线：用户记录里没有保存可直接读出的密码。

## 第二层：Cookie 保存会话标识，不保存身份结论

登录成功后，服务器创建 session：

```python
session = Session(
    session_id=session_id,
    username=username,
    csrf_token=csrf_token,
    expires_at=now() + ttl_seconds,
)
sessions[session_id] = session
```

返回给浏览器的是：

```text
Set-Cookie: sid=<session_id>; HttpOnly; SameSite=Lax; Secure; Path=/; Max-Age=1800
```

这些属性各自解决一个边界问题：

| 属性 | 作用 | 初学时容易误解的地方 |
| --- | --- | --- |
| `sid=<session_id>` | 浏览器下次请求时带回来的 opaque id | 它不是用户名，也不是角色，也不应该被业务代码解释成权限 |
| `HttpOnly` | 限制脚本读取 Cookie | 它降低脚本窃取 Cookie 的风险，但不能修复服务端鉴权错误 |
| `SameSite=Lax` | 降低跨站请求自动带 Cookie 的风险 | 它不能替代服务端 CSRF token 检查 |
| `Secure` | 只通过 HTTPS 发送 | 本地教学环境仍可检查字符串属性；生产必须配合 HTTPS |
| `Path=/` | 指定 Cookie 适用路径 | 路径不是权限系统，只是浏览器发送范围的一部分 |
| `Max-Age=1800` | 浏览器端保存时间 | 服务端仍要检查自己的 `expires_at` |

实验专门检查伪造 Cookie：

```python
forged = service.handle(Request("GET", "/me", {"Cookie": "sid=alice"}))
assert forged.status == 401
assert forged.body["error"]["code"] == "invalid_session"
```

这条测试很关键。它证明服务端没有把 `sid` 的字面值当成用户名，也没有让客户端决定自己的身份。

## 第三层：认证、授权和 CSRF 分开看

三个词经常混在一起，实际代码里要分层处理：

1. **认证**：这个请求能否对应到一个有效 session。
2. **授权**：这个 session 对应的用户是否有权限做这件事。
3. **CSRF 检查**：这个状态修改请求是否带了本 session 的附加 token。

实验里的 `GET /me` 只需要认证：

```python
context = authenticate(request.headers.get("Cookie"))
return {"user": public_user(context.user)}
```

管理员报表需要认证加角色判断：

```python
context = authenticate(request.headers.get("Cookie"))
if context.user.role != "admin":
    return 403
return {"users": len(users), "active_sessions": active_session_count()}
```

修改 email 需要认证加 CSRF：

```python
context = authenticate(request.headers.get("Cookie"))
require_csrf(request, context.session)
change_email(context.user, request.json_body)
```

状态修改请求需要 CSRF token 的原因在于：浏览器会按 Cookie 规则自动携带 Cookie。用户已经登录时，跨站页面可能诱导浏览器发起请求。服务端要求一个攻击页面读不到的 per-session token，可以把“浏览器自动带 Cookie”与“用户在本站页面发出的有效修改动作”区分开。

实验输出中的两行对应这个边界：

```text
CSRF_REQUIRED=yes
CSRF_ACCEPTED=yes
```

前者来自缺少 `X-CSRF-Token` 的失败请求，后者来自携带正确 token 的成功请求。

## 第四层：logout 和 expiry 是服务端状态

只让浏览器删 Cookie 不够。服务端也要把 session 标记为 revoked，后续即便有人重放旧 Cookie，服务端仍然拒绝：

```python
context = authenticate(cookie)
context.session.revoked = True
return Set-Cookie: sid=; Max-Age=0
```

过期也要由服务端检查：

```python
if session.expires_at <= now():
    return 401, "expired_session"
```

所以实验有两条独立证据：

```text
LOGOUT_REVOKED=yes
EXPIRY_REJECTED=yes
```

`LOGOUT_REVOKED` 检查旧 session 被主动撤销；`EXPIRY_REJECTED` 检查时间推进后服务端拒绝已过期 session。二者解决的问题不同，实际系统都需要。

## 把输出报告读成证据链

`run_lab.sh` 运行后会生成本地 `reports/` 目录。公开仓库不提交这些运行产物，因为它们应该由你在自己的机器上重新生成。

```text
reports/session_auth_probe.json
reports/session_auth_report.md
reports/session_events.jsonl
reports/run_lab_output.txt
```

`session_auth_probe.json` 适合给脚本检查：

```json
{
  "admin_allowed": true,
  "cookie_httponly": true,
  "csrf_required": true,
  "forged_cookie_rejected": true,
  "login_status": 200,
  "password_stored_plaintext": false,
  "run_status": "ok"
}
```

`session_events.jsonl` 适合观察服务端状态变化。事件里记录注册、登录、拒绝、修改、撤销，不记录密码值。日志能帮助定位边界错误，但日志自身也要遵守敏感信息边界。

## 常见错误和定位方法

### 错误一：把用户信息直接放进 Cookie

如果业务代码读到 `Cookie: role=admin` 就授予管理员权限，权限边界已经交给客户端。正确模型是：Cookie 只提供 session id，服务端从自己的存储里查用户和角色。

定位方法：写一个伪造 Cookie 测试，例如 `sid=alice` 或 `role=admin`。如果服务端接受，说明身份边界错误。

### 错误二：只在前端做登录态判断

前端可以决定显示哪个按钮，不能作为服务器权限判断依据。所有敏感操作都要在服务端重新认证和授权。

定位方法：绕过 UI 直接构造请求。实验里的 `GET /admin/report` 用普通用户 Cookie 返回 403，就是服务端权限检查在工作。

### 错误三：退出登录只清浏览器 Cookie

清 Cookie 能改善用户体验，但服务端如果没有撤销 session，旧 Cookie 仍可能被重放。

定位方法：登录、保存旧 `Set-Cookie`，调用 logout，再用旧 Cookie 请求 `/me`。正确结果是 401。

### 错误四：把 CSRF 和登录状态混成一件事

Cookie 证明请求携带了某个登录态；CSRF token 证明状态修改请求还带了服务端发给本站页面的附加值。读取接口、幂等接口、状态修改接口的检查强度可以不同。

定位方法：对状态修改接口分别发三次请求：无 Cookie、有 Cookie 无 CSRF、有 Cookie 有 CSRF。三次结果应该能解释为 401、403、200 或类似分层。

## 练习

1. 给实验增加 `POST /password`：要求旧密码正确、CSRF token 正确，并在修改后撤销当前用户的所有旧 session。
2. 给 session 增加 `last_seen_at` 字段：每次认证成功时更新它，并在报告里输出最近活跃时间。
3. 把 `SameSite=Lax` 改成 `SameSite=Strict`，在文章里解释它对导航、表单和跨站跳转体验的影响。
4. 给管理员报表增加测试：普通用户即使伪造 `Cookie: sid=admin` 也必须失败。

## 小结

登录功能可以先按四层理解：password verifier、server-side session、CSRF token、authorization check。每一层都应该有一个可观察的失败样例和成功样例。这样写出来的认证边界才能被测试、被解释，也能在以后接入框架、数据库、反向代理和 OAuth/OIDC 时保持清晰。

## 参考资料

- [Python `hashlib.pbkdf2_hmac`](https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac)
- [Python `hmac.compare_digest`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest)
- [Python `secrets`](https://docs.python.org/3/library/secrets.html)
- [Python `http.cookies`](https://docs.python.org/3/library/http.cookies.html)
- [MDN：Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP Cross-Site Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [RFC 6265：HTTP State Management Mechanism](https://datatracker.ietf.org/doc/html/rfc6265)
