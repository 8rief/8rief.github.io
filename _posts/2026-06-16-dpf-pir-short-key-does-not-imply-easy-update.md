---
layout: post
title: "DPF/PIR 笔记：短查询 key 为什么不等于低成本更新"
date: 2026-06-16 10:10:00 +0800
categories: secure-query
column: problem-exploration
column_title: "问题探究"
tags: [dpf, pir, update, source-reading]
---

DPF 能把一次私密读取压缩成短 key，但动态数据库还包含写入、hint 维护、聚合状态变化和未来查询材料失效等问题。因此，短查询 key 与低成本 append/update 之间没有直接等价关系。

## 背景：DPF-PIR 解决的是读位置隐藏

`dpf-cpp` 的 README 把系统定位得很清楚：这是一个基于 Distributed Point Functions 的高性能 PIR 实现，需要两个 non-colluding servers 持有 identical databases。这个模型适合解释 DPF-PIR 的核心读流程：

```text
client 生成两份 DPF key
server0、server1 分别在相同数据库上 eval
client 合并两个 response 得到目标记录
```

在源码中，`dpf.h` 暴露的接口也很直接：`Gen(alpha, logn)` 生成两份 key，`Eval` 评估单点，`EvalFull` 或 `EvalFull8` 展开完整选择向量。`main.cpp` 的 microbenchmark 对 `2^N` 条 dummy hash 记录建库，然后统计 `DPF.Gen`、`DPF.Eval` 和 inner product 时间。它还打印 `NN*32 bytes total transfer`，这反映了 DPF key 随深度线性增长的典型直觉。

## 定义：短 key 只约束 query request

DPF 的短 key 主要约束的是一次 query request 的表示长度。它没有自动回答以下问题：

- 数据库 append 后，两台服务器的 identical database 如何同步；
- 如果系统存在 query hint，hint 是否要重建；
- 如果数据库不是原始数组，而是 prefix、tree 或 histogram，append 会影响多少逻辑节点；
- 如果预处理材料绑定了旧数据库状态，未使用 token 是否需要被修正。

因此，DPF key size 是读协议的一部分，不是动态数据库总成本的上界。

## 源码细节：full eval 暗示 server 端仍要做工作

`dpf-cpp` 中 `EvalFull` 和 `EvalFull8` 会从短 key 展开完整选择向量。`hashdatastore` 再对选择向量和数据库做 inner product 风格的响应计算。这个结构说明了一个常见误解：短 key 不等于 server 只访问一个位置；PIR 的隐私通常要求 server 端按固定形状计算，常见实现会扫描或等价评估整个域。

这对动态聚合尤其重要。如果数据库逻辑层是 histogram prefix，那么 append 写入的不是一个普通 bit，而可能是一个长为 `K` 的 one-hot 增量；如果逻辑层是 max tree，那么 append 可能影响一条树路径。DPF 可以压缩“选择哪个位置”，但不能凭空消除“写入什么结构”的成本。

## 一个 mode append 预实验

在 Mode histogram append 上，曾用 Google DPF 风格的 `uint32` additive point function 做过预实验。目标是把 dense one-hot update 从 `O(K)` payload 压缩为 DPF key。结果显示：

| K | dense append bytes | DPF append bytes | compression |
|---:|---:|---:|---:|
| 32 | 310 | 343 | 0.90x |
| 64 | 566 | 398 | 1.42x |
| 512 | 4150 | 558 | 7.44x |
| 32768 | 262198 | 884.5 | 296.44x |

这个结果说明两点。第一，当 `K` 足够大时，point-function key 确实可能压缩 one-hot 写入。第二，该原型仍标注为 `rss_dropin_secure=false`，因为两份 additive DPF key 不自动满足三服务器 replicated RSS 的 component-view 约束。通信压缩成立，不代表可以直接替换现有存储模型。

## 结论

- DPF/PIR 的短 key 优化的是 query 表示，不自动优化 append。
- 动态数据库还要单独分析状态同步、hint 维护和聚合结构更新。
- DPF one-hot append 在大 `K` 下有通信压缩潜力，但需要重新设计 server view 和 share 语义。
- 读协议和写协议必须分开建模；把二者合并成“PIR 很短所以更新也短”是不成立的。

## 参考

- `dpf-cpp` repository: <https://github.com/dkales/dpf-cpp>
- Revisiting User Privacy for Certificate Transparency: <http://www.ramacher.at/_static/papers/ct-privacy.pdf>
- Google Distributed Point Functions repository: <https://github.com/google/distributed_point_functions>
- Source anchors checked: `dpf.h`, `dpf.cpp`, `main.cpp`, `hashdatastore.cpp`
