#pragma once
#include <chrono>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace buglab {

struct ParseResult {
    std::vector<int> values;
    std::vector<std::string> errors;
};

ParseResult parse_positive_ints(const std::vector<std::string>& tokens);
double running_mean(const std::vector<int>& values);
std::optional<int> first_value_above(const std::vector<int>& values, int threshold);
std::vector<int> shrink_to_failing_case(const std::vector<int>& values, int threshold);
std::string diagnostic_line(std::string_view level, std::string_view component, std::string_view message);
std::uint64_t checksum_workload(int rounds);
long long timed_checksum_ms(int rounds);
int unsafe_index_demo();
int signed_overflow_demo();

}  // namespace buglab
