---
layout: post
title: "PCG 失败复盘（一）：outer product 不是很多个独立乘法三元组"
date: 2026-06-16 10:20:00 +0800
categories: secure-query
tags: [pcg, ole, outer-product, failed-attempt]
---

这篇只讨论一个问题：**为什么“能生成很多二阶乘法相关性”不等于“能生成 selector 需要的 outer-product 相关性”。**

我一开始看 F2 OLE PCG 时，很自然地想：既然 PCG 可以从短 seed 展开很多乘法相关随机性，那它是不是可以直接生成二维 selector 需要的材料？后来发现，这个想法太粗糙。

## selector 里的二维相关性长什么样

二维 selector 里常见的目标不是一批互相独立的乘法：

```text
a_i AND b_i
```

而是一张 outer-product 矩阵：

```text
R_xy[u, v] = rho_x[u] AND rho_y[v]
```

关键区别在于，整张矩阵共享同一批轴向 mask：

```text
rho_x[0], rho_x[1], ...
rho_y[0], rho_y[1], ...
```

这意味着同一个 `rho_x[u]` 会出现在很多列，同一个 `rho_y[v]` 会出现在很多行。

## 独立 triples 为什么不够

普通独立 triples 可以给你很多组：

```text
a_{u,v}, b_{u,v}, c_{u,v} = a_{u,v} AND b_{u,v}
```

但这并不保证：

```text
a_{u,0} = a_{u,1} = ... = rho_x[u]
b_{0,v} = b_{1,v} = ... = rho_y[v]
```

也就是说，它缺少 repeated-axis 约束。

如果没有这个约束，矩阵里的每个格子确实有乘法关系，但它们不是同一个 selector 的 outer product。这样生成出来的东西可以通过局部测试，却无法对应到真正的二维 one-hot 选择结构。

## 为什么普通 F2 OLE PCG 不能直接替代

`f2-ole-pcg` 这类实现解决的是 binary field OLE PCG 问题。它的接口围绕 seed exchange 和 expansion，生成大量 F2 上的 OLE-style correlations。这当然很有价值。

但对我的目标来说，还要额外问：

```text
这些 correlations 的输入能否被组织成重复轴？
能否直接表达 matrix-product / outer-product？
能否把同一 rho_x[u] 绑定到一整行？
能否把同一 rho_y[v] 绑定到一整列？
```

如果接口没有暴露这种 linked matrix-product 能力，那它就不是我需要的 primitive。

## 这次失败的核心原因

失败不在于 PCG 没用，而在于我一开始把 primitive 名字看得太粗。

我真正需要的是：

```text
linked outer-product PCG
或 matrix-product correlation PCG
```

而不是普通的：

```text
many independent multiplication triples
```

这两者的抽象层级不同。

## 后续问题

这个失败反而提出了一个更清楚的问题：

> 是否存在一个工程上可用的、支持 repeated-axis matrix-product correlation 的 PCG/PCF 接口？

如果有，它会是二维 selector seed 化的关键工具。若没有，就要么自己设计适配层，要么换一种数据/selector 组织方式。

## 参考源码

- f2-ole-pcg: <https://github.com/mtrom/f2-ole-pcg>
