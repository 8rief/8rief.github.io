#include "debug_lab.hpp"

#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

int parse_rounds(const std::string& text) {
    try {
        return std::stoi(text);
    } catch (const std::exception&) {
        throw std::invalid_argument("rounds must be an integer");
    }
}

}  // namespace

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "usage: debug_lab_cli <parse|shrink|log|timing|unsafe-index|ubsan-overflow> [args]\n";
        return 2;
    }
    const std::string command = argv[1];
    try {
        if (command == "parse") {
            std::vector<std::string> tokens;
            for (int i = 2; i < argc; ++i) tokens.emplace_back(argv[i]);
            const auto parsed = buglab::parse_positive_ints(tokens);
            std::cout << "values=" << parsed.values.size() << " errors=" << parsed.errors.size() << "\n";
            std::cout << "mean=" << buglab::running_mean(parsed.values) << "\n";
            return parsed.errors.empty() ? 0 : 1;
        }
        if (command == "shrink") {
            std::vector<int> values{1, 2, 50, 3, 4, 80, 5};
            const auto shrunk = buglab::shrink_to_failing_case(values, 40);
            std::cout << "original_size=" << values.size() << " shrunk_size=" << shrunk.size() << " trigger=" << shrunk.front() << "\n";
            return 0;
        }
        if (command == "log") {
            std::cout << buglab::diagnostic_line("info", "parser", "accepted input batch") << "\n";
            std::cout << buglab::diagnostic_line("warn", "parser", "rejected non-positive token") << "\n";
            return 0;
        }
        if (command == "timing") {
            const int rounds = argc >= 3 ? parse_rounds(argv[2]) : 200000;
            std::cout << "rounds=" << rounds << " checksum=" << buglab::checksum_workload(rounds)
                      << " measured_ms=" << buglab::timed_checksum_ms(rounds) << "\n";
            return 0;
        }
        if (command == "unsafe-index") {
            std::cout << buglab::unsafe_index_demo() << "\n";
            return 0;
        }
        if (command == "ubsan-overflow") {
            std::cout << buglab::signed_overflow_demo() << "\n";
            return 0;
        }
        std::cerr << "unknown command: " << command << "\n";
        return 2;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }
}
