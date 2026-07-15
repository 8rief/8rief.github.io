---
layout: post
title: "Secure Selective-Scan Bench：先用成本模型否掉过早的性能结论"
date: 2026-07-13 18:00:00 +0800
categories: research-notes
column: problem-exploration
column_title: "问题探究"
tags: [mamba, secure-inference, mpc, state-space-models]
---

> 代码状态：暂未公开。当前结果是操作数与依赖深度模型，没有接入 MPC/FHE backend，也没有模型准确率结论。

Mamba 一类 selective state-space model 依赖输入相关的状态更新。放进安全计算后，token-dependent transition 不能直接公开，而逐 token 递推又会形成很深的在线依赖链。

Secure Selective-Scan Bench 检查一个候选思路：把仿射状态更新写成可结合的 map，在公开 chunk 边界上组合私有 state capsule，能否用更多乘法换取更小的交互深度。

证据边界要写窄：本文只用一个可审查的成本模型回答前置问题——在不泄漏输入相关 transition 的条件下，scan scheduling 是否至少可能降低交互深度。高效安全推理和模型精度仍需要真实 backend 与任务实验。

## 结合律检查

对标量递推

\[
h_t = a_t h_{t-1} + b_t,
\]

把每一步写成仿射 map `(a_t, b_t)`。两个 map 的组合为

\[
(a_2,b_2)\circ(a_1,b_1)=(a_2a_1, a_2b_1+b_2).
\]

测试中的确定性样例比较串行递推与组合结果，最大绝对误差为 `8.882e-16`。这只验证代数恒等式和浮点 smoke，不等于安全协议正确性。

## 成本模型

```bash
cd projects/02-academic/frontier-crypto-timeseries/secure_selective_scan_bench
python3 selective_scan_bench.py examples/mamba_edge_timeseries.json \
  --output reports/mamba_edge_timeseries.md \
  --html-output reports/mamba_edge_timeseries.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

样例设定为长度 4096、状态维度 128、24 层。下面只摘取三种策略：

| 策略 | secret mults | round-depth proxy | latency proxy |
|---|---:|---:|---:|
| token-recurrent-private | 25,165,824 | 98,304 | 3,440,640 ms |
| full-affine-prefix-scan-private | 75,485,184 | 600 | 21,000 ms |
| chunked-capsule-private-c16 | 53,465,088 | 1,176 | 41,160 ms |

prefix scan 大幅降低依赖深度，同时把 secret multiplication 增加到约三倍。chunked capsule 位于两者之间。所有非泄漏方案都远高于样例的 2,500 ms 目标，因此当前结果不能支持“已经高效”。

表里的毫秒值来自每层交互 35 ms 的代理公式。它不是端到端测量，也没有包含具体 backend 的 batching、向量化、预处理和非线性近似成本。正式图表不能把这些数写成真实 latency。

## 两个容易越界的地方

第一，boundary-only capsule 只适用于周期性告警或状态交接。语言模型如果需要每个 token 的输出，语义已经不同，不能拿它直接比较。

第二，公开输入相关的 transition 参数虽然更便宜，却可能泄漏模型的选择性信号。它应保留为“不可接受的快速基线”，用于说明隐私约束带来的成本。

第三，结合律只覆盖仿射递推的组合，不覆盖激活函数、归一化、量化、溢出、截断误差或具体 MPC backend 的通信调度。若后续图表加入这些项，必须重新生成成本表。

## 当前结论与置信度

```text
conclusion=scan_scheduling_reduces_depth_but_not_enough_without_backend
confidence=medium_for_cost_model
open_item=real_mpc_or_fhe_backend_required
```

这个负结果的作用是提前收窄路线：若真实 backend 中非线性、比较、量化或通信栈占主导，selective scan 的 work-depth 变换就不构成独立贡献。

## 路线是否继续，取决于真实 backend

下一步要选择一个公开 MPC/FHE 框架，固定安全级别、硬件、模型和序列长度，实测离线/在线时间、通信、轮数、数值误差与任务准确率。同时必须审计 MPCMamba 等直接 prior。

若 selector nonlinearities 在真实后端中占据绝对主导，scan scheduling 就没有论文价值；若已有工作已经完成相同的 work-depth 和 lifecycle 分析，这个项目应改成复现与审计，而不是宣称新方案。

## 常见误判

第一类误判是把 latency proxy 当成实测延迟。这里的 35 ms 每层交互只是代理参数，不能替代真实网络、序列化、预处理和 batch 调度。

第二类误判是把公开 transition 当成可接受 baseline。公开 transition 的行可以保留在内部报告里，用来展示隐私约束的成本；正式对比时必须标注为泄漏 baseline，不能和安全候选混排。

第三类误判是只比较 round-depth。secure inference 的瓶颈可能来自乘法数、通信量、非线性、定点精度或模型精度下降；只看深度会掩盖不可用的方案。

## 可以怎样练习

把任一候选策略拆成下面几列：

```text
semantics=per_token_output/boundary_state_only
private_transition=yes/no
secret_mults=
round_depth=
communication_bytes=
numeric_error=
backend_measured=yes/no
```

只有 `semantics` 和 `private_transition` 同时对齐的行，才可以进入同一张正式 baseline 表。

## 参考入口

- [Mamba: Linear-Time Sequence Modeling with Selective State Spaces](https://arxiv.org/abs/2312.00752)
- [Mamba official repository](https://github.com/state-spaces/mamba)
- [Transformers are SSMs / Mamba-2](https://arxiv.org/abs/2405.21060)
- [Cheetah secure inference](https://www.usenix.org/conference/usenixsecurity22/presentation/huang-zhicong)
- [BumbleBee secure transformer inference](https://www.ndss-symposium.org/ndss-paper/bumblebee-secure-two-party-inference-framework-for-large-transformers/)
