---
layout: post
title: "子域格图怎么画：以 GF(p^12) 为例"
date: 2026-06-25 15:04:00 +0800
categories: mathematical-foundations
column: mathematical-foundations
column_title: "数学基础"
excerpt: "用指数整除规则画出 GF(p^12) 的全部子域，并解释交、生成域与 gcd/lcm 的关系。"
tags: [math, finite-field, subfield]
---
{% raw %}

> 主题：子域格图 / 指数整除 / gcd 与 lcm

有限域的子域结构非常规整。对 \(\mathrm{GF}(p^n)\)，它的子域正好对应 \(n\) 的正因子：

\[
\mathrm{GF}(p^d),\qquad d\mid n.
\]

而且包含关系也只看指数是否整除：

\[
\mathrm{GF}(p^a)\subseteq\mathrm{GF}(p^b)
\iff
 a\mid b.
\]

这篇用 \(\mathrm{GF}(p^{12})\) 做完整例子。

![GF(p^12) 的子域格图](/assets/diagrams/finite-field-subfield-lattice-p12.svg)

## 第一步：找 12 的所有正因子

\(12\) 的正因子是

\[
1,2,3,4,6,12.
\]

所以 \(\mathrm{GF}(p^{12})\) 的子域是

\[
\mathrm{GF}(p),
\mathrm{GF}(p^2),
\mathrm{GF}(p^3),
\mathrm{GF}(p^4),
\mathrm{GF}(p^6),
\mathrm{GF}(p^{12}).
\]

没有 \(\mathrm{GF}(p^5)\)，因为 \(5\nmid12\)。也没有 \(\mathrm{GF}(p^8)\)，因为 \(8\nmid12\)。

## 第二步：按整除关系连线

根据

\[
\mathrm{GF}(p^a)\subseteq\mathrm{GF}(p^b)
\iff a\mid b,
\]

可以得到：

\[
\mathrm{GF}(p)\subset\mathrm{GF}(p^2),
\quad
\mathrm{GF}(p)\subset\mathrm{GF}(p^3),
\]

\[
\mathrm{GF}(p^2)\subset\mathrm{GF}(p^4),
\quad
\mathrm{GF}(p^2)\subset\mathrm{GF}(p^6),
\]

\[
\mathrm{GF}(p^3)\subset\mathrm{GF}(p^6),
\]

\[
\mathrm{GF}(p^4)\subset\mathrm{GF}(p^{12}),
\quad
\mathrm{GF}(p^6)\subset\mathrm{GF}(p^{12}).
\]

但下面这些不成立：

\[
\mathrm{GF}(p^3)\not\subseteq\mathrm{GF}(p^4),
\]

因为 \(3\nmid4\)。同理，

\[
\mathrm{GF}(p^4)\not\subseteq\mathrm{GF}(p^6),
\quad
\mathrm{GF}(p^6)\not\subseteq\mathrm{GF}(p^4).
\]

## 为什么叫“格”

格的意思是：任意两个节点都有交，也有共同生成的最小上界。

在有限域子域中，规则特别简单：

\[
\mathrm{GF}(p^a)\cap\mathrm{GF}(p^b)=\mathrm{GF}(p^{\gcd(a,b)}),
\]

\[
\mathrm{GF}(p^a)\mathrm{GF}(p^b)=\mathrm{GF}(p^{\operatorname{lcm}(a,b)}).
\]

这里第二个式子表示两个子域共同生成的复合域。

## 例子一：\(\mathrm{GF}(p^4)\) 和 \(\mathrm{GF}(p^6)\)

它们的交是

\[
\mathrm{GF}(p^4)\cap\mathrm{GF}(p^6)
=\mathrm{GF}(p^{\gcd(4,6)})
=\mathrm{GF}(p^2).
\]

它们共同生成的域是

\[
\mathrm{GF}(p^{\operatorname{lcm}(4,6)})
=\mathrm{GF}(p^{12}).
\]

所以图上 \(\mathrm{GF}(p^4)\) 和 \(\mathrm{GF}(p^6)\) 往下共同落到 \(\mathrm{GF}(p^2)\)，往上共同生成 \(\mathrm{GF}(p^{12})\)。

## 例子二：\(\mathrm{GF}(p^2)\) 和 \(\mathrm{GF}(p^3)\)

它们的交是

\[
\mathrm{GF}(p^{\gcd(2,3)})=\mathrm{GF}(p).
\]

共同生成的域是

\[
\mathrm{GF}(p^{\operatorname{lcm}(2,3)})=\mathrm{GF}(p^6).
\]

因此 \(\mathrm{GF}(p^2)\) 和 \(\mathrm{GF}(p^3)\) 在图中没有包含关系，但它们一起能生成 \(\mathrm{GF}(p^6)\)。

## 这个结构有什么用

第一，它告诉我们某个元素可能落在哪个更小子域中。若元素 \(a\) 满足 \(a^{p^d}=a\)，它就在 \(\mathrm{GF}(p^d)\) 中。

第二，它帮助组织塔式扩张。例如可以先从 \(\mathrm{GF}(p)\) 到 \(\mathrm{GF}(p^2)\)，再到 \(\mathrm{GF}(p^6)\)，最后到 \(\mathrm{GF}(p^{12})\)。

第三，它在编码理论、有限域变换、计算代数和序列分析中帮助判断“这个运算到底发生在哪一层域里”。

## 常见误区

**误区一：只要指数小就是子域。** 不对。\(3<4\)，但 \(\mathrm{GF}(p^3)\) 不是 \(\mathrm{GF}(p^4)\) 的子域，因为 \(3\nmid4\)。

**误区二：两个子域的交总是最小域。** 不一定。\(\mathrm{GF}(p^4)\) 和 \(\mathrm{GF}(p^6)\) 的交是 \(\mathrm{GF}(p^2)\)，不是 \(\mathrm{GF}(p)\)。

**误区三：格图只是画图技巧。** 它实际表达的是子域包含、交、生成域的代数关系。

## 检查点

在 \(\mathrm{GF}(p^{18})\) 中，\(\mathrm{GF}(p^6)\) 和 \(\mathrm{GF}(p^9)\) 的交是什么？它们共同生成哪个子域？

{% endraw %}
