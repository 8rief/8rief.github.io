#include "file_indexer/indexer.hpp"

#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <fstream>

namespace {
std::filesystem::path fixture_root() {
    return std::filesystem::path{CMAKE_SOURCE_DIR} / "sample_data" / "docs";
}
}

TEST_CASE("build_index summarizes sample files") {
    file_indexer::IndexerConfig config{fixture_root(), {".txt", ".md"}};
    const auto result = file_indexer::build_index(config);
    REQUIRE(result.summary.files == 3);
    REQUIRE(result.summary.lines == 7);
    REQUIRE(result.summary.words >= 40);
    REQUIRE(result.files.front().path == "intro.txt");
}

TEST_CASE("json report contains summary and files") {
    file_indexer::IndexerConfig config{fixture_root(), {".txt"}};
    const auto result = file_indexer::build_index(config);
    const auto value = file_indexer::to_json_value(result);
    REQUIRE(value.at("summary").at("files").get<std::size_t>() == 2);
    REQUIRE(value.at("files").is_array());
}

TEST_CASE("write reports creates JSON and CSV files") {
    const auto temp = std::filesystem::temp_directory_path() / "cpp-file-indexer-test-report";
    std::filesystem::remove_all(temp);
    file_indexer::IndexerConfig config{fixture_root(), {".md"}};
    const auto result = file_indexer::build_index(config);
    const auto json_path = temp / "index.json";
    const auto csv_path = temp / "index.csv";
    file_indexer::write_json_report(json_path, result);
    file_indexer::write_csv_report(csv_path, result);
    REQUIRE(std::filesystem::exists(json_path));
    REQUIRE(std::filesystem::exists(csv_path));
    std::ifstream csv(csv_path);
    std::string header;
    std::getline(csv, header);
    REQUIRE(header == "path,bytes,lines,words");
    std::filesystem::remove_all(temp);
}
