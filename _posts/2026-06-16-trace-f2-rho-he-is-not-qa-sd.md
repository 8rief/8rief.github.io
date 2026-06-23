---
layout: post
title: "Trace-F2 PCG 笔记：rho = H e 原型为什么缺少安全依据"
date: 2026-06-16 10:30:00 +0800
categories: secure-query
column: problem-exploration
column_title: "问题探究"
tags: [pcg, trace, qa-sd, failed-attempt]
---

一个小规模测试正确、输出也看起来随机的 \(\rho=He\) 原型，不能直接当成安全 PCG。问题不在代数正确性，而在它没有接上论文证明所依赖的样本分布。

## 背景：一个很诱人的简化

为了 seed 化 selector mask，可以考虑如下构造：令 \(e\) 是稀疏秘密，令 \(H_\tau\) 是由 token 或 counter 派生的公开矩阵，然后定义：

\[
\rho_\tau=H_\tau e.
\]

这个构造很容易实现，也容易做出许多通过正确性测试的输出。不同 counter 使用不同 \(H_\tau\)，表面上也能得到不同 mask。

但这只是一个线性稀疏编码原型，不等于 Trace-F2 PCG 的安全构造。

## Trace-F2 方向依赖的样本形状

Li 等关于任意有限域 PCG 的工作，以及 `Trace-F2-OLE-PCG` 原型，使用的安全基础更接近：

\[
x = a s + e,
\]

再通过 trace 映射得到目标域上的相关性。这里 \(s\) 和 \(e\) 是稀疏秘密，\(a\) 是公开结构，安全性依赖 QA-SD/Ring-LPN 类假设和 trace 变换。也就是说，证明讨论的是一个具体分布，而不是“公开矩阵乘稀疏向量看起来随机”这个直觉。

如果把结构改成 \(\rho_\tau=H_\tau e\)，尤其还跨很多 counter 复用同一个 \(e\)，就不能直接继承原文安全性。

## README 警告本身也是一个信号

`Trace-F2-OLE-PCG` 的 README 给出两个重要边界：

1. 它是 OLE 和 authenticated multiplication triples 的 prototype implementation，面向研究用途；
2. README 明确提示，早期 QA-SD 参数 \((c=3,t=27,q=4,n=16)\) 已被新攻击影响，并建议例如 \((c=5,t=27,q=4,n\le16)\) 等参数，其中推荐参数在作者机器上约慢 \(2.75\times\)。

这说明安全性不能靠“测试能跑”判断。即使是在论文形状内，参数也需要随攻击进展重新评估；偏离论文形状后，更不能把正确性测试当作安全证据。

## 小测试为什么容易误导

\(\rho=He\) 可以通过以下测试：

- 输出长度正确；
- 不同 counter 输出不同；
- selector 组合后的代数关系正确；
- 单次查询结果与明文模拟一致。

这些测试只能说明实现没有明显算错。它们不能证明 server view 下的不可区分性，也不能证明复用稀疏秘密时不存在跨 token 相关性泄露。密码实现中，正确性测试和安全性论证是两类证据。

## 结论

- \(\rho=He\) 可以作为正确性原型，但不能作为安全 PCG 结论。
- Trace-F2 路线的安全基础是 \(x=as+e\) 加 trace，而不是任意线性稀疏编码。
- 复用同一个稀疏 \(e\) 跨 counter 会让安全论证更加困难。
- 研究原型的 README 参数警告应被当作安全边界，而不是实现细节。

## 参考

- Efficient Pseudorandom Correlation Generators for Any Finite Field: <https://eprint.iacr.org/2025/169>
- `Trace-F2-OLE-PCG`: <https://github.com/zhli271828/Trace-F2-OLE-PCG>
- Trace-F2 code availability note in the published version: <https://link.springer.com/content/pdf/10.1007/978-3-031-91092-0_6.pdf?pdf=inline+link>
