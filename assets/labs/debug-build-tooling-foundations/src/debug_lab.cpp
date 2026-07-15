#include "debug_lab.hpp"

#include <algorithm>
#include <chrono>
#include <charconv>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>

namespace buglab {

ParseResult parse_positive_ints(const std::vector<std::string>& tokens) {
    ParseResult result;
    for (const std::string& token : tokens) {
        int value = 0;
        const char* begin = token.data();
        const char* end = token.data() + token.size();
        auto [ptr, ec] = std::from_chars(begin, end, value);
        if (ec != std::errc{} || ptr != end) {
            result.errors.push_back("not an integer: " + token);
            continue;
        }
        if (value <= 0) {
            result.errors.push_back("not positive: " + token);
            continue;
        }
        result.values.push_back(value);
    }
    return result;
}

double running_mean(const std::vector<int>& values) {
    if (values.empty()) {
        throw std::invalid_argument("running_mean requires at least one value");
    }
    const long long sum = std::accumulate(values.begin(), values.end(), 0LL);
    return static_cast<double>(sum) / static_cast<double>(values.size());
}

std::optional<int> first_value_above(const std::vector<int>& values, int threshold) {
    auto it = std::find_if(values.begin(), values.end(), [&](int value) { return value > threshold; });
    if (it == values.end()) return std::nullopt;
    return *it;
}

std::vector<int> shrink_to_failing_case(const std::vector<int>& values, int threshold) {
    std::vector<int> candidate = values;
    bool changed = true;
    while (changed && candidate.size() > 1) {
        changed = false;
        for (std::size_t i = 0; i < candidate.size(); ++i) {
            std::vector<int> trial = candidate;
            trial.erase(trial.begin() + static_cast<std::ptrdiff_t>(i));
            if (first_value_above(trial, threshold).has_value()) {
                candidate = std::move(trial);
                changed = true;
                break;
            }
        }
    }
    return candidate;
}

std::string diagnostic_line(std::string_view level, std::string_view component, std::string_view message) {
    std::ostringstream out;
    out << "level=" << level << " component=" << component << " message=\"" << message << "\"";
    return out.str();
}

std::uint64_t checksum_workload(int rounds) {
    if (rounds < 0) {
        throw std::invalid_argument("rounds must be non-negative");
    }
    std::uint64_t state = 1469598103934665603ULL;
    for (int i = 0; i < rounds; ++i) {
        state ^= static_cast<std::uint64_t>(i * 2654435761U);
        state *= 1099511628211ULL;
        state ^= state >> 32;
    }
    return state;
}

long long timed_checksum_ms(int rounds) {
    const auto start = std::chrono::steady_clock::now();
    volatile std::uint64_t sink = checksum_workload(rounds);
    (void)sink;
    const auto stop = std::chrono::steady_clock::now();
    return std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();
}

int unsafe_index_demo() {
    std::vector<int> values{1, 2, 3};
    return values[3];
}

int signed_overflow_demo() {
    int value = std::numeric_limits<int>::max();
    return value + 1;
}

}  // namespace buglab
