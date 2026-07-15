---
layout: post
title: "Trace-F2 PCG 笔记：rho = H e 原型为什么缺少安全依据"
date: 2026-07-12 18:00:00 +0800
categories: secure-query
column: problem-exploration
column_title: "问题探究"
tags: [pcg, trace, qa-sd, failed-attempt]
---

一个小规模测试正确、输出也看起来随机的 \(\rho=He\) 原型，不能直接当成安全 PCG。问题不在代数正确性，而在它没有接上论文证明所依赖的样本分布。

## 问题为什么不平凡

密码构造同时承担两项义务。正确性要求相关方展开后得到预期代数关系；安全性要求攻击者看到的联合分布满足明确的不可区分性定义。输出长度相同、边缘分布均匀或功能测试通过，只能提供前一类证据。

PCG 的证明还会固定参与方视图、公开参数、秘密采样方式以及跨多次调用时的相关性。替换其中一个分布后，原定理没有自动覆盖新构造。评估 \(\rho=He\) 的第一步因而是找到可引用的安全归约，而不是继续扩大性能测试。

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

## 跨 counter 复用暴露了什么结构

观察者收集 \(T\) 个公开矩阵与输出后，可以把它们写成一个线性系统：

\[
\begin{bmatrix}
\rho_1\\
\rho_2\\
\vdots\\
\rho_T
\end{bmatrix}
=
\begin{bmatrix}
H_1\\
H_2\\
\vdots\\
H_T
\end{bmatrix}e.
\]

随着 counter 增加，未知量 \(e\) 没有增加，线性观察却持续累积。是否能恢复 \(e\)、区分输出或利用稀疏性，取决于矩阵分布、维度、噪声与攻击复杂度。当前原型没有给出这些条件下的 hardness assumption，也没有证明堆叠分布与 Trace-F2 的 QA-SD 样本等价。

这段推导只能指出证明缺口，尚未构成有效攻击。要把怀疑升级为结论，需要给出具体参数、攻击算法、成功率和复杂度。

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

## 为什么本文没有安排“运行成功”演示

这里缺少的是安全归约，不是一个尚未执行的命令。再写一个 CLI 可以证明矩阵乘法与序列化正确，却无法证明攻击者视图安全；把绿色测试截图放在这里反而会模糊证据层级。

因此，本文只保留来源可核对的构造形状、README 参数警告与线性观察。后续若实现攻击实验，演示必须同时报告公开参数、样本数量、秘密复用次数、攻击预算和随机种子，不能只展示一次“恢复成功”。

## 下一步验证

1. **锁定目标相关性**：明确需要生成 OLE、乘法三元组还是 selector mask，并写出双方完整视图。
2. **逐项对照定理**：核对论文中 \(a,s,e\) 的分布、trace 映射、参数范围与安全游戏，列出 \(\rho=He\) 改动的每一项假设。
3. **建立攻击基线**：实现稀疏恢复、秩分析和跨 counter 区分器，扫描 \(T\)、矩阵维度与秘密重量。
4. **使用当前攻击重新定参**：先复现公开的 QA-SD 参数攻击，再评估 README 推荐参数；无法复现时不得宣称参数安全。
5. **设置终止条件**：若没有可信归约，或多样本攻击在目标参数内有效，\(\rho=He\) 只保留为正确性玩具，不进入安全方案。

## 常见误判

第一类误判是把随机性外观当成安全性。输出的 0/1 比例接近均匀、不同 counter 输出不同，只能说明样本不像明显常数；它不能替代不可区分性游戏。

第二类误判是忽略秘密复用。单个 \(\rho=He\) 看起来无害，不代表同一个稀疏 \(e\) 在大量公开 \(H_\tau\) 下仍安全。多样本场景必须单独建模。

第三类误判是把研究原型 README 的参数警告当成实现备注。参数被新攻击影响，说明安全余量本身在变化；偏离论文分布的原型更不能沿用旧参数直觉。

## 可以怎样练习

可以先不写协议，做一个分布对照表：

```text
paper_sample_shape=x=a*s+e
prototype_shape=rho=H*e
secret_reuse_count=T
public_matrix_distribution=
known_attack_to_run=
claim_allowed=correctness_only/security
```

只有当每一行都能对上论文假设或新的安全归约，才考虑把原型升级为候选方案。否则，实验最多用于验证矩阵运算和序列化。

## 结论

- \(\rho=He\) 可以作为正确性原型，但不能作为安全 PCG 结论。
- Trace-F2 路线的安全基础是 \(x=as+e\) 加 trace，而不是任意线性稀疏编码。
- 复用同一个稀疏 \(e\) 跨 counter 会让安全论证更加困难。
- 研究原型的 README 参数警告应被当作安全边界，而不是实现细节。

## 参考

- Efficient Pseudorandom Correlation Generators for Any Finite Field: <https://eprint.iacr.org/2025/169>
- `Trace-F2-OLE-PCG`: <https://github.com/zhli271828/Trace-F2-OLE-PCG>
- Published chapter: <https://link.springer.com/chapter/10.1007/978-3-031-91092-0_6>
- Practical Cryptanalysis of Pseudorandom Correlation Generators Based on Quasi-Abelian Syndrome Decoding: <https://eprint.iacr.org/2025/892>
