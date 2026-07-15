#include <algorithm>
#include <cassert>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

int quickselect(std::vector<int> a, int k, std::mt19937& rng) {
    if (k < 0 || k >= static_cast<int>(a.size())) throw std::out_of_range("k");
    int lo = 0, hi = static_cast<int>(a.size());
    while (true) {
        std::uniform_int_distribution<int> pick(lo, hi - 1);
        int pivot = a[pick(rng)];
        int lt = lo, i = lo, gt = hi;
        while (i < gt) {
            if (a[i] < pivot) std::swap(a[lt++], a[i++]);
            else if (a[i] > pivot) std::swap(a[i], a[--gt]);
            else ++i;
        }
        if (k < lt) hi = lt;
        else if (k >= gt) lo = gt;
        else return pivot;
    }
}

int sorted_kth(std::vector<int> a, int k) {
    std::sort(a.begin(), a.end());
    return a[k];
}

void run_tests() {
    std::mt19937 rng(12345);
    std::vector<int> fixed{9, 1, 5, 7, 3, 3, 8};
    assert(quickselect(fixed, 0, rng) == 1);
    assert(quickselect(fixed, 3, rng) == 5);
    assert(quickselect(fixed, 6, rng) == 9);
    std::vector<int> equal(50, 42);
    assert(quickselect(equal, 25, rng) == 42);

    std::uniform_int_distribution<int> n_dist(1, 120);
    std::uniform_int_distribution<int> value_dist(-50, 50);
    for (int round = 0; round < 500; ++round) {
        int n = n_dist(rng);
        std::vector<int> a(n);
        for (int& x : a) x = value_dist(rng);
        std::uniform_int_distribution<int> k_dist(0, n - 1);
        int k = k_dist(rng);
        assert(quickselect(a, k, rng) == sorted_kth(a, k));
    }
}

void run_demo() {
    std::mt19937 rng(20260625);
    std::vector<int> a{9, 1, 5, 7, 3, 3, 8};
    int k = 3;
    std::cout << "array: ";
    for (int x : a) std::cout << x << ' ';
    std::cout << "\n";
    std::cout << "k=" << k << " zero-based -> kth value=" << quickselect(a, k, rng) << "\n";
    std::sort(a.begin(), a.end());
    std::cout << "sorted check: ";
    for (int x : a) std::cout << x << ' ';
    std::cout << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "randomized quickselect tests passed\n";
        return 0;
    }
    run_demo();
}
