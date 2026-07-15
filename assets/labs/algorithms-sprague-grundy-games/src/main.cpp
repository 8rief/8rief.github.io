#include <algorithm>
#include <cassert>
#include <iostream>
#include <numeric>
#include <string>
#include <vector>

int mex(std::vector<int> values) {
    std::sort(values.begin(), values.end());
    int g = 0;
    for (int x : values) {
        if (x == g) ++g;
        else if (x > g) break;
    }
    return g;
}

std::vector<int> subtraction_grundy(int n, const std::vector<int>& moves) {
    std::vector<int> sg(n + 1);
    for (int heap = 1; heap <= n; ++heap) {
        std::vector<int> reachable;
        for (int move : moves) if (heap >= move) reachable.push_back(sg[heap - move]);
        sg[heap] = mex(reachable);
    }
    return sg;
}

bool naive_single_win(int n, const std::vector<int>& moves) {
    std::vector<int> win(n + 1);
    for (int heap = 1; heap <= n; ++heap) {
        for (int move : moves) {
            if (heap >= move && !win[heap - move]) win[heap] = 1;
        }
    }
    return win[n];
}

bool naive_two_heap_win(int a, int b, const std::vector<int>& moves) {
    std::vector<std::vector<int>> win(a + 1, std::vector<int>(b + 1));
    for (int i = 0; i <= a; ++i) {
        for (int j = 0; j <= b; ++j) {
            for (int move : moves) {
                if (i >= move && !win[i - move][j]) win[i][j] = 1;
                if (j >= move && !win[i][j - move]) win[i][j] = 1;
            }
        }
    }
    return win[a][b];
}

int xor_sum(const std::vector<int>& heaps, const std::vector<int>& sg) {
    int x = 0;
    for (int heap : heaps) x ^= sg[heap];
    return x;
}

void run_tests() {
    auto one = subtraction_grundy(40, {1});
    for (int i = 0; i <= 40; ++i) assert(one[i] == i % 2);
    auto three = subtraction_grundy(40, {1, 2, 3});
    for (int i = 0; i <= 40; ++i) assert(three[i] == i % 4);

    std::vector<int> moves{1, 3, 4};
    auto sg = subtraction_grundy(50, moves);
    for (int i = 0; i <= 50; ++i) assert((sg[i] != 0) == naive_single_win(i, moves));
    for (int a = 0; a <= 12; ++a) {
        for (int b = 0; b <= 12; ++b) {
            assert(((sg[a] ^ sg[b]) != 0) == naive_two_heap_win(a, b, moves));
        }
    }
}

void run_demo() {
    std::vector<int> moves{1, 3, 4};
    auto sg = subtraction_grundy(20, moves);
    std::cout << "moves: 1 3 4\nsg[0..10]: ";
    for (int i = 0; i <= 10; ++i) std::cout << sg[i] << ' ';
    std::vector<int> heaps{7, 10, 12};
    int x = xor_sum(heaps, sg);
    std::cout << "\nheaps 7 10 12 xor=" << x << " -> " << (x ? "winning" : "losing") << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "sprague-grundy tests passed\n";
        return 0;
    }
    run_demo();
}
