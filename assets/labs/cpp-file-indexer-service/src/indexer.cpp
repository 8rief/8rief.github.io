#include "file_indexer/indexer.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <iterator>
#include <set>
#include <sstream>
#include <stdexcept>

namespace file_indexer {
namespace {

void ensure_parent(const std::filesystem::path& path) {
    if (const auto parent = path.parent_path(); !parent.empty()) {
        std::filesystem::create_directories(parent);
    }
}

std::set<std::string> normalized_extensions(const std::vector<std::string>& extensions) {
    std::set<std::string> result;
    for (auto extension : extensions) {
        if (extension.empty()) {
            continue;
        }
        if (extension.front() != '.') {
            extension.insert(extension.begin(), '.');
        }
        std::ranges::transform(extension, extension.begin(), [](unsigned char ch) {
            return static_cast<char>(std::tolower(ch));
        });
        result.insert(extension);
    }
    return result;
}

bool has_allowed_extension(const std::filesystem::path& path, const std::set<std::string>& allowed) {
    if (allowed.empty()) {
        return true;
    }
    auto ext = path.extension().string();
    std::ranges::transform(ext, ext.begin(), [](unsigned char ch) {
        return static_cast<char>(std::tolower(ch));
    });
    return allowed.contains(ext);
}

FileEntry inspect_file(const std::filesystem::path& root, const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("failed to open " + path.string());
    }
    FileEntry entry;
    entry.path = std::filesystem::relative(path, root).generic_string();
    entry.bytes = std::filesystem::file_size(path);
    std::string line;
    while (std::getline(input, line)) {
        ++entry.lines;
        std::istringstream words(line);
        entry.words += static_cast<std::size_t>(std::distance(std::istream_iterator<std::string>{words}, std::istream_iterator<std::string>{}));
    }
    return entry;
}

}  // namespace

IndexerConfig load_config(const std::filesystem::path& path) {
    std::ifstream input(path);
    if (!input) {
        throw std::runtime_error("failed to read config " + path.string());
    }
    nlohmann::json value;
    input >> value;
    IndexerConfig config;
    config.root = value.at("root").get<std::string>();
    config.extensions = value.value("extensions", std::vector<std::string>{});
    if (config.root.empty()) {
        throw std::runtime_error("config root must not be empty");
    }
    return config;
}

IndexResult build_index(const IndexerConfig& config) {
    if (!std::filesystem::exists(config.root)) {
        throw std::runtime_error("root does not exist: " + config.root.string());
    }
    const auto allowed = normalized_extensions(config.extensions);
    IndexResult result;
    for (const auto& item : std::filesystem::recursive_directory_iterator(config.root)) {
        if (!item.is_regular_file() || !has_allowed_extension(item.path(), allowed)) {
            continue;
        }
        result.files.push_back(inspect_file(config.root, item.path()));
    }
    std::ranges::sort(result.files, {}, &FileEntry::path);
    for (const auto& entry : result.files) {
        ++result.summary.files;
        result.summary.bytes += entry.bytes;
        result.summary.lines += entry.lines;
        result.summary.words += entry.words;
    }
    return result;
}

nlohmann::json to_json_value(const IndexResult& result) {
    nlohmann::json files = nlohmann::json::array();
    for (const auto& entry : result.files) {
        files.push_back({
            {"path", entry.path},
            {"bytes", entry.bytes},
            {"lines", entry.lines},
            {"words", entry.words},
        });
    }
    return {
        {"summary", {
            {"files", result.summary.files},
            {"bytes", result.summary.bytes},
            {"lines", result.summary.lines},
            {"words", result.summary.words},
        }},
        {"files", files},
    };
}

void write_json_report(const std::filesystem::path& path, const IndexResult& result) {
    ensure_parent(path);
    std::ofstream output(path);
    if (!output) {
        throw std::runtime_error("failed to write JSON report " + path.string());
    }
    output << to_json_value(result).dump(2) << '\n';
}

void write_csv_report(const std::filesystem::path& path, const IndexResult& result) {
    ensure_parent(path);
    std::ofstream output(path);
    if (!output) {
        throw std::runtime_error("failed to write CSV report " + path.string());
    }
    output << "path,bytes,lines,words\n";
    for (const auto& entry : result.files) {
        output << entry.path << ',' << entry.bytes << ',' << entry.lines << ',' << entry.words << '\n';
    }
}

}  // namespace file_indexer
