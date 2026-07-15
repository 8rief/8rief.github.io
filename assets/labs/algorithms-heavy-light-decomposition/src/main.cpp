#include <algorithm>
#include <cassert>
#include <iostream>
#include <memory>
#include <numeric>
#include <random>
#include <string>
#include <vector>

class SegmentTree {
public:
    explicit SegmentTree(const std::vector<int>& a) {
        n_ = 1;
        while (n_ < static_cast<int>(a.size())) n_ <<= 1;
        tree_.assign(2 * n_, 0);
        for (int i = 0; i < static_cast<int>(a.size()); ++i) tree_[n_ + i] = a[i];
        for (int i = n_ - 1; i > 0; --i) tree_[i] = tree_[2 * i] + tree_[2 * i + 1];
    }

    long long query(int l, int r) const {
        long long res = 0;
        for (l += n_, r += n_; l < r; l >>= 1, r >>= 1) {
            if (l & 1) res += tree_[l++];
            if (r & 1) res += tree_[--r];
        }
        return res;
    }

private:
    int n_ = 1;
    std::vector<long long> tree_;
};

class HLD {
public:
    HLD(const std::vector<std::vector<int>>& g, const std::vector<int>& values)
        : n_(static_cast<int>(g.size())), g_(g), values_(values), parent_(n_), depth_(n_), heavy_(n_, -1),
          size_(n_), head_(n_), pos_(n_) {
        dfs_size(0, 0);
        int cur = 0;
        decompose(0, 0, cur);
        std::vector<int> linear(n_);
        for (int v = 0; v < n_; ++v) linear[pos_[v]] = values_[v];
        seg_ = std::make_unique<SegmentTree>(linear);
    }

    long long path_sum(int a, int b) const {
        long long res = 0;
        while (head_[a] != head_[b]) {
            if (depth_[head_[a]] < depth_[head_[b]]) std::swap(a, b);
            res += seg_->query(pos_[head_[a]], pos_[a] + 1);
            a = parent_[head_[a]];
        }
        if (depth_[a] > depth_[b]) std::swap(a, b);
        res += seg_->query(pos_[a], pos_[b] + 1);
        return res;
    }

private:
    int n_;
    std::vector<std::vector<int>> g_;
    std::vector<int> values_, parent_, depth_, heavy_, size_, head_, pos_;
    std::unique_ptr<SegmentTree> seg_;

    int dfs_size(int u, int p) {
        parent_[u] = p;
        size_[u] = 1;
        int best = 0;
        for (int v : g_[u]) {
            if (v == p) continue;
            depth_[v] = depth_[u] + 1;
            int child = dfs_size(v, u);
            size_[u] += child;
            if (child > best) {
                best = child;
                heavy_[u] = v;
            }
        }
        return size_[u];
    }

    void decompose(int u, int h, int& cur) {
        head_[u] = h;
        pos_[u] = cur++;
        if (heavy_[u] != -1) decompose(heavy_[u], h, cur);
        for (int v : g_[u]) {
            if (v == parent_[u] || v == heavy_[u]) continue;
            decompose(v, v, cur);
        }
    }
};

long long naive_path_sum(int a, int b, const std::vector<int>& parent, const std::vector<int>& depth, const std::vector<int>& values) {
    long long sum = 0;
    int x = a, y = b;
    while (depth[x] > depth[y]) { sum += values[x]; x = parent[x]; }
    while (depth[y] > depth[x]) { sum += values[y]; y = parent[y]; }
    while (x != y) {
        sum += values[x] + values[y];
        x = parent[x];
        y = parent[y];
    }
    sum += values[x];
    return sum;
}

void run_tests() {
    int n = 8;
    std::vector<std::vector<int>> g(n);
    auto add = [&](int u, int v) { g[u].push_back(v); g[v].push_back(u); };
    add(0, 1); add(0, 2); add(1, 3); add(1, 4); add(2, 5); add(2, 6); add(4, 7);
    std::vector<int> values{1, 2, 3, 4, 5, 6, 7, 8};
    HLD hld(g, values);
    assert(hld.path_sum(3, 7) == 19);
    assert(hld.path_sum(5, 6) == 16);
    assert(hld.path_sum(0, 7) == 16);

    std::mt19937 rng(123);
    std::uniform_int_distribution<int> val_dist(-5, 10);
    for (int round = 0; round < 80; ++round) {
        int m = 5 + (round % 40);
        std::vector<std::vector<int>> tree(m);
        std::vector<int> parent(m), depth(m), vals(m);
        for (int i = 0; i < m; ++i) vals[i] = val_dist(rng);
        for (int v = 1; v < m; ++v) {
            std::uniform_int_distribution<int> p_dist(0, v - 1);
            int p = p_dist(rng);
            parent[v] = p;
            depth[v] = depth[p] + 1;
            tree[v].push_back(p);
            tree[p].push_back(v);
        }
        HLD check(tree, vals);
        std::uniform_int_distribution<int> node_dist(0, m - 1);
        for (int q = 0; q < 200; ++q) {
            int a = node_dist(rng), b = node_dist(rng);
            assert(check.path_sum(a, b) == naive_path_sum(a, b, parent, depth, vals));
        }
    }
}

void run_demo() {
    int n = 8;
    std::vector<std::vector<int>> g(n);
    auto add = [&](int u, int v) { g[u].push_back(v); g[v].push_back(u); };
    add(0, 1); add(0, 2); add(1, 3); add(1, 4); add(2, 5); add(2, 6); add(4, 7);
    std::vector<int> values{1, 2, 3, 4, 5, 6, 7, 8};
    HLD hld(g, values);
    std::cout << "path_sum(3,7)=" << hld.path_sum(3, 7) << "\n";
    std::cout << "path_sum(5,6)=" << hld.path_sum(5, 6) << "\n";
    std::cout << "path_sum(0,7)=" << hld.path_sum(0, 7) << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "heavy-light decomposition tests passed\n";
        return 0;
    }
    run_demo();
}
