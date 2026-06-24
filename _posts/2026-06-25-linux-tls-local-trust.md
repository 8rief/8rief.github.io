---
layout: post
title: "TLS 本地信任链：自签名 CA、服务端证书和 curl 验证"
date: 2026-06-25 04:50:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 OpenSSL 生成本地 CA 和 localhost 服务端证书，比较 curl 默认验证失败、--cacert 成功与 -k 跳过验证。"
tags: [linux, tls, openssl, curl, defensive-security]
---
{% raw %}

> 主题：Linux 网络基础 / TLS / 证书验证 / 本地信任链  
> 本文命令已在 Ubuntu 24.04、Python 3.12.3、OpenSSL 3.0.13、curl 8.5.0 环境下本地执行验证。实验只启动 `127.0.0.1` 上的 HTTPS 服务，证书有效期为 1 天，只用于本地教学。

HTTP 讲清楚以后，下一层常见困惑是 HTTPS：为什么浏览器或 curl 会说证书不可信？`-k` 为什么能“解决”问题，却又不应该作为真正的修复？证书里的域名、签发者和本机信任库到底分别起什么作用？

这一讲构造一个最小本地信任链：先生成一个本地 CA，再用它签发 `localhost` 服务端证书，最后用 Python 启动 HTTPS 服务。我们对比三种访问方式：默认 curl 失败、显式信任本地 CA 后成功、用 `-k` 跳过验证也成功但失去身份校验。

## 安全边界

本文不访问公网 HTTPS 站点，不导入系统级根证书，不修改浏览器或操作系统信任库。所有证书、私钥和服务都只在本地实验目录内生成和使用。`curl -k` 只作为反例展示，不作为上线或日常排障的推荐修复。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 区分加密通道、服务端身份和本地信任锚。
2. 用 OpenSSL 生成本地 CA 和带 SAN 的服务端证书。
3. 解释为什么未信任 CA 时 curl 返回证书错误。
4. 用 `--cacert` 对单次请求显式指定信任锚。
5. 说明 `-k/--insecure` 牺牲了哪一类安全属性。

## 核心模型

TLS 同时承担两件事：把流量放进加密通道，并让客户端验证自己连接的是预期服务。

![TLS 本地信任链](/assets/diagrams/linux-tls-local-trust.svg)

最小链条有三个对象：

- **本地 CA**：实验中自己生成的根证书，客户端只有显式信任它，才会接受它签出的服务端证书。
- **服务端证书**：包含 `CN=localhost` 和 `subjectAltName = DNS:localhost, IP:127.0.0.1`，证明这个服务端证书适用于本地名字。
- **客户端验证**：curl 检查证书链、域名匹配、有效期和签名。链条不可信时，即使网络连接和加密握手的部分步骤能进行，也不能把服务身份当成可信。

## 生成本地 CA 和服务端证书

先写服务端证书配置，关键是 SAN：

```ini
[req]
distinguished_name = dn
req_extensions = v3_req
prompt = no
[dn]
CN = localhost
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
```

然后生成 CA 和服务端证书：

```bash
openssl genrsa -out certs/ca.key 2048
openssl req -x509 -new -nodes -key certs/ca.key -sha256 -days 1 \
  -subj /CN=Local-Teaching-CA -out certs/ca.crt
openssl genrsa -out certs/server.key 2048
openssl req -new -key certs/server.key -out certs/server.csr -config certs/server.cnf
openssl x509 -req -in certs/server.csr -CA certs/ca.crt -CAkey certs/ca.key \
  -CAcreateserial -out certs/server.crt -days 1 -sha256 \
  -extfile certs/server.cnf -extensions v3_req
```

查看证书关键信息：

```bash
openssl x509 -in certs/server.crt -noout -subject -issuer -ext subjectAltName
```

输出：

```text
subject=CN = localhost
issuer=CN = Local-Teaching-CA
X509v3 Subject Alternative Name:
    DNS:localhost, IP Address:127.0.0.1
```

`subject` 说明服务端证书写给 `localhost`，`issuer` 说明它由本地 CA 签发，SAN 说明这个证书可用于 `localhost` 和 `127.0.0.1`。现代客户端主要依赖 SAN 判断名称匹配，CN 不能替代 SAN。

## 启动本地 HTTPS 服务

服务端使用 Python 标准库，把普通 HTTPServer 的 socket 包进 TLS：

```python
ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain('certs/server.crt', 'certs/server.key')
httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
httpd.serve_forever()
```

启动后访问 `https://localhost:18184/without-ca`。默认 curl 不知道我们的本地 CA，所以失败：

```bash
curl --noproxy '*' --connect-timeout 3 -sS https://localhost:18184/without-ca
```

输出节选：

```text
curl: (60) SSL certificate problem: unable to get local issuer certificate
exit status: 60
```

这个失败是正确行为。服务端证书虽然由某个 CA 签发，但这个 CA 不在 curl 当前信任集合里，所以身份不能被验证。

## 用 --cacert 显式信任本地 CA

对单次请求指定 CA 文件：

```bash
curl --noproxy '*' --cacert certs/ca.crt -sS https://localhost:18184/with-local-ca
```

输出：

```text
tls lab response
path=/with-local-ca
client=127.0.0.1:44906
cipher=TLS_AES_256_GCM_SHA384
```

这次成功的原因是客户端获得了验证所需的信任锚。curl 可以沿着 `server.crt -> ca.crt` 验证签名，并确认请求名 `localhost` 在 SAN 中。

再用 OpenSSL 客户端检查验证结果：

```bash
openssl s_client -connect localhost:18184 -servername localhost \
  -CAfile certs/ca.crt -verify_return_error </dev/null 2>/dev/null \
  | grep -E 'subject=|issuer=|Verify return code'
```

输出：

```text
subject=CN = localhost
issuer=CN = Local-Teaching-CA
Verify return code: 0 (ok)
```

`Verify return code: 0 (ok)` 是证书链验证成功的直接证据。

## 为什么 -k 不是修复

执行：

```bash
curl --noproxy '*' -k -sS https://localhost:18184/skip-verify
```

输出也会成功：

```text
tls lab response
path=/skip-verify
client=127.0.0.1:44922
cipher=TLS_AES_256_GCM_SHA384
```

但这种成功的含义不同。`-k` 让 curl 跳过证书校验，客户端不再确认服务端身份。通道仍然可能使用 TLS 加密，但“我连接的是不是预期服务”这个问题被放弃了。实验和临时定位可以用它验证是否是证书链问题；真正修复应当是配置正确证书、域名、信任链和时间。

## 服务端日志如何读

日志节选：

```text
path='/with-local-ca' peer=127.0.0.1:44906 cipher=('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
path='/skip-verify' peer=127.0.0.1:44922 cipher=('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
```

默认验证失败的请求没有进入应用层日志，因为客户端在证书校验失败后没有发送 HTTP 请求。后两次都完成了 TLS 握手并进入 HTTP 处理流程。服务端日志只能说明请求到达应用层，不能证明客户端是否验证了服务端身份；客户端侧的 curl 或 OpenSSL 输出才是验证证据。

## 常见错误

**只有加密，没有身份。** TLS 的安全目标不仅是加密字节流，还包括验证对端身份。跳过证书校验会削弱这个目标。

**证书域名不匹配。** 用 `https://127.0.0.1` 访问时，证书需要包含 IP SAN；用 `https://localhost` 访问时，证书需要包含 DNS SAN。

**把本地 CA 私钥当成普通文件传播。** CA 私钥可以签发证书，实验结束后应清理；真实环境要有严格的密钥保护和签发流程。

**把 -k 写进脚本长期使用。** `-k` 可以帮助定位问题，但不能作为生产脚本、监控脚本或正式接口调用的默认参数。

## 练习

1. 删除配置里的 `IP.1 = 127.0.0.1`，重新签发证书，再用 `https://127.0.0.1:18184/` 访问，观察域名/IP 匹配错误。
2. 把 `--cacert certs/ca.crt` 换成错误 CA 文件，观察 curl 的错误码。
3. 用 `openssl x509 -in certs/ca.crt -noout -dates` 查看证书有效期。
4. 在服务端日志中记录 `self.headers`，确认 HTTPS 建立后应用看到的仍然是普通 HTTP 请求头。

## 参考资料

- [RFC 8446: The Transport Layer Security Protocol Version 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- [OpenSSL req manual](https://docs.openssl.org/3.0/man1/openssl-req/)
- [OpenSSL x509 manual](https://docs.openssl.org/3.0/man1/openssl-x509/)
- [curl man page](https://curl.se/docs/manpage.html)
- [Python ssl documentation](https://docs.python.org/3/library/ssl.html)
{% endraw %}
