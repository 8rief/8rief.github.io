---
layout: post
title: "结课项目：写一个本地 network observer，整理接口、路由和协议证据"
date: 2026-04-02 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 interface、route、resolver、TCP、UDP、HTTP、ss、curl 和 timing 汇总成一份可复跑网络观察报告。"
tags: [networking, linux, capstone, observability, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/network-foundations-nonsecurity/README.md`](/assets/labs/network-foundations-nonsecurity/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：非安全向计算机网络基础 / capstone / network observer
> 本文 lab 已验证：`Ran 5 tests`，并生成 `observations.json`、`network_report.md`、`curl_http.txt`、`ss_listen.txt` 等报告。

网络基础学到最后，要能把分散的命令和现象整理成证据包。这个结课项目写一个本地 network observer：读取 interface 和 route，观察 `localhost` resolver，启动本地 TCP/UDP/HTTP 服务，记录 curl 与 ss 输出，再把结果写成 Markdown 和 JSON。

## 学习目标

1. 把 interface、route、DNS、TCP、UDP 和 HTTP 的观测汇总到一份报告。
2. 用 unittest 固定解析逻辑和本地服务行为。
3. 保留 transcript，避免只凭屏幕输出判断。
4. 明确实验边界：服务只绑定 loopback，不扫描外部主机。

## 先修知识

建议读完本包前七篇。需要会运行 Bash、Python 和基础 Linux 网络命令。

## 核心模型

![Network observer 证据管线](/assets/diagrams/network-observer-service-map-capstone.svg)

Network observer 先采集 Linux 环境证据，再启动本地 TCP/UDP/HTTP demo，随后保存工具输出和结构化 JSON。Markdown 报告服务于人类复查，JSON 服务于脚本检查和后续自动化。

## 逐步实现

运行：

```bash
bash run_lab.sh
```

核心 transcript：

```text
interfaces=5 routes=4
localhost_dns_answers=3
tcp_echo=NETWORK-FOUNDATIONS tcp_bytes=1048576
udp_echo=UDP DATAGRAM
http_status=200 body_contains=True
Ran 5 tests
OK
```

生成的报告包括：

```text
reports/observations.json
reports/network_report.md
reports/ip_addr.txt
reports/ip_route.txt
reports/resolv_conf.txt
reports/curl_http.txt
reports/ss_listen.txt
```

这套产物覆盖三类证据：系统配置、协议行为、测试结果。因为 demo 都在 loopback 上运行，它适合教学和本地调试，不会把学习过程变成对外部网络的探测。

## 为什么要做 network observer

network observer 要解决的核心问题是“网络现象分散在太多命令里”。`ip addr`、`ip route`、`getent`、`ss`、`curl`、Python socket 输出各自有价值，但如果没有统一报告，学习者很难把它们串成一条证据链。

这个结课项目把观察分成三类：

```text
系统视图：interfaces、routes、resolver 配置
协议行为：TCP echo、UDP echo、HTTP response
复查证据：JSON、Markdown、curl/ss 原始输出、unittest transcript
```

它的目标是让本地网络机制能被反复复现；公网性能测量不属于这个实验边界。

## artifacts 怎么读

生成文件可以按用途分组：

| 文件 | 用途 | 读法 |
|---|---|---|
| `observations.json` | 结构化证据 | 给脚本或后续实验读取 |
| `network_report.md` | 人类复查报告 | 看摘要和解释是否一致 |
| `ip_addr.txt` | 接口原始输出 | 对照 interface 数量和地址 |
| `ip_route.txt` | 路由原始输出 | 对照 route 选择模型 |
| `curl_http.txt` | HTTP 原始响应 | 检查 status、headers、body |
| `ss_listen.txt` | 监听端口证据 | 检查服务绑定在本地 |

这组文件让报告中的结论可以回到原始观测，而不是只依赖一段摘要。

## observations.json 的结构

结构化输出可以抽象成：

```json
{
  "interfaces_observed": 5,
  "routes_observed": 4,
  "localhost_dns_answers": 3,
  "tcp": {"echo": "NETWORK-FOUNDATIONS", "bytes": 1048576},
  "udp": {"echo": "UDP DATAGRAM"},
  "http": {"status": 200, "body_contains": true}
}
```

字段名应该稳定，数值可以随环境变化。比如 interface 数量可能因为 WSL、容器、VPN 或虚拟网卡变化；HTTP status 和 body 断言则应该在本地服务逻辑不变时保持稳定。

## 输出怎么读

transcript 中的：

```text
Ran 5 tests
OK
```

说明 observer 的解析函数、route 选择模型和本地 TCP/UDP/HTTP 行为都有自动检查。报告里的 `Interpretation` 段说明实验只停留在 loopback，外部形状的地址只用于本地 route 计算，不发起外部探测。

## 扩展方向

完成基础 observer 后，可以安全扩展：

```text
增加 /health HTTP path，并在 curl_http.txt 中验证
把多次运行的 RTT 写入 CSV，观察本机波动
把 route 选择模型做成小 CLI：target IP -> iface/gateway
为 observations.json 加 schema_version，方便后续兼容
```

每个扩展都应继续保持本地边界和可复查证据。

## 常见错误

1. **只有命令，没有报告。** transcript 和结构化输出能让结果被复查。
2. **把公网可达性混进基础 lab。** 初学阶段优先固定本地变量。
3. **没有测试解析逻辑。** route 解析、最长前缀选择、TCP/UDP/HTTP 行为都应该有最小测试。
4. **过度解释一次性能数值。** loopback timing 只说明本机实验边界内的观察。

## 练习或延伸

1. 给 `observations.json` 增加一个 `timestamp` 字段，并解释可复现性影响。
2. 把 HTTP handler 增加 `/health` 和 `/metrics` 两个路径。
3. 把报告转成 CSV，比较多次运行的 TCP RTT 和吞吐波动。

## 参考资料

- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- curl 文档：[curl man page](https://curl.se/docs/manpage.html)
- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)

{% endraw %}
