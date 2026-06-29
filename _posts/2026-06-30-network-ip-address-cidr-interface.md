---
layout: post
title: "IP 地址和 CIDR：先判断一个目标在哪个网络里"
date: 2026-06-30 03:01:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 interface address、prefix length、loopback 和本地网段解释为什么路由判断离不开 CIDR。"
tags: [networking, ip-address, cidr, linux, teaching]
---
{% raw %}
> 主题：非安全向计算机网络基础 / IP address / CIDR
> 本文 lab 已验证：报告记录了 interface 列表，并用本地 route 表选择目标地址应走的 route。

网络程序常见需求是判断“这个目标是不是本地网络内”。答案不能只看 IP 字符串的前几位，要看地址和前缀长度组成的网络范围。CIDR 写法如 `192.168.1.0/24`，含义是前 24 位是网络前缀，剩下的位用于主机地址。

## 学习目标

1. 理解 IP 地址、prefix length 和网络范围之间的关系。
2. 区分 loopback 地址、接口地址和目标地址。
3. 能用 CIDR 判断一个目标是否属于某个网络。
4. 知道为什么路由表必须依赖前缀而不是字符串匹配。

## 先修知识

需要知道 IPv4 地址由 32 位组成，常写成点分十进制，例如 `127.0.0.1`。本文只用 IPv4 建立基本模型；IPv6 的地址长度和记法不同，但前缀思想一致。

## 核心模型

![IP 地址、前缀和接口](/assets/diagrams/network-ip-address-cidr-interface.svg)

interface 上配置的是地址加前缀。地址说明本机在该网络中的端点，前缀说明网络范围。目标地址进入路由判断时，内核会检查它落入哪些前缀，再决定下一跳和发送 interface。

## 逐步实现

查看本机地址：

```bash
ip addr show
```

lab 同时读取 `/proc/net/dev`，把 interface 的收发字节和包数写入报告。示例摘要：

```text
interfaces=6
routes=4
```

用 Python 标准库可以直接表达 CIDR 判断：

```python
import ipaddress
network = ipaddress.IPv4Network("127.0.0.0/8")
print(ipaddress.IPv4Address("127.0.0.1") in network)
```

这段代码输出 `True`。它说明 `127.0.0.1` 属于 `127.0.0.0/8`，因此会落在 loopback 相关路径上。真实系统中，`ip addr` 展示接口配置，`ip route` 展示路由选择规则，两者共同决定数据如何离开应用。

## 常见错误

1. **只背私有地址段。** 更关键的是会用前缀判断范围。
2. **把 `/24` 理解成端口或主机数。** `/24` 是网络前缀长度，不是端口，也不是直接写出的主机数量。
3. **忽略 loopback。** `127.0.0.1` 指向本机，适合开发和测试本地服务。
4. **用字符串前缀判断 IP。** `10.1.2.3` 是否属于某个网络，应交给二进制前缀判断。

## 练习或延伸

1. 用 `python3 -q` 试验 `ipaddress.IPv4Network("10.0.0.0/8")` 是否包含 `10.2.3.4`。
2. 找到 `ip addr show` 中一个非 loopback 地址，写出它的前缀长度。
3. 比较 `/16` 和 `/24` 的网络范围大小，并解释哪一个更具体。

## 参考资料

- Python 文档：[ipaddress](https://docs.python.org/3/library/ipaddress.html)
- Linux man-pages：[ip-address(8)](https://man7.org/linux/man-pages/man8/ip-address.8.html)
- IETF RFC 4632：[Classless Inter-domain Routing](https://www.rfc-editor.org/rfc/rfc4632)

{% endraw %}
