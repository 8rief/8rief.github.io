#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <string>
#include <vector>

std::vector<int> suffix_array(const std::string& s) {
    int n = static_cast<int>(s.size());
    if (n == 0) return {};
    std::vector<int> sa(n), rank(n), tmp(n);
    for (int i = 0; i < n; ++i) { sa[i] = i; rank[i] = static_cast<unsigned char>(s[i]); }
    for (int k = 1;; k <<= 1) {
        auto key = [&](int i) { return std::pair<int, int>{rank[i], i + k < n ? rank[i + k] : -1}; };
        std::sort(sa.begin(), sa.end(), [&](int a, int b) { return key(a) < key(b); });
        tmp[sa[0]] = 0;
        for (int i = 1; i < n; ++i) tmp[sa[i]] = tmp[sa[i - 1]] + (key(sa[i - 1]) < key(sa[i]));
        rank = tmp;
        if (rank[sa.back()] == n - 1) break;
    }
    return sa;
}

std::vector<int> lcp_array(const std::string& s, const std::vector<int>& sa) {
    int n = static_cast<int>(s.size());
    std::vector<int> rank(n), lcp(std::max(0, n - 1));
    for (int i = 0; i < n; ++i) rank[sa[i]] = i;
    int h = 0;
    for (int i = 0; i < n; ++i) {
        if (rank[i] == n - 1) { h = 0; continue; }
        int j = sa[rank[i] + 1];
        while (i + h < n && j + h < n && s[i + h] == s[j + h]) ++h;
        lcp[rank[i]] = h;
        if (h) --h;
    }
    return lcp;
}

std::vector<int> brute_sa(const std::string& s) {
    std::vector<int> sa(s.size());
    for (int i = 0; i < static_cast<int>(s.size()); ++i) sa[i] = i;
    std::sort(sa.begin(), sa.end(), [&](int a, int b) { return s.substr(a) < s.substr(b); });
    return sa;
}

std::vector<int> brute_lcp(const std::string& s, const std::vector<int>& sa) {
    std::vector<int> lcp;
    for (int i = 0; i + 1 < static_cast<int>(sa.size()); ++i) {
        int a = sa[i], b = sa[i + 1], h = 0;
        while (a + h < static_cast<int>(s.size()) && b + h < static_cast<int>(s.size()) && s[a + h] == s[b + h]) ++h;
        lcp.push_back(h);
    }
    return lcp;
}

void run_tests() {
    assert(suffix_array("").empty());
    assert(lcp_array("", {}).empty());
    std::string s = "banana";
    assert((suffix_array(s) == std::vector<int>{5, 3, 1, 0, 4, 2}));
    assert((lcp_array(s, suffix_array(s)) == std::vector<int>{1, 3, 0, 0, 2}));

    std::mt19937 rng(9);
    std::uniform_int_distribution<int> n_dist(1, 35);
    std::uniform_int_distribution<int> c_dist(0, 3);
    for (int round = 0; round < 500; ++round) {
        int n = n_dist(rng);
        std::string t;
        for (int i = 0; i < n; ++i) t.push_back(static_cast<char>('a' + c_dist(rng)));
        auto sa = suffix_array(t);
        assert(sa == brute_sa(t));
        assert(lcp_array(t, sa) == brute_lcp(t, sa));
    }
}

void run_demo() {
    std::string s = "banana";
    auto sa = suffix_array(s);
    auto lcp = lcp_array(s, sa);
    std::cout << "s=banana\nsa: ";
    for (int x : sa) std::cout << x << ' ';
    std::cout << "\nlcp: ";
    for (int x : lcp) std::cout << x << ' ';
    std::cout << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "suffix array/lcp tests passed\n";
        return 0;
    }
    run_demo();
}
