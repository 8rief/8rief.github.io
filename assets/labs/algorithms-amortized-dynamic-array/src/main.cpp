#include <algorithm>
#include <cassert>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <vector>

class AmortizedArray {
public:
    void push_back(int value) {
        if (size_ == static_cast<int>(storage_.size())) {
            grow();
        }
        storage_[size_++] = value;
        ++writes_;
    }

    int at(int index) const {
        if (index < 0 || index >= size_) throw std::out_of_range("index");
        return storage_[index];
    }

    int size() const { return size_; }
    int capacity() const { return static_cast<int>(storage_.size()); }
    long long copied() const { return copied_; }
    long long writes() const { return writes_; }
    long long total_work() const { return copied_ + writes_; }
    const std::vector<int>& capacity_trace() const { return capacity_trace_; }

private:
    std::vector<int> storage_;
    int size_ = 0;
    long long copied_ = 0;
    long long writes_ = 0;
    std::vector<int> capacity_trace_;

    void grow() {
        int new_capacity = storage_.empty() ? 1 : static_cast<int>(storage_.size()) * 2;
        std::vector<int> next(new_capacity);
        for (int i = 0; i < size_; ++i) {
            next[i] = storage_[i];
            ++copied_;
        }
        storage_ = std::move(next);
        capacity_trace_.push_back(new_capacity);
    }
};

bool is_power_of_two(int x) {
    return x > 0 && (x & (x - 1)) == 0;
}

void run_tests() {
    AmortizedArray a;
    for (int i = 0; i < 1000; ++i) a.push_back(i * i);
    assert(a.size() == 1000);
    for (int i = 0; i < a.size(); ++i) assert(a.at(i) == i * i);
    assert(a.copied() < 2LL * a.size());
    assert(a.total_work() < 3LL * a.size());
    for (int cap : a.capacity_trace()) assert(is_power_of_two(cap));

    AmortizedArray b;
    for (int i = 0; i < 17; ++i) b.push_back(i);
    assert((b.capacity_trace() == std::vector<int>{1, 2, 4, 8, 16, 32}));
    assert(b.copied() == 31);
    assert(b.writes() == 17);
}

void run_demo() {
    AmortizedArray a;
    for (int i = 0; i < 20; ++i) a.push_back(i);
    double average = static_cast<double>(a.total_work()) / a.size();
    std::cout << "after 20 pushes: size=" << a.size()
              << " capacity=" << a.capacity()
              << " copied=" << a.copied()
              << " writes=" << a.writes() << "\n";
    std::cout << "total work=" << a.total_work()
              << " average work per push=" << std::fixed << std::setprecision(2)
              << average << "\n";
    std::cout << "capacity growth: ";
    for (int cap : a.capacity_trace()) std::cout << cap << ' ';
    std::cout << "\n";
}

int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "--test") {
        run_tests();
        std::cout << "amortized dynamic-array tests passed\n";
        return 0;
    }
    run_demo();
}
