---
layout: post
title: "路由表和最长前缀匹配：数据包下一跳怎么选"
date: 2026-06-30 03:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 /proc/net/route 和一个本地 route 选择模型解释 destination、gateway、interface 与 longest-prefix match。"
tags: [networking, routing, linux, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / routing table / longest-prefix match
> 本文 lab 已验证：本地 route 表有 4 条记录，`8.8.8.8` 只用于本地 route 选择计算，不发送外部数据包。

当应用连接一个 IP 地址时，内核需要回答：这个包从哪个 interface 发出？是否交给 gateway？路由表就是这个决策表。每条路由描述一个目标网络、前缀长度、下一跳 gateway 和出口 interface。若多条路由都匹配目标地址，选择前缀最长的一条。

## 学习目标

1. 读懂 route 表中的 destination、gateway、mask/prefix 和 interface。
2. 理解最长前缀匹配为什么能覆盖默认路由和更具体路由。
3. 用一个小模型复现 route 选择，不依赖外部网络连通性。
4. 区分“计算路由选择”和“真的发送数据包”。

## 先修知识

需要理解 IP 地址和 CIDR 前缀。建议先读上一篇 IP 地址和 CIDR。

## 核心模型

![路由选择的最长前缀匹配](/assets/diagrams/network-routing-table-longest-prefix.svg)

目标 IP 进入路由选择后，会和 route 表中每个网络前缀比较。默认路由 `0.0.0.0/0` 几乎匹配所有 IPv4 目标，但它的前缀长度最短。若存在更具体的 `/24`、`/16` 或 loopback 路由，内核会优先选择更具体的记录。

## 逐步实现

查看路由表：

```bash
ip route show
```

lab 还会读取 `/proc/net/route`，解析十六进制小端地址，并生成结构化字段。核心函数逻辑如下：

```python
def choose_route(routes, target_ip):
    target = ipaddress.IPv4Address(target_ip)
    candidates = []
    for row in routes:
        network = ipaddress.IPv4Network(row["cidr"], strict=False)
        if target in network:
            candidates.append(row)
    return sorted(candidates, key=lambda row: row["prefix"], reverse=True)[0]
```

报告摘要中记录：

```text
routes_observed: 4
example_route_iface: eth0
```

这里的 `example_route_iface` 来自本地 route 表计算。lab 没有向 `8.8.8.8` 发送探测包，只用这个地址测试默认路由会落到哪条记录上。

## 常见错误

1. **把 gateway 当最终目标。** gateway 是下一跳，最终目标仍然是原始目标 IP。
2. **忽略最长前缀。** 默认路由能兜底，但更具体路由优先。
3. **混淆路由选择和连通性。** 能选出路由不代表远端一定可达。
4. **手工解析 `/proc/net/route` 时忽略字节序。** Linux 文件里的 IPv4 十六进制值以小端形式显示。

## 练习或延伸

1. 运行 `ip route show`，找出默认路由。
2. 用 Python 写三条 route：`0.0.0.0/0`、`10.0.0.0/8`、`10.1.2.0/24`，测试 `10.1.2.3` 选中哪条。
3. 解释为什么 route 选择不能替代 `curl` 或 `ping` 的端到端可达性验证。

## 参考资料

- Linux man-pages：[ip-route(8)](https://man7.org/linux/man-pages/man8/ip-route.8.html)
- Linux man-pages：[proc_net(5)](https://man7.org/linux/man-pages/man5/proc_net.5.html)
- IETF RFC 1812：[Requirements for IP Version 4 Routers](https://www.rfc-editor.org/rfc/rfc1812)

{% endraw %}
