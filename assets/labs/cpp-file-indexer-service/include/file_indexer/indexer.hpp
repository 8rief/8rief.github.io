#pragma once

#include <cstdint>
#include <filesystem>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

namespace file_indexer {

struct IndexerConfig {
    std::filesystem::path root;
    std::vector<std::string> extensions;
};

struct FileEntry {
    std::string path;
    std::uintmax_t bytes{};
    std::size_t lines{};
    std::size_t words{};
};

struct IndexSummary {
    std::size_t files{};
    std::uintmax_t bytes{};
    std::size_t lines{};
    std::size_t words{};
};

struct IndexResult {
    IndexSummary summary;
    std::vector<FileEntry> files;
};

IndexerConfig load_config(const std::filesystem::path& path);
IndexResult build_index(const IndexerConfig& config);
nlohmann::json to_json_value(const IndexResult& result);
void write_json_report(const std::filesystem::path& path, const IndexResult& result);
void write_csv_report(const std::filesystem::path& path, const IndexResult& result);

}  // namespace file_indexer
