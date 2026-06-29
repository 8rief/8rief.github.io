---
layout: post
title: "结课项目：写一个本地 network observer，整理接口、路由和协议证据"
date: 2026-06-30 03:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 interface、route、resolver、TCP、UDP、HTTP、ss、curl 和 timing 汇总成一份可复跑网络观察报告。"
tags: [networking, linux, capstone, observability, teaching]
---
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
interfaces=6 routes=4
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
