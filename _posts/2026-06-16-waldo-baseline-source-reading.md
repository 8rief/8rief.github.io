---
layout: post
title: "Waldo 源码笔记：实验 baseline 的协议边界如何确定"
date: 2026-06-16 10:00:00 +0800
categories: secure-query
tags: [waldo, fss, benchmark, source-reading]
---

安全查询系统的实验比较中，baseline 首先是一个协议对象，而不是一行复杂度公式。通信边界、状态组织、查询形状和序列化边界如果没有对齐，最终数字很容易失去解释力。Waldo 是一个典型例子：论文和仓库说明它面向隐私保护时间序列数据库，使用 Function Secret Sharing 支持查询；仓库 README 同时明确标注该实现是 academic proof-of-concept，不是生产系统。这个定位决定了读源码时既要尊重其协议语义，也要审慎处理工程外壳。

## 背景：baseline 为什么不能只看公式

Waldo 的抽象目标不是“生成一份 FSS key”这么单薄，而是把时间序列数据组织成可查询的聚合结构，再通过 FSS/DCF 类查询隐藏访问模式。实验比较时至少有三层边界需要拆开：

```text
区间查询语义
  -> 聚合树或过滤结构
  -> FSS/DCF key、server eval、response reconstruction
```

如果只记录论文中的渐近复杂度，会遗漏几个直接影响实验数字的问题：

- query 发送的是单个点函数 key，还是左右边界的区间/DCF key；
- 每台服务器返回的是一个聚合值，还是每层一组候选节点值；
- append 是单轮写入，还是先读路径再写回路径；
- 测量包含 gRPC/protobuf，还是只统计协议 payload；
- baseline 的核心协议是否被保留，还是被测量 wrapper 改变了语义。

这些边界不固定，通信量和时延就不能直接解释。

## 源码中的 WaldoTree 查询边界

在 Waldo 源码中，`AggTreeIndexClient` 同时承担聚合树 key 生成和 append 路径更新相关的 client 逻辑。几个函数能清楚看出协议形状：

- `secure-indices/core/AggTree.cpp` 中的 `gen_agg_tree_keys` 为左右边界分别生成 DCF key；
- `serialize_keys` 把 LT 和 GT 两类 key 拼接后发给服务器；
- `client/core/client.cpp` 中的 `AggTreeQuery` 对三台服务器分别构造 pairwise key；
- server response 不是单个值，而是按深度返回 `retShares` 和 `retShares_r`，client 再逐层重构。

因此，WaldoTree 的查询通信和树深度相关是协议形状决定的，而不是某个实现常数导致的偶然现象。源码中的三服务器 pairwise key 分发逻辑也说明：比较 Waldo 时不能把它退化成两服务器 DPF 查询，否则模型已经变了。

## 源码中的 append 边界

append 更容易被误读。`client/core/client.cpp` 的 `AggTreeAppend` 分成两个阶段：

1. client 向三台服务器发送 `SendATAppend1`，取回 append path 上的 parent shares；
2. client 重构 parent path，调用 `propagateNewVal` 计算新聚合值，再拆分成 shares；
3. client 通过 `SendATAppend2` 把新路径 shares 发回服务器。

`AggTreeIndexServer::getAppendPath` 和 `finishAppend` 也对应这个流程：先定位下一次 append 的父路径，再在第二阶段完成写入。也就是说，Max/聚合树类 append 的通信与路径长度有关；如果某个实验把 append 简化成一次单值写入，就已经不是同一个 baseline 语义。

## 实测数字如何解释

在统一 raw-TCP payload 口径下，depth 22 的 WaldoTree 结果显示：

| comparison | phase | mean total bytes | mean latency |
|---|---:|---:|---:|
| Waldo Sum128 | query | 10.778 KiB | 1248.93 ms |
| Waldo Sum128 | append | 0.170 KiB | 80.83 ms |
| Waldo Max64 | query | 10.263 KiB | 1275.72 ms |
| Waldo Max64 | append | 1.676 KiB | 161.65 ms |

这些数字的重点不是“Waldo 慢”这个简单结论，而是协议边界解释：Sum append 可以是一轮较小数据更新；Max append 需要路径相关的两阶段更新；query 需要按树深度携带和返回相关材料。实验比较只有在这些边界保持一致时才有意义。

## 结论

- baseline 是协议实现，不是复杂度公式。
- WaldoTree query 的 key 和 response 结构由左右边界 DCF 与树深度共同决定。
- WaldoTree append 对聚合路径敏感，不能与单 slot append 混为一谈。
- 公平比较应先固定三件事：协议语义、通信统计边界、online/offline 分界。

## 参考

- Waldo paper: <https://eprint.iacr.org/2021/1661>
- Waldo GitHub repository: <https://github.com/ucbrise/waldo>
- Waldo local source anchors checked: `secure-indices/core/AggTree.{h,cpp}`, `client/core/client.cpp`
