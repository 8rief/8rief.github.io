---
layout: post
title: "NTT 卷积：在模数下做快速多项式乘法"
date: 2026-03-13 18:00:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从卷积定义出发，解释 NTT 的系数表示、点值表示、单位根、逆变换和随机暴力对照。"
tags: [algorithm, ntt, convolution, polynomial, cplusplus]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/algorithms-ntt-convolution/README.md`](/assets/labs/algorithms-ntt-convolution/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
> 主题：Number Theoretic Transform / Convolution / Polynomial Multiplication / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

多项式乘法的系数形式直接计算需要 `O(nm)`。NTT 在模数域中把多项式从系数表示变成点值表示，逐点相乘后再逆变换回系数。常用模数 `998244353 = 119 · 2^23 + 1` 支持较长的 2 的幂次单位根。

当两个多项式各有数十个系数时，双循环最简单；当长度增长到数万，平方级乘法成为瓶颈。NTT 用有限域整数运算完成 FFT 同类的分治变换，结果天然按模数精确，不引入浮点舍入误差。

## 学习目标

1. 把多项式乘法理解为卷积。
2. 说明 NTT 与 FFT 的表示转换思想。
3. 写出迭代 bit-reversal NTT。
4. 使用逆 NTT 恢复卷积系数。
5. 用暴力卷积验证随机样例。

## 核心模型

![NTT 卷积流程](/assets/diagrams/algorithm-ntt-convolution.svg)

系数表示下乘法昂贵；点值表示下乘法只需逐点相乘。NTT 和逆 NTT 负责两种表示之间的切换。

## 为什么要引入变换

系数卷积定义为：

```text
c[k] = Σ_(i+j=k) a[i]b[j]
```

每个输出系数要汇总多组乘积。若在足够多的不同点上评价多项式，则乘积满足 `C(x)=A(x)B(x)`，每个点只做一次乘法；逆变换再从点值恢复系数。

变换长度 N 必须满足：

1. `N >= a.size()+b.size()-1`，避免循环卷积回绕；
2. N 是当前实现支持的 2 的幂；
3. 模数中存在 N 次单位根，即 `N | (MOD-1)`。

`998244353-1=119×2^23`，所以当前模数支持最大 `2^23` 的二次幂长度。

## 固定样例先手算

```text
(1+2x+3x²)(4+5x)
= 4 +(5+8)x +(10+12)x² +15x³
= 4 +13x +22x² +15x³
```

输入长度 3 和 2 需要 4 个输出系数，变换长度正好补到 N=4。

## C++ 实现片段

```cpp
for (int len = 2; len <= n; len <<= 1) {
    int wlen = mod_pow(G, (MOD - 1) / len);
    if (invert) wlen = mod_pow(wlen, MOD - 2);
    for (int i = 0; i < n; i += len) {
        long long w = 1;
        for (int j = 0; j < len / 2; ++j) {
            int u = a[i + j];
            int v = static_cast<int>(a[i + j + len / 2] * w % MOD);
            a[i + j] = u + v < MOD ? u + v : u + v - MOD;
            a[i + j + len / 2] = u - v >= 0 ? u - v : u - v + MOD;
            w = w * wlen % MOD;
        }
    }
}
```

每个 butterfly 接收 `u` 和旋转后的 `v`，输出 `(u+v,u-v)`；一层覆盖全部 N 个元素，共有 `log₂N` 层。开始前的 bit-reversal 置换把递归分治顺序改成可原地迭代的顺序：

```cpp
for (int i = 1, j = 0; i < n; ++i) {
    int bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) std::swap(a[i], a[j]);
}
```

逆变换使用单位根的逆元，并在最后乘 `N^-1 mod MOD`。由于 MOD 是质数，源码用费马小定理计算 `x^(MOD-2)`。

## 实验输出怎样解释

```text
100% tests passed, 0 tests failed out of 1
(1 + 2x + 3x^2) * (4 + 5x) coefficients: 4 13 22 15
mod=998244353 primitive_root=3
```

随机测试生成小多项式，用 NTT 结果和双循环暴力卷积逐项比较。固定样例对应 `4 + 13x + 22x^2 + 15x^3`。

复跑：

```bash
./run_lab.sh
```

CTest 使用 seed 17 生成 300 对随机多项式，两个长度都在 1 到 40，系数位于 0 到 1000；NTT 结果逐项等于模 `998244353` 的暴力卷积。空输入由公开 `convolution` 接口直接返回空数组。

## 正确性思路

NTT 选取模数域中的单位根，把次数小于 `n` 的多项式映射到 `n` 个点的取值。乘积多项式在每个点上的取值等于两个输入取值相乘。逆 NTT 利用单位根正交性恢复系数，并在最后乘以 `n` 的模逆元。

primitive root 3 生成模数乘法群。对每层长度 `len`，`3^((MOD-1)/len)` 是对应的 len 次单位根；其幂遍历该层所需评价点。单位根正交性使非零频率项在求和中抵消，只留下原系数的 N 倍，再由 `inv_n` 归一化。

## 复杂度与适用边界

设补零后的长度为 N。正变换两次、逐点乘法一次、逆变换一次，总时间 `O(N log N)`，额外数组空间 `O(N)`；暴力方法为 `O(nm)`。

当前实现只定义模 `998244353` 的非负规范系数。负数或外部大系数应先规范化到 `[0,MOD)`；目标模数不同且不支持足够单位根时，需要多模 NTT + CRT，或选择其他卷积方法。

## 常见错误

- 变换长度没有补到至少 `a.size()+b.size()-1`。
- 逆变换后忘记乘 `inv_n`。
- 随意选择模数，导致不存在目标长度的单位根。
- 输入长度超过 `2^23`，当前模数无法提供更长的二次幂单位根。
- 把 NTT 结果当普通整数卷积；系数增长超过模数后结果已经取模。
- 小数组也强行使用 NTT，常数成本可能高于双循环。

## 练习

1. 用 NTT 计算大整数乘法。
2. 使用多个 NTT 模数加 CRT 处理任意模数。
3. 实现形式幂级数求逆。
4. 比较暴力卷积和 NTT 的耗时拐点。
5. 加入负系数规范化，并用暴力模卷积验证。

## 参考资料

- [cp-algorithms: Fast Fourier transform](https://cp-algorithms.com/algebra/fft.html)
- [cp-algorithms: Primitive Root](https://cp-algorithms.com/algebra/primitive-root.html)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
