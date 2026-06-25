---
layout: post
title: "数论工具箱：gcd、筛法、快速幂、逆元和 CRT"
date: 2026-06-25 14:25:00 +0800
categories: algorithms-data-structures
column: algorithms-data-structures
column_title: "算法与数据结构"
excerpt: "把常用竞赛数论工具串成一条逻辑链：整除结构、素数表、模幂、扩展欧几里得、逆元和同余合并。"
tags: [algorithm, number-theory, modular-arithmetic, crt, cplusplus]
---
{% raw %}
> 主题：Number Theory Toolkit / gcd / sieve / modular inverse / CRT / C++ 可复现实验
> 本文实验在 Ubuntu 24.04、GCC 13.3.0、CMake 3.28.3、Ninja 1.11.1 环境下执行。实验包含固定样例、逆元校验和 CRT 可解/不可解检查。

数论题常常看起来分散：最大公约数、素数筛、快速幂、模逆元、中国剩余定理。把它们放在一起看，会发现主线很统一：先刻画整除结构，再在模意义下安全地做乘法、幂、方程求解和同余合并。

本文聚焦一个可复用的基础工具箱：整除、素数、模幂、逆元和同余合并。后续遇到组合计数、哈希、密码学玩具实验、图论计数或 CRT 分解，都可以从这些函数扩展。

## 学习目标

1. 写出欧几里得算法和扩展欧几里得算法。
2. 用线性筛得到不超过 `n` 的素数表。
3. 用二进制快速幂计算 `a^e mod m`。
4. 判断模逆元存在条件，并求出逆元。
5. 合并两个同余方程并检测无解情况。

## 核心模型

![数论工具之间的依赖关系](/assets/diagrams/algorithm-number-theory-toolkit.svg)

`gcd` 给出整除结构；扩展欧几里得给出 `ax + by = gcd(a,b)` 的系数；当 `gcd(a,m)=1` 时，系数 `x` 就是 `a` 在模 `m` 下的逆元。CRT 合并同余时也要依赖同样的 Bezout 系数。

## C++ 实现片段

```cpp
long long exgcd(long long a, long long b, long long& x, long long& y) {
    if (b == 0) { x = 1; y = 0; return a; }
    long long x1, y1;
    long long g = exgcd(b, a % b, x1, y1);
    x = y1;
    y = x1 - (a / b) * y1;
    return g;
}

optional<long long> mod_inverse(long long a, long long mod) {
    long long x, y;
    long long g = exgcd(a, mod, x, y);
    if (g != 1) return nullopt;
    x %= mod;
    if (x < 0) x += mod;
    return x;
}
```

快速幂按指数二进制展开，每一位决定是否把当前底数乘入结果。实验实现还使用了不依赖编译器扩展的安全模乘，避免严格编译选项下的非标准整数扩展警告。

## 实验输出

```text
100% tests passed, 0 tests failed out of 1
gcd(84,30)=6
primes<=30: 2 3 5 7 11 13 17 19 23 29
2^10 mod 1000=24
inverse of 3 mod 11=4
CRT x=2 mod 3, x=3 mod 5 -> x=8 mod 15
```

测试部分把 `gcd_ll` 与标准库 `std::gcd` 对照，检查线性筛结果，验证所有 `1..16` 中与 17 互素的数都满足 `a * inv(a) = 1 mod 17`。CRT 同时测试可解样例和不可解样例。

## CRT 合并思路

要合并 `x = a1 mod m1` 与 `x = a2 mod m2`，设 `x = a1 + k m1`。代入第二个方程得到 `k m1 = a2 - a1 mod m2`。这个线性同余有解当且仅当 `gcd(m1,m2)` 整除 `a2-a1`。

如果有解，就把模数合并为 `lcm(m1,m2)`。实现中要注意乘法溢出：教学代码覆盖 `long long` 可承载范围内的输入，工程代码应根据业务范围增加显式溢出检查或使用大整数。

## 复杂度

- 欧几里得与扩展欧几里得：`O(log min(a,b))`。
- 线性筛：`O(n)`。
- 快速幂：`O(log e)` 次模乘。
- CRT 合并两个方程：一次扩展欧几里得，`O(log min(m1,m2))`。

## 常见错误

**逆元存在条件写错。** `a` 在模 `m` 下有逆元的充要条件是 `gcd(a,m)=1`。

**负数取模没有规范化。** C++ 的 `%` 结果可能为负，需要统一转成 `[0, mod)`。

**把 CRT 默认成模数互素。** 非互素模数也可能有解，关键是余数差能否被 gcd 整除。

## 练习

1. 把两个同余方程合并扩展为合并一组同余方程。
2. 实现欧拉函数筛，并验证 `a^phi(m)=1 mod m` 的适用条件。
3. 用费马小定理在质数模下求逆元，并和 exgcd 版本比较。
4. 为 CRT 增加显式 lcm 溢出检测。

## 参考资料

- [cp-algorithms: Euclidean algorithm](https://cp-algorithms.com/algebra/euclid-algorithm.html)
- [cp-algorithms: Sieve of Eratosthenes](https://cp-algorithms.com/algebra/sieve-of-eratosthenes.html)
- [cp-algorithms: Binary exponentiation](https://cp-algorithms.com/algebra/binary-exp.html)
- [cp-algorithms: Modular inverse](https://cp-algorithms.com/algebra/module-inverse.html)
- [cp-algorithms: Chinese Remainder Theorem](https://cp-algorithms.com/algebra/chinese-remainder-theorem.html)
- [cppreference: std::gcd](https://en.cppreference.com/w/cpp/numeric/gcd)
{% endraw %}
