---
layout: post
title: "DPF/PIR 笔记：短查询 key 为什么不等于低成本更新"
date: 2026-07-11 09:00:00 +0800
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
- 如果数据库逻辑层采用 prefix、tree 或 histogram，append 会影响多少逻辑节点；
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

## 为什么这个问题不平凡

读协议里的短 key 和写协议里的低更新成本属于不同层次。短 key 约束的是请求表示；动态更新还要处理数据库同步、聚合状态、预处理材料和未使用 token 的有效性。把这几类成本混在一起，会把一个读侧优化误判成完整动态系统优化。

## 证据路径

本文的证据来自三类材料：公开 DPF/PIR 实现的接口形状、Mode one-hot append 的预实验数字，以及 share/view 语义检查。最小证据表可以写成：

```text
read_key_size=O(lambda * log N)
server_eval_shape=full_domain_or_equivalent
append_payload_dense=O(K)
append_dpf_payload=O(lambda * log K)
rss_dropin_secure=false
```

## 当前结论与置信度

```text
conclusion=short_query_key_does_not_imply_low_update_cost
confidence=high_for_model_boundary
remaining_risk=needs_protocol_specific_write_view_proof
```

这个结论只排除“短查询 key 自动推出低更新成本”的跳跃。它不排除某些特定系统通过额外写协议、批处理或预处理设计降低更新成本。

## 下一步验证

下一步应该分开画两张图：读协议的 key/eval/response 流程，写协议的 append/update/hint-maintenance 流程。只有当两张图的 server view、同步边界和材料生命周期都成立时，才能把某个 DPF 写入方案当成完整候选。

## 常见误判

第一类误判是只看 client request 大小。DPF key 短，说明一次读取请求可以被紧凑表示；server 端是否需要 full-domain evaluation、是否需要扫描数据库、是否需要维护 hint，是另一组成本。

第二类误判是把 one-hot append 当成动态数据库更新。one-hot payload 被压缩，只说明某个逻辑增量可以被压缩；动态系统还要说明两台或多台服务器如何同步、未使用查询材料是否仍有效、历史状态是否可链接。

第三类误判是把两服务器 additive DPF 原型直接塞进三服务器 replicated sharing。drop-in 替换至少要检查每个参与方看到的 component view，不能只检查重构后的数值正确。

## 可以怎样练习

用一张小表把一个候选方案拆开：

```text
read_request_bytes=
server_eval_shape=
write_payload_bytes=
state_sync_messages=
hint_or_preprocessing_lifetime=
security_view_checked=yes/no
```

如果某一行写不出来，就不要把它并入总成本结论。进一步的练习是选一个很小的 histogram，例如 `K=8`，分别写出 dense append、DPF append 和 server-side share view；这个练习只用于发现哪些成本没有被短 key 覆盖；它不提供安全证明。
