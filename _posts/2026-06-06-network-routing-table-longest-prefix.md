---
layout: post
title: "路由表和最长前缀匹配：数据包下一跳怎么选"
date: 2026-06-06 18:00:00 +0800
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

## 为什么要引入最长前缀匹配

最长前缀匹配要解决的核心问题是“默认规则和特殊规则同时存在”。系统通常有一条默认路由 `0.0.0.0/0`，又有 loopback、本地网段、容器网段等更具体路由。若只取第一条匹配记录，路由结果会依赖表顺序；按最长前缀选择，含义更稳定：越具体的网络范围越优先。

可以把 route 表理解成从宽到窄的规则集合：

```text
0.0.0.0/0       覆盖所有 IPv4，最宽
10.0.0.0/8      覆盖 10.*，更具体
10.1.2.0/24     覆盖 10.1.2.*，最具体
```

目标 `10.1.2.3` 同时匹配三条，最终选择 `/24`。

## 可复现的小模型

下面的纯 Python 模型不发送任何网络包，只复现选择规则：

```python
import ipaddress
routes = [
    {"cidr": "0.0.0.0/0", "iface": "eth0"},
    {"cidr": "10.0.0.0/8", "iface": "vpn0"},
    {"cidr": "10.1.2.0/24", "iface": "lab0"},
]
target = ipaddress.IPv4Address("10.1.2.3")
matched = [r for r in routes if target in ipaddress.IPv4Network(r["cidr"])]
print(max(matched, key=lambda r: ipaddress.IPv4Network(r["cidr"]).prefixlen))
```

预期输出：

```text
{'cidr': '10.1.2.0/24', 'iface': 'lab0'}
```

这个输出说明：默认路由确实匹配，但更具体的 `/24` 会胜出。

## 读 route 表时看哪些字段

`ip route show` 常见输出形状如下：

```text
default via 172.20.0.1 dev eth0
172.20.0.0/20 dev eth0 proto kernel scope link src 172.20.5.10
127.0.0.0/8 dev lo scope host
```

读法是：destination 前缀决定匹配范围；`via` 表示下一跳 gateway；`dev` 表示出口 interface；`src` 是本机可能使用的源地址。没有 `via` 的直连路由通常表示目标网络直接在该 interface 上。

## 状态变化和边界

route 选择只完成“下一跳怎么选”这个决策：

```text
target_ip -> candidate routes -> longest prefix -> iface/gateway
```

它不证明远端主机在线，不证明防火墙允许，不证明 HTTP 服务正常。后续还需要 TCP、TLS、HTTP 或应用层检查。

## 输出怎么读

lab 中 `8.8.8.8` 只作为目标地址参与本地 route 计算。报告里的 `example_route_iface: eth0` 表示本机路由表会把该目标交给 `eth0` 相关记录；这不是对外部地址的连通性测试。

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
