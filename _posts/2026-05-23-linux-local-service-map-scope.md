---
layout: post
title: "本地服务映射：写一个只扫描 loopback 的端口检查器"
date: 2026-05-23 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Python socket 写受限 loopback 端口映射器，并用 ss 交叉验证开放端口。"
tags: [linux, service-map, socket, authorized-security]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / local service map
> 本文只做本机 loopback 范围映射。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

服务映射的目标是知道自己机器上哪些端口在监听。为了保持授权边界，lab 的映射器只接受 `127.0.0.1`、`localhost` 或 `::1`，端口列表也有长度限制。它的定位是教学用的本地观察工具，范围固定在 loopback。

## 为什么需要一个小映射器

`ss` 已经能列出本机监听 socket，但它回答的是内核状态；客户端真正关心的是“从这个地址族连接该端口能否成功”。自己写一个三端口映射器，可以把地址解析、连接超时、结果分类和授权限制放进同一条可测试路径。

目标不是复制成熟扫描器。这个练习保留最小功能，让范围约束直接写进代码：host 只能来自三个 loopback 值，端口必须位于 1–65535，去重后最多 128 个。

## 学习目标

1. 理解端口映射和授权边界的关系。
2. 用 socket 连接结果判断端口开放状态。
3. 将映射结果与 `ss -ltn` 交叉验证。
4. 给安全工具加范围限制和输入校验。

## 先修知识

需要理解 TCP connect 到端口的基本过程。

## 核心模型

![本地服务映射范围](/assets/diagrams/linux-local-service-map-scope.svg)

输入范围先被校验，再逐个端口尝试 TCP connect。开放端口再探测 `/health`，从 `tcp-open` 细化为 `http-health`。

## 逐步实现

在 lab 根目录保持 18480 端口的教学服务运行，再执行：

```bash
PYTHONPATH=src python3 -m local_netsec_lab.cli map \
  --host 127.0.0.1 \
  --ports 18479-18481 \
  --output reports/service_map.json
```

本次结果：

```json
{
  "host": "127.0.0.1",
  "scope": "loopback-only",
  "open_ports": [18480]
}
```

端口 `18480` 是 lab 服务，前后相邻端口关闭。脚本还记录每个端口的 `latency_ms` 和 `service_hint`。

`latency_ms` 受调度和机器负载影响，不应写成固定验收值。稳定断言是端口集合与服务提示：18480 可建立 TCP 连接，并且 `/health` 返回 200，所以提示为 `http-health`。

## 连接探测怎样工作

核心路径使用 `socket.create_connection`：

```python
try:
    with socket.create_connection((host, port), timeout=0.25):
        is_open = True
except OSError:
    is_open = False
```

`create_connection` 会通过 `getaddrinfo` 获得可用地址族，因此 `127.0.0.1`、`localhost` 和 `::1` 不再被强制塞进 IPv4 socket。早期实现固定使用 `AF_INET`，却又声称接受 `::1`；新增 IPv6 loopback 回归测试后，这个接口与实现的不一致已经消除。

TCP 连接成功后，映射器再用 `HTTPConnection` 请求 `/health`：

```text
连接失败             -> open=false, service_hint=closed
TCP 成功、HTTP 未确认 -> open=true,  service_hint=tcp-open
HTTP /health 返回 200 -> open=true,  service_hint=http-health
```

当前范围固定在 loopback，邻近未监听端口通常立即得到 connection refused。对真实网络而言，超时、过滤和路由失败都可能表现为“未连接成功”，不能仅凭一次 false 断言远端没有服务。

## 为什么要限制范围

端口检查本身是中性技术，边界由目标、授权和速率决定。教学工具把 host 限制在 loopback，把端口数量限制在小范围内，可以让学习集中在 socket 语义和结果解释上。

## 与 ss 的关系

`ss -ltn` 从系统角度列出监听 socket；自写 mapper 从客户端角度尝试连接。两者能互相验证：如果 `ss` 显示监听，但 mapper 连接失败，可能是地址族、bind 地址或权限边界差异。

只查看目标端口可减少噪声：

```bash
ss -ltn 'sport = :18480'
```

在服务运行时应出现 `127.0.0.1:18480`。如果 mapper 报告开放而 `ss` 里没有该端口，还要确认命令是否在同一个 network namespace 中运行。

## 输入失败也要测试

范围限制只有在拒绝路径被执行过之后才算有证据。当前测试确认外部示例地址会被拒绝，混合端口表达式会排序和去重，IPv6 loopback 可以实际连接：

```text
test_non_loopback_rejected ... ok
test_parse_ports_limited_and_sorted ... ok
test_ipv6_loopback_probe_uses_address_family_resolution ... ok
```

## 常见错误

1. **把本地实验命令改到外部地址。** 学习目标会从排障变成未授权探测风险。
2. **扫描范围过大。** 初学阶段只需要少量端口来理解状态。
3. **只信一个工具。** `ss` 和客户端连接视角应一起看。
4. **忽略超时。** 没有 timeout 的网络代码容易卡住脚本。

## 练习或延伸

1. 把端口范围改成 `18480,18482`，观察 JSON 排序。
2. 尝试把 host 改成保留示例网段地址，确认工具拒绝。
3. 给 mapper 增加 `--timeout` 参数，并记录不同 timeout 的影响。

## 参考资料

- Python 文档：[socket](https://docs.python.org/3/library/socket.html)
- Python 文档：[`socket.create_connection`](https://docs.python.org/3/library/socket.html#socket.create_connection)
- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- Python 文档：[ipaddress](https://docs.python.org/3/library/ipaddress.html)


{% endraw %}
