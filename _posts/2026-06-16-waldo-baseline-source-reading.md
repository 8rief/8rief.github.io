---
layout: post
title: "读 Waldo 源码学到的第一件事：baseline 不是一行复杂度公式"
date: 2026-06-16 10:00:00 +0800
categories: secure-query
tags: [waldo, fss, benchmark, source-reading]
---

这篇只讨论一个问题：**为什么做安全查询系统时，不能把 baseline 简化成论文里的一行复杂度公式。**

我最近读 Waldo 的源码和 README，最直观的感受是：一个认真 baseline 不是“通信量多少、复杂度多少”这么简单，而是一个有完整系统语义的实现。Waldo 的 README 说它是一个 private time-series database from Function Secret Sharing，同时也明确提醒这是 academic proof-of-concept prototype，不适合生产使用。这两个信息放在一起看很重要：它既是值得认真参考的系统 baseline，又不能被当成工程完备的生产组件。

## baseline 的语义比数字更重要

Waldo 不是一个孤立的 FSS key generator。它把时间序列聚合组织成树结构，然后用 FSS/DCF 风格的查询去选择树节点。也就是说，读 Waldo 时至少要同时理解三层东西：

```text
时间序列区间查询
        ↓
聚合树 / cover nodes
        ↓
FSS/DCF 查询与服务器响应
```

如果只看 FSS key size，很容易漏掉系统层面的边界。例如：

- 查询是不是固定形状？
- 一次查询覆盖多少树节点？
- 每台服务器返回的是节点值还是聚合值？
- append 是否走同一套路径？
- 代码里的网络序列化算不算协议开销？
- setup 阶段和 online 阶段如何分界？

这些问题不解决，实验结果就很容易失真。

## 读源码时我最关注的不是函数名

读 Waldo 这种系统时，我觉得最重要的不是逐个解释函数，而是抓住它的协议边界。

我会先问：

```text
client 在线发送什么？
server 根据什么状态计算？
server 返回什么？
client 如何恢复答案？
append 是否真的改变了 server state？
```

这比一开始钻进某个 C++ 类更有效。因为安全查询系统的性能往往不是某个函数决定的，而是由一整条路径决定的：key generation、query packing、server eval、response reconstruction、network framing、state update。

## baseline 改写时最容易犯的错

如果为了测量方便改写 baseline，有两个相反的风险。

第一个风险是把 baseline 改得不像 baseline。比如把原方案里必须做的工作删掉，或者改变服务器返回语义。这样测出来再快也没意义。

第二个风险是把工程实现的额外开销误当成协议本身。比如一个方案用 protobuf/gRPC，另一个方案用 raw TCP，如果直接比较端到端字节数，就可能比较的是框架开销，而不是协议开销。

所以我现在更倾向于把问题拆开：

```text
协议 payload 是多少？
raw TCP frame 后是多少？
完整系统实现端到端是多少？
```

这三个都可以有价值，但不能混着讲。

## 这件事对我的启发

Waldo 给我的最大启发不是“某个数值是多少”，而是：**baseline 是一个系统对象，不是一个公式对象。**

以后读安全查询论文或代码时，我会优先画出这张表：

| 问题 | 要确认的内容 |
|---|---|
| 查询输入 | client 在线到底发什么 |
| 服务端状态 | server 存的是明文、share、hint 还是树节点 |
| 返回值 | response 是节点列表、聚合 share 还是最终 share |
| 动态更新 | append/update 是否真正持久化 |
| 离线边界 | setup、preprocessing、online 是否分清 |
| 通信口径 | payload、framing、序列化是否分列 |

这张表比单独记住某个复杂度更有用。

## 参考源码

- Waldo: <https://github.com/ucbrise/waldo>
