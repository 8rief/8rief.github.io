---
layout: post
title: "三阶 selector 笔记：continuation wire 为什么是核心难点"
date: 2026-07-11 18:00:00 +0800
categories: secure-query
column: problem-exploration
column_title: "问题探究"
tags: [pcg, aby2, tensor, failed-attempt]
---

三阶 selector 的难点在于中间乘积能否继续作为 wire 参与后续 gate；简单多做一次明文乘法不能说明 share 形态成立。若第一层乘法只给出最终 additive share，它可以用于本次重构，却不一定能作为第二层乘法的输入。

## 背景：三阶 selector 的自然分解

三维 selector 中经常出现如下项：

\[
\rho_x[i]\wedge \rho_y[j]\wedge \rho_z[k].
\]

最自然的分解是两层乘法：

\[
\rho_{xy}[i,j]=\rho_x[i]\wedge\rho_y[j],
\]

\[
\rho_{xyz}[i,j,k]=\rho_{xy}[i,j]\wedge\rho_z[k].
\]

从明文代数看，这只是多乘一次。但在 secret sharing、ABY2.0 或 PCG 语境下，第一层输出的“形式”比数值更重要。

## final share 和 continuation wire 的区别

若一个乘法 gate 只输出 additive response share，那么三方相加可以得到乘积。这适合最终响应：

\[
z_0+z_1+z_2=xy.
\]

但下一层乘法通常要求输入仍是某种可继续计算的 share/wire 表示，例如每个参与方持有约定形式的相邻 share 或 masked wire。此时只知道一个 additive share 不够，因为 gate 需要的不只是“最终能重构的值”，还包括后续本地乘法公式所需的 share 结构。

因此，三阶 selector 需要的是：

```text
rho_x, rho_y  ->  mul gate  ->  rho_xy as continuation wire
rho_xy, rho_z ->  mul gate  ->  rho_xyz as output wire/share
```

这就是 continuation wire 问题。

## ABY2.0/BEAVY 带来的启发

ABY2.0 的核心改进之一是围绕 online 阶段效率重新组织 sharing、masked value 和 multiplication protocol。MOTION2NX 的 README 也说明它实现了 Arithmetic/Boolean variants of ABY2.0 的 secret-sharing-based protocols，并提供多种协议转换。这个系统视角提示了一个边界：乘法预处理不能只看单个乘积，还要看乘积是否要继续进入后续电路。

换到三阶 selector 上，PCG 需要 seed 化的是固定电路中的 gate material，而非孤立的 \(xy\)：第一层 gate 的输出必须能被第二层 gate 消费。若现有 PCG 只提供普通 OLE 或逐点乘法相关性，而没有 linked continuation-wire API，就还不是完整解决方案。

## 在线通信计算中的一个典型错误

三维 selector 的正确 online masked input 应该是三个轴向量：

\[
\Delta_x=e_x\oplus\delta_x,
\quad
\Delta_y=e_y\oplus\delta_y,
\quad
\Delta_z=e_z\oplus\delta_z.
\]

服务器使用预处理/PCG 材料组合出三输入 selector share。错误做法是把中间 \(xy\) 平面 materialize 后让 client 发送 \(\Delta_{xy}\) 和 \(\Delta_z\)。如果三维 layout 平衡，边长为 \(m\)，两种请求规模分别是：

\[
3m \text{ bits}
\]

和

\[
m^2+m \text{ bits}.
\]

当 \(N=2^{22}\) 时，平衡三维边长约为 \(m=\lceil N^{1/3}\rceil=162\)。于是三轴发送约为 \(486\) bits，而平面发送约为 \(26406\) bits。后者把请求放大了约 \(54.3\times\)。这个计算说明：中间 wire 应该留在 server-side gate circuit 中，而不是作为在线请求显式发送。

## 结论

- 三阶 selector 的核心是 share/wire 形态能否延续；明文代数只提供直观草图。
- 第一层乘法如果只输出 final additive share，就不能自动作为第二层乘法输入。
- PCG 需要服务于固定电路中的 linked gate material，而不是孤立乘法。
- 在线请求应发送三个轴向 masked inputs，不应发送二维中间平面。

## 参考

- ABY2.0: Improved Mixed-Protocol Secure Two-Party Computation: <https://www.usenix.org/conference/usenixsecurity21/presentation/patra>
- ABY2.0 full version PDF: <https://encrypto.de/papers/PSSY21.pdf>
- MOTION2NX repository: <https://github.com/encryptogroup/MOTION2NX>
- `mtrom/f2-ole-pcg`: <https://github.com/mtrom/f2-ole-pcg>

## 为什么这个问题不平凡

三阶 selector 的难点不只是多做一次乘法。continuation wire 承担的是“前一阶段选择结果如何安全进入下一阶段”的连接语义。如果这条线暴露或形状不固定，后续层即使单独安全也会泄漏路径信息。

## 证据路径

可以把三阶流程拆成三个对象：

```text
stage1=select first axis
continuation=masked state passed to next axis
stage2=select second axis using continuation
stage3=combine without revealing intermediate coordinate
```

证据重点是 continuation 的 view：服务器看到的消息长度、位置、更新频率和内容分布是否与真实路径无关。

## 当前结论与置信度

```text
conclusion=continuation_wire_is_core_security_object
confidence=medium_high
remaining_risk=needs_formal_server_view_and_cost_accounting
```

这个判断来自协议形状分析，还需要形式化 server view 后才能写成证明结论。

## 下一步验证

先固定一个玩具三阶数组，写出真实路径和伪路径的公开 transcript。如果两者在 continuation 长度或访问位置上不同，就说明当前设计还没有隐藏完整路径。

## 常见误判

最容易犯的错误是把中间乘积当成普通明文变量。明文里 \(xy\) 可以继续乘 \(z\)，协议里却要问 \(xy\) 的 share 形态是否仍满足下一层 gate 的输入约束。

第二个错误是只统计最终 response share。最终能重构不代表中间 wire 可延续；很多协议的中间对象还包含 mask、authentication tag、pairwise share 或固定电路位置。

第三个错误是把在线请求改成二维中间平面。这样看起来绕过了 continuation wire，实际把 \(m^2\) 级别的中间选择显式交给在线阶段，既放大通信，也可能改变泄漏形状。

## 可以怎样练习

先写一个 \(3\times3\times3\) 玩具例子，只记录公开 transcript，不写优化：

```text
input_axes=(x,y,z)
public_messages_for_real_path=
public_messages_for_dummy_path=
continuation_object_shape=
can_next_gate_consume_it=yes/no
```

若真实路径和伪路径在消息长度、位置集合或 continuation 对象数量上不同，当前设计就不能写成路径隐藏。这个练习比直接写性能表更早暴露协议缺口。
