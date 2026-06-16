---
layout: post
title: "PCG 失败复盘（三）：三阶 selector 难点不是多乘一次，而是 continuation wire"
date: 2026-06-16 10:40:00 +0800
categories: secure-query
tags: [pcg, aby2, tensor, failed-attempt]
---

这篇只讨论一个问题：**三阶 selector 的难点不是把三个 bit 乘起来，而是中间乘积能不能继续作为 wire 使用。**

在三维 selector 里，一个自然目标是：

```text
rho_x * rho_y * rho_z
```

直觉上可以分两步：

```text
rho_xy  = rho_x * rho_y
rho_xyz = rho_xy * rho_z
```

看起来只是多做一次乘法。但真正进入 secret sharing / PCG 语境后，这个想法会遇到一个关键问题：第一层输出是什么形式？

## final share 和 continuation wire 不一样

如果第一层乘法只输出一个最终 additive share，那么它可以用于本次响应重构，但未必能继续参与下一层乘法。

继续乘法通常要求中间值仍然处在某种 wire/share 表示里。换句话说，`rho_xy` 不能只是“最后答案的一部分”，它必须还能被 server 当作下一层 gate 的输入。

这就是我理解的 continuation wire 问题。

```text
rho_x, rho_y  --mul gate-->  rho_xy as wire
rho_xy, rho_z --mul gate-->  rho_xyz as wire/share
```

如果第一层 gate 没有输出可继续使用的 wire，第二层 gate 就没有正确输入。

## ABY2.0 给我的启发

ABY2.0/MOTION2NX 这类工作让我意识到，乘法协议不只是“算出乘积 share”。它还关心 wire representation、masked value、setup correlation 和 online reconstruction 的关系。

对于固定电路，如果 setup 阶段已经知道后续要乘哪些东西，就可以把相关材料围绕电路结构组织，而不是把每个乘法都当成孤立事件。

但这也意味着：

```text
普通二阶 PCG + 临时拼接
```

不一定足够。你需要的是：

```text
circuit-dependent preprocessing
或 linked gate-correlation PCG
```

## 为什么直接三阶 tensor 很重

另一个替代路线是直接生成：

```text
rho_x ⊗ rho_y ⊗ rho_z
```

这样可以绕过中间 wire 问题。但它会带来三阶 tensor 的存储和 key 数量问题。尤其是使用 sparse cross-term + SPFSS 这类方法时，二阶是 `t^2`，三阶就会变成 `t^3`，还要乘上多个 holder pattern、trace/Frobenius 分量和 component 组合。

所以直接三阶 tensor 是一个清晰但很重的 baseline。

## 这次失败的核心原因

我最初把问题想成：

```text
有二阶 PCG，就能拼出三阶
```

后来发现更准确的说法应该是：

```text
有二阶 PCG，只能说明第一层乘法有希望；
如果第二层要继续乘，第一层输出必须被组织成可继续使用的 wire，
这需要 linked/circuit-dependent 的相关材料。
```

也就是说，三阶问题不是“乘法次数 +1”，而是“相关材料结构升级”。

## 后续问题

未来值得看的问题包括：

1. 有没有现成 PCF/PCG 支持固定电路的 linked preprocessing？
2. 能不能避免显式三阶 tensor，在扫描或评估过程中边展开边消费？
3. 对 selector 这种特殊电路，是否存在比通用 circuit preprocessing 更轻的构造？
4. 安全参数下，三阶直接 baseline 的 key size 到底是否完全不可接受，还是在某些小域/小 depth 场景可用？

这些问题比“再写一个 demo”更重要。

## 参考源码

- MOTION2NX: <https://github.com/encryptogroup/MOTION2NX>
- f2-ole-pcg: <https://github.com/mtrom/f2-ole-pcg>
- Trace-F2-OLE-PCG: <https://github.com/zhli271828/Trace-F2-OLE-PCG>
