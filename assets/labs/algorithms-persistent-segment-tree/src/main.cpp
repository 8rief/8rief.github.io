#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

class PersistentSegmentTree {
public:
    explicit PersistentSegmentTree(const std::vector<int>& a) : n_(static_cast<int>(a.size())) {
        nodes_.reserve(n_ * 40);
        roots_.push_back(build(0, n_, a));
    }

    int update(int version, int index, int value) {
        int root = update_node(roots_.at(version), 0, n_, index, value);
        roots_.push_back(root);
        return static_cast<int>(roots_.size()) - 1;
    }

    long long query(int version, int l, int r) const {
        return query_node(roots_.at(version), 0, n_, l, r);
    }

    int versions() const { return static_cast<int>(roots_.size()); }
    int node_count() const { return static_cast<int>(nodes_.size()); }

private:
    struct Node { int left = -1, right = -1; long long sum = 0; };
    int n_;
    std::vector<Node> nodes_;
    std::vector<int> roots_;

    int new_node(Node node) {
        nodes_.push_back(node);
        return static_cast<int>(nodes_.size()) - 1;
    }

    int build(int l, int r, const std::vector<int>& a) {
        if (r - l == 1) return new_node(Node{-1, -1, a[l]});
        int m = (l + r) / 2;
        int left = build(l, m, a);
        int right = build(m, r, a);
        return new_node(Node{left, right, nodes_[left].sum + nodes_[right].sum});
    }

    int update_node(int id, int l, int r, int index, int value) {
        Node cur = nodes_[id];
        if (r - l == 1) {
            cur.sum = value;
            return new_node(cur);
        }
        int m = (l + r) / 2;
        if (index < m) cur.left = update_node(cur.left, l, m, index, value);
        else cur.right = update_node(cur.right, m, r, index, value);
        cur.sum = nodes_[cur.left].sum + nodes_[cur.right].sum;
        return new_node(cur);
    }

    long long query_node(int id, int l, int r, int ql, int qr) const {
        if (qr <= l || r <= ql) return 0;
        if (ql <= l && r <= qr) return nodes_[id].sum;
        int m = (l + r) / 2;
        return query_node(nodes_[id].left, l, m, ql, qr)
             + query_node(nodes_[id].right, m, r, ql, qr);
    }
};

long long naive_sum(const std::vector<int>& a, int l, int r) {
    return std::accumulate(a.begin() + l, a.begin() + r, 0LL);
}

void run_tests() {
    std::vector<int> a{1, 2, 3, 4, 5};
    PersistentSegmentTree pst(a);
    int v1 = pst.update(0, 2, 10);
    int v2 = pst.update(v1, 0, -1);
    assert(pst.query(0, 0, 5) == 15);
    assert(pst.query(v1, 0, 5) == 22);
    assert(pst.query(v2, 0, 3) == 11);
    assert(pst.query(0, 0, 3) == 6);

    std::mt19937 rng(7);
    std::uniform_int_distribution<int> value_dist(-20, 20);
    std::vector<int> base(30);
    for (int& x : base) x = value_dist(rng);
    PersistentSegmentTree random_pst(base);
    std::vector<std::vector<int>> versions{base};
    std::uniform_int_distribution<int> index_dist(0, 29);
    for (int round = 0; round < 200; ++round) {
        std::uniform_int_distribution<int> version_dist(0, static_cast<int>(versions.size()) - 1);
        int parent = version_dist(rng);
        int index = index_dist(rng);
        int value = value_dist(rng);
        auto next = versions[parent];
        next[index] = value;
        int new_version = random_pst.update(parent, index, value);
        versions.push_back(next);
        assert(new_version == static_cast<int>(versions.size()) - 1);
        for (int check = 0; check < 5; ++check) {
            int v = version_dist(rng) % static_cast<int>(versions.size());
            int l = index_dist(rng), r = index_dist(rng);
            if (l > r) std::swap(l, r);
            ++r;
            assert(random_pst.query(v, l, r) == naive_sum(versions[v], l, r));
        }
    }
}

void run_demo() {
    std::vector<int> a{1, 2, 3, 4, 5};
    PersistentSegmentTree pst(a);
    int v1 = pst.update(0, 2, 10);
    int v2 = pst.update(v1, 0, -1);
    std::cout << "version0 sum[0,5)=" << pst.query(0, 0, 5) << "\n";
    std::cout << "version1 set a[2]=10, sum[0,5)=" << pst.query(v1, 0, 5) << "\n";
    std::cout << "version2 set a[0]=-1, sum[0,3)=" << pst.query(v2, 0, 3) << "\n";
    std::cout << "stored versions=" << pst.versions() << " nodes=" << pst.node_count() << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "persistent segment tree tests passed\n";
        return 0;
    }
    run_demo();
}
