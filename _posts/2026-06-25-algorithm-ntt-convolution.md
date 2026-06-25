---
layout: post
title: "NTT 卷积：在模数下做快速多项式乘法"
date: 2026-06-25 15:45:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "从卷积定义出发，解释 NTT 的系数表示、点值表示、单位根、逆变换和随机暴力对照。"
tags: [algorithm, ntt, convolution, polynomial, cplusplus]
---
{% raw %}
> 主题：Number Theoretic Transform / Convolution / Polynomial Multiplication / C++ 可复现实验
> 实验环境：Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1。

多项式乘法的系数形式直接计算需要 `O(nm)`。NTT 在模数域中把多项式从系数表示变成点值表示，逐点相乘后再逆变换回系数。常用模数 `998244353 = 119 · 2^23 + 1` 支持较长的 2 的幂次单位根。

## 学习目标

1. 把多项式乘法理解为卷积。
2. 说明 NTT 与 FFT 的表示转换思想。
3. 写出迭代 bit-reversal NTT。
4. 使用逆 NTT 恢复卷积系数。
5. 用暴力卷积验证随机样例。

## 核心模型

![NTT 卷积流程](/assets/diagrams/algorithm-ntt-convolution.svg)

系数表示下乘法昂贵；点值表示下乘法只需逐点相乘。NTT 和逆 NTT 负责两种表示之间的切换。

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

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
(1 + 2x + 3x^2) * (4 + 5x) coefficients: 4 13 22 15
mod=998244353 primitive_root=3
```

随机测试生成小多项式，用 NTT 结果和双循环暴力卷积逐项比较。固定样例对应 `4 + 13x + 22x^2 + 15x^3`。

## 正确性思路

NTT 选取模数域中的单位根，把次数小于 `n` 的多项式映射到 `n` 个点的取值。乘积多项式在每个点上的取值等于两个输入取值相乘。逆 NTT 利用单位根正交性恢复系数，并在最后乘以 `n` 的模逆元。

## 常见错误

- 变换长度没有补到至少 `a.size()+b.size()-1`。
- 逆变换后忘记乘 `inv_n`。
- 随意选择模数，导致不存在目标长度的单位根。

## 练习

1. 用 NTT 计算大整数乘法。
2. 使用多个 NTT 模数加 CRT 处理任意模数。
3. 实现形式幂级数求逆。
4. 比较暴力卷积和 NTT 的耗时拐点。

## 参考资料

- [cp-algorithms: Fast Fourier transform](https://cp-algorithms.com/algebra/fft.html)
- [cp-algorithms: Primitive Root](https://cp-algorithms.com/algebra/primitive-root.html)
- [cppreference: std::vector](https://en.cppreference.com/w/cpp/container/vector)
{% endraw %}
