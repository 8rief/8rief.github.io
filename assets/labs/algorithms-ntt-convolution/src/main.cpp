#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <string>
#include <vector>

constexpr int MOD = 998244353;
constexpr int G = 3;

int mod_pow(long long a, long long e) {
    long long r = 1;
    while (e) {
        if (e & 1) r = r * a % MOD;
        a = a * a % MOD;
        e >>= 1;
    }
    return static_cast<int>(r);
}

void ntt(std::vector<int>& a, bool invert) {
    int n = static_cast<int>(a.size());
    for (int i = 1, j = 0; i < n; ++i) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) std::swap(a[i], a[j]);
    }
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
    if (invert) {
        int inv_n = mod_pow(n, MOD - 2);
        for (int& x : a) x = static_cast<int>(1LL * x * inv_n % MOD);
    }
}

std::vector<int> convolution(std::vector<int> a, std::vector<int> b) {
    if (a.empty() || b.empty()) return {};
    int need = static_cast<int>(a.size() + b.size() - 1);
    int n = 1;
    while (n < need) n <<= 1;
    a.resize(n);
    b.resize(n);
    ntt(a, false);
    ntt(b, false);
    for (int i = 0; i < n; ++i) a[i] = static_cast<int>(1LL * a[i] * b[i] % MOD);
    ntt(a, true);
    a.resize(need);
    return a;
}

std::vector<int> brute_convolution(const std::vector<int>& a, const std::vector<int>& b) {
    std::vector<int> c(a.size() + b.size() - 1);
    for (int i = 0; i < static_cast<int>(a.size()); ++i)
        for (int j = 0; j < static_cast<int>(b.size()); ++j)
            c[i + j] = static_cast<int>((c[i + j] + 1LL * a[i] * b[j]) % MOD);
    return c;
}

void run_tests() {
    assert((convolution({1, 2, 3}, {4, 5}) == std::vector<int>{4, 13, 22, 15}));
    std::mt19937 rng(17);
    std::uniform_int_distribution<int> n_dist(1, 40);
    std::uniform_int_distribution<int> value_dist(0, 1000);
    for (int round = 0; round < 300; ++round) {
        int n = n_dist(rng), m = n_dist(rng);
        std::vector<int> a(n), b(m);
        for (int& x : a) x = value_dist(rng);
        for (int& x : b) x = value_dist(rng);
        assert(convolution(a, b) == brute_convolution(a, b));
    }
}

void run_demo() {
    auto c = convolution({1, 2, 3}, {4, 5});
    std::cout << "(1 + 2x + 3x^2) * (4 + 5x) coefficients: ";
    for (int x : c) std::cout << x << ' ';
    std::cout << "\nmod=" << MOD << " primitive_root=" << G << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "ntt convolution tests passed\n";
        return 0;
    }
    run_demo();
}
