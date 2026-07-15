#include "debug_lab.hpp"

#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Harness {
    int passed = 0;
    void truth(bool condition, const std::string& name) {
        if (!condition) throw std::runtime_error("FAILED: " + name);
        ++passed;
    }
    template <class T, class U>
    void equal(const T& actual, const U& expected, const std::string& name) {
        if (!(actual == expected)) throw std::runtime_error("FAILED: " + name);
        ++passed;
    }
};

}  // namespace

int main() {
    Harness test;
    const auto parsed = buglab::parse_positive_ints({"10", "-2", "abc", "5"});
    test.equal(parsed.values.size(), static_cast<std::size_t>(2), "parse keeps two positive ints");
    test.equal(parsed.errors.size(), static_cast<std::size_t>(2), "parse records two errors");
    test.truth(std::abs(buglab::running_mean(parsed.values) - 7.5) < 1e-9, "running mean of parsed values");

    bool threw = false;
    try {
        (void)buglab::running_mean({});
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    test.truth(threw, "running_mean rejects empty input");

    const auto shrunk = buglab::shrink_to_failing_case({1, 2, 50, 3, 80}, 40);
    test.equal(shrunk.size(), static_cast<std::size_t>(1), "shrinker finds one-value repro");
    test.truth(shrunk.front() > 40, "shrunk value still triggers predicate");

    const auto line = buglab::diagnostic_line("warn", "parser", "bad token");
    test.truth(line.find("level=warn") != std::string::npos, "log line has level");
    test.truth(line.find("component=parser") != std::string::npos, "log line has component");

    test.truth(buglab::checksum_workload(1000) == buglab::checksum_workload(1000), "checksum is deterministic");
    test.truth(buglab::timed_checksum_ms(1000) >= 0, "timing is non-negative");

    std::cout << "tests_passed=" << test.passed << "\n";
    std::cout << "parsed_values=" << parsed.values.size() << " parse_errors=" << parsed.errors.size() << "\n";
    std::cout << "shrunk_size=" << shrunk.size() << " trigger=" << shrunk.front() << "\n";
    return 0;
}
