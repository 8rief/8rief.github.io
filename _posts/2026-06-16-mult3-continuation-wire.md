---
layout: post
title: "三阶 selector 笔记：continuation wire 为什么是核心难点"
date: 2026-06-16 10:40:00 +0800
categories: secure-query
column: problem-exploration
column_title: "问题探究"
tags: [pcg, aby2, tensor, failed-attempt]
---

三阶 selector 的难点不是“把三个 bit 多乘一次”，而是中间乘积能否继续作为 wire 参与后续 gate。若第一层乘法只给出最终 additive share，它可以用于本次重构，却不一定能作为第二层乘法的输入。

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

换到三阶 selector 上，PCG 需要 seed 化的不是一个孤立的 \(xy\)，而是固定电路中的 gate material：第一层 gate 的输出必须能被第二层 gate 消费。若现有 PCG 只提供普通 OLE 或逐点乘法相关性，而没有 linked continuation-wire API，就还不是完整解决方案。

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

- 三阶 selector 的核心不是明文代数，而是 share/wire 形态能否延续。
- 第一层乘法如果只输出 final additive share，就不能自动作为第二层乘法输入。
- PCG 需要服务于固定电路中的 linked gate material，而不是孤立乘法。
- 在线请求应发送三个轴向 masked inputs，不应发送二维中间平面。

## 参考

- ABY2.0: Improved Mixed-Protocol Secure Two-Party Computation: <https://www.usenix.org/conference/usenixsecurity21/presentation/patra>
- ABY2.0 full version PDF: <https://encrypto.de/papers/PSSY21.pdf>
- MOTION2NX repository: <https://github.com/encryptogroup/MOTION2NX>
- `mtrom/f2-ole-pcg`: <https://github.com/mtrom/f2-ole-pcg>
