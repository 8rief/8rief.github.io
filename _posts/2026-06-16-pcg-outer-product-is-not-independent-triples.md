---
layout: post
title: "PCG 笔记：outer product 相关性为什么不能由独立 triples 代替"
date: 2026-06-16 10:20:00 +0800
categories: secure-query
tags: [pcg, ole, outer-product, failed-attempt]
---

二维 selector 需要的不是一组互相独立的乘法相关性，而是一张共享轴向 mask 的 outer-product 相关矩阵。这个共享结构正是普通独立 triples 无法直接覆盖的地方。

## 背景：从 OLE PCG 到 selector material 的误判

OLE/PCG 相关工作关注如何让双方从短 seed 本地展开大量相关随机性。这个目标和 selector material 很接近，因此容易产生一个直觉：既然 PCG 可以生成许多乘法相关性，那么二维 selector 需要的材料也可以直接用很多独立乘法 triples 代替。

这个直觉的漏洞在于“很多乘法”和“结构化乘法矩阵”不是同一个对象。

## 定义：二维 selector 的目标是 outer product

设两个轴向 mask 为：

\[
\rho_x \in \{0,1\}^{m},\qquad \rho_y \in \{0,1\}^{n}.
\]

二维 selector 需要的二阶项是：

\[
R_{xy}[u,v] = \rho_x[u] \wedge \rho_y[v].
\]

矩阵形式为：

\[
R_{xy}=\rho_x \rho_y^\top.
\]

关键点是整张矩阵共享同一批轴向 mask。同一个 \(\rho_x[u]\) 会出现在第 \(u\) 行的所有列，同一个 \(\rho_y[v]\) 会出现在第 \(v\) 列的所有行。

## 为什么独立 triples 不够

独立 triples 通常给出很多互不相关的：

\[
a_{u,v},\quad b_{u,v},\quad c_{u,v}=a_{u,v}\wedge b_{u,v}.
\]

但 outer product 要求的是：

\[
a_{u,0}=a_{u,1}=\cdots=\rho_x[u],
\]

\[
b_{0,v}=b_{1,v}=\cdots=\rho_y[v].
\]

普通 triples 没有这个重复轴约束。若强行把每个格子当成独立乘法，正确性测试可能仍能通过某些局部断言，但无法保证 selector 的轴向一致性；若后续查询依赖轴 mask 与二阶材料之间的绑定关系，就会出现语义断裂。

## 更接近的对象：matrix-product correlation

Ring-LPN PCG 论文明确讨论了 matrix product correlations。outer product 是矩阵乘法的特例：令 \(A\) 是 \(m\times 1\) 的列向量 \(\rho_x\)，令 \(B\) 是 \(1\times n\) 的行向量 \(\rho_y^\top\)，则 \(C=AB\) 正好是 \(\rho_x\rho_y^\top\)。

这说明方向上应寻找 matrix-product / outer-product correlation PCG，而不是把 selector material 拆成独立 triples。

## 开源实现检查带来的边界

两个本地检查过的开源实现给出了不同边界：

- `mtrom/f2-ole-pcg` 实现的是 binary-field OLE 的 programmable PCG，接口包含 `prepare`、`online`、`finalize`、`expand` 等阶段，目标是 OLE 风格相关性；它没有直接暴露“给定两个复用轴向 mask，生成整张 linked outer-product material”的 API。
- `zhli271828/Trace-F2-OLE-PCG` 更贴近 \(\mathbb F_2\) 和 trace 方向，README 说明其目标包括 OLE 和 authenticated multiplication triples；但该实现仍是研究原型，且不是 selector outer-product 的 drop-in backend。

因此，失败点不是“PCG 没有用”，而是“选错了 PCG 目标相关性”。需要的是 linked outer-product / matrix-product correlation，而不是普通逐点乘法相关性。

## 结论

- 二维 selector 的核心对象是 \(\rho_x\rho_y^\top\)，不是很多独立的 \(a_i b_i\)。
- 轴向 mask 的复用关系是正确性和安全语义的一部分。
- matrix-product correlation 是更合适的理论接口。
- 现有 OLE PCG 实现可提供重要参考，但不能自动等价为 selector 所需的 linked outer-product PCG。

## 参考

- Efficient Pseudorandom Correlation Generators from Ring-LPN: <https://eprint.iacr.org/2022/1035>
- `mtrom/f2-ole-pcg`: <https://github.com/mtrom/f2-ole-pcg>
- `zhli271828/Trace-F2-OLE-PCG`: <https://github.com/zhli271828/Trace-F2-OLE-PCG>
