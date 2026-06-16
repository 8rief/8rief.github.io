---
layout: post
title: "DPF/PIR 学习笔记：短查询 key 不等于动态更新友好"
date: 2026-06-16 10:10:00 +0800
categories: secure-query
tags: [dpf, pir, update, source-reading]
---

这篇只讨论一个问题：**为什么 DPF/PIR 里的短查询 key，并不自动意味着 append/update 也便宜。**

读 `dpf-cpp` 时，最容易记住的是 DPF 的漂亮接口：client 生成两份 key，两个 non-colluding servers 在相同数据库上分别评估，client 合并响应。这个抽象非常干净：

```text
client 生成 key0, key1
server0 Eval(key0, DB)
server1 Eval(key1, DB)
client 合并 response
```

但它主要解决的是“怎么私密读取一个位置”。一旦进入动态数据库，问题会发生变化。

## 读操作和写操作是两类问题

PIR/DPF 的核心目标是隐藏读位置。数据库可以被看成一个相对静态的数组，服务器固定扫描或评估，client 拿到目标记录。

但是时间序列系统不是只有 read。append-only 场景里，新的记录不断进入，聚合结构也可能变化。于是要多问一个问题：

```text
数据库变了以后，之前准备好的查询材料还有效吗？
```

如果查询材料只依赖随机性和查询位置，那么更新数据库可能很简单。可如果查询材料里提前混入了数据库状态、mask、hint 或某些预计算结果，append 就可能要求修正大量未使用材料。

## 短 key 不能掩盖 hidden maintenance cost

DPF key 本身可能很短，但系统总成本不只取决于 key size。还要看：

- server eval 是否需要全库扫描；
- 数据库更新后是否需要重建 hint；
- 是否有和 token 绑定的预处理材料；
- append 是否会影响多个聚合节点；
- 更新是否需要通知每个未来 query token。

这也是我后来理解动态安全查询时的一个重要分界：

```text
查询随机材料是否依赖数据库状态？
```

如果依赖，append 就不再只是写数据，还可能变成维护未来查询材料。

## 一个容易混淆的地方

有时我们会说“服务器存相同数据库，client 发 DPF key，最后合成结果”。这个说法对读很自然。但如果要支持 update，就要区分：

```text
更新数据库本身
vs
更新和数据库绑定的查询 hint/material
```

前者是数据层问题，后者是随机材料层问题。两者混在一起，系统会变得很难分析。

## 我从 DPF/PIR 学到的判断标准

以后看到一个 PIR/DPF 方案，我会先问四个问题：

1. 数据库是静态还是动态？
2. setup/hint 是否依赖数据库内容？
3. update 是否会让未使用 query key 失效？
4. 更新成本是随 record width、数据库大小，还是 token 数增长？

只有这四个问题都清楚了，才能判断它是否适合 append-only 时间序列。

## 参考源码

- dpf-cpp: <https://github.com/dkales/dpf-cpp>
