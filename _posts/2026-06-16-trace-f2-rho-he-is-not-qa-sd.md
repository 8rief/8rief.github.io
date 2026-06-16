---
layout: post
title: "PCG 失败复盘（二）：为什么 rho = H e 不能替代 QA-SD/trace 结构"
date: 2026-06-16 10:30:00 +0800
categories: secure-query
tags: [pcg, trace, qa-sd, failed-attempt]
---

这篇只讨论一个问题：**一个看起来随机、测试也正确的 `rho = H e` 构造，为什么不能直接当成安全 PCG。**

在尝试 seed 化 selector material 时，我曾经考虑过一种非常直接的做法：令 `e` 是稀疏秘密，`H` 是由 label/counter 派生的公开矩阵，然后：

```text
rho_tau = H_tau e
```

这个构造很诱人，因为它容易实现，也容易让不同 counter 产生不同输出。小规模测试里，它可以通过很多正确性检查。

但后来我认为这个方向不能作为安全结论。

## 问题不在正确性，而在安全来源

`rho = H e` 可以做出正确的代数关系，不代表它接上了论文里的安全假设。

Trace-F2-OLE-PCG 相关工作里的核心样本形状更接近：

```text
x = a * s + e
rho = Tr(x)
```

这里 `s` 和 `e` 是稀疏秘密，`a` 是公开结构，安全性来自 QA-SD/Ring-LPN 类假设和 trace 变换。也就是说，安全证明依赖的是一个具体分布，而不是“公开矩阵乘稀疏向量看起来随机”这个直觉。

如果把它改成：

```text
rho_tau = H_tau e
```

并且还让同一个 `e` 跨很多 counter 复用，那就不能直接套原文安全性。

## 为什么小测试会误导

这类构造在小规模测试里可能表现不错：

- 输出看起来接近平衡；
- 不同 counter 输出不同；
- 单点统计看不出明显泄露；
- selector reconstruction 正确。

但这些测试只能说明“没有发现明显错误”，不能说明它满足 QA-SD/trace 的伪随机性。

安全构造最危险的地方就在这里：

```text
正确性测试通过 ≠ 安全分布正确
```

## Trace-F2 路线真正有用的部分

Trace-F2-OLE-PCG 仍然很有价值。它提醒我：

1. 要回到 `a*s+e` 这样的证明结构；
2. sparse cross terms 可以用 DPF/SPFSS 分享；
3. F2 目标域可以通过 trace 处理；
4. 参数安全性不是随便选小参数就行。

尤其是它 README 里对 QA-SD 参数安全的提醒，很适合作为警示：能跑 demo 的参数不一定安全，旧参数甚至可能被新的攻击否定。

## 这次失败的核心原因

这个方向失败不是因为它完全没有用，而是因为它只能作为代数/接口原型，不能作为安全 PCG 实现。

更准确地说：

```text
rho = H e
```

可以帮助验证 selector 公式和工程接口；但如果要写安全性，就必须回到：

```text
x = a*s + e
rho = Tr(x)
```

以及与之配套的 sparse cross-term sharing。

## 后续问题

真正值得继续做的问题是：

> 如何把 QA-SD/trace sample 产生的轴向 mask，和 selector 需要的 outer-product/tensor-product correlation 绑定起来？

这不是简单替换一行 PRG，而是要重新定义 setup 输出、holder key、client key、counter/label 范围和安全参数。

## 参考源码

- Trace-F2-OLE-PCG: <https://github.com/zhli271828/Trace-F2-OLE-PCG>
