#include <algorithm>
#include <cassert>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>

const long long INF = std::numeric_limits<long long>::max() / 4;

struct Line {
    long long m = 0, b = INF;
    long long eval(long long x) const { return m * x + b; }
};

class LiChaoTree {
public:
    LiChaoTree(long long lo, long long hi) : lo_(lo), hi_(hi) {
        nodes_.push_back(Node{});
    }

    void add_line(Line line) { add_line(0, lo_, hi_, line); }

    long long query(long long x) const { return query(0, lo_, hi_, x); }

private:
    struct Node { Line line; int left = -1, right = -1; bool has = false; };
    long long lo_, hi_;
    std::vector<Node> nodes_;

    int new_node() {
        nodes_.push_back(Node{});
        return static_cast<int>(nodes_.size()) - 1;
    }

    void add_line(int id, long long l, long long r, Line nw) {
        if (!nodes_[id].has) {
            nodes_[id].line = nw;
            nodes_[id].has = true;
            return;
        }
        long long mid = (l + r) / 2;
        Line& cur = nodes_[id].line;
        bool left_better = nw.eval(l) < cur.eval(l);
        bool mid_better = nw.eval(mid) < cur.eval(mid);
        if (mid_better) std::swap(nw, cur);
        if (r - l == 1) return;
        if (left_better != mid_better) {
            if (nodes_[id].left == -1) nodes_[id].left = new_node();
            add_line(nodes_[id].left, l, mid, nw);
        } else {
            if (nodes_[id].right == -1) nodes_[id].right = new_node();
            add_line(nodes_[id].right, mid, r, nw);
        }
    }

    long long query(int id, long long l, long long r, long long x) const {
        long long best = nodes_[id].has ? nodes_[id].line.eval(x) : INF;
        if (r - l == 1) return best;
        long long mid = (l + r) / 2;
        int child = x < mid ? nodes_[id].left : nodes_[id].right;
        if (child == -1) return best;
        if (x < mid) return std::min(best, query(child, l, mid, x));
        return std::min(best, query(child, mid, r, x));
    }
};

long long brute_query(const std::vector<Line>& lines, long long x) {
    long long best = INF;
    for (auto line : lines) best = std::min(best, line.eval(x));
    return best;
}

void run_tests() {
    std::vector<Line> lines{{1, 0}, {-1, 5}, {2, -3}};
    LiChaoTree tree(-10, 11);
    for (auto line : lines) tree.add_line(line);
    for (int x = -10; x <= 10; ++x) assert(tree.query(x) == brute_query(lines, x));

    std::mt19937 rng(99);
    std::uniform_int_distribution<int> coef_dist(-20, 20);
    for (int round = 0; round < 100; ++round) {
        LiChaoTree random_tree(-50, 51);
        std::vector<Line> random_lines;
        for (int i = 0; i < 80; ++i) {
            Line line{coef_dist(rng), coef_dist(rng)};
            random_lines.push_back(line);
            random_tree.add_line(line);
            for (int x = -50; x <= 50; x += 5) {
                assert(random_tree.query(x) == brute_query(random_lines, x));
            }
        }
    }
}

void run_demo() {
    std::vector<Line> lines{{1, 0}, {-1, 5}, {2, -3}};
    LiChaoTree tree(-10, 11);
    for (auto line : lines) tree.add_line(line);
    for (int x : {-5, 0, 3, 10}) {
        std::cout << "min at x=" << x << " -> " << tree.query(x) << "\n";
    }
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "li chao tree tests passed\n";
        return 0;
    }
    run_demo();
}
