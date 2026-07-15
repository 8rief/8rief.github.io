#include "file_indexer/indexer.hpp"

#include <CLI/CLI.hpp>
#include <httplib.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <spdlog/spdlog.h>

#include <exception>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>

namespace {

std::shared_ptr<spdlog::logger> make_logger(const std::filesystem::path& path) {
    if (!path.parent_path().empty()) {
        std::filesystem::create_directories(path.parent_path());
    }
    auto logger = spdlog::basic_logger_mt("file-indexer", path.string(), true);
    logger->set_pattern("%Y-%m-%dT%H:%M:%S%z [%l] %v");
    return logger;
}

int run_scan(const std::filesystem::path& config_path,
             const std::filesystem::path& json_path,
             const std::filesystem::path& csv_path,
             const std::filesystem::path& log_path) {
    auto logger = make_logger(log_path);
    auto config = file_indexer::load_config(config_path);
    logger->info("scan root={} json={} csv={}", config.root.string(), json_path.string(), csv_path.string());
    const auto result = file_indexer::build_index(config);
    file_indexer::write_json_report(json_path, result);
    file_indexer::write_csv_report(csv_path, result);
    logger->info("scan done files={} bytes={} lines={} words={}", result.summary.files, result.summary.bytes, result.summary.lines, result.summary.words);
    std::cout << "files=" << result.summary.files << " bytes=" << result.summary.bytes
              << " lines=" << result.summary.lines << " words=" << result.summary.words << '\n';
    return 0;
}

int run_serve(const std::filesystem::path& config_path,
              const std::filesystem::path& log_path,
              const std::string& host,
              int port) {
    auto logger = make_logger(log_path);
    auto config = file_indexer::load_config(config_path);
    auto result = std::make_shared<file_indexer::IndexResult>(file_indexer::build_index(config));
    httplib::Server server;
    server.Get("/health", [](const httplib::Request&, httplib::Response& response) {
        response.set_content(R"({"status":"ok"})", "application/json");
    });
    server.Get("/api/summary", [result](const httplib::Request&, httplib::Response& response) {
        response.set_content(file_indexer::to_json_value(*result).at("summary").dump(2), "application/json");
    });
    server.Get("/api/files", [result](const httplib::Request&, httplib::Response& response) {
        response.set_content(file_indexer::to_json_value(*result).at("files").dump(2), "application/json");
    });
    logger->info("listen host={} port={} files={}", host, port, result->summary.files);
    if (!server.listen(host, port)) {
        throw std::runtime_error("failed to listen on " + host + ':' + std::to_string(port));
    }
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    CLI::App app{"Local file indexer CLI and API"};
    std::filesystem::path config_path{"sample_config/indexer.json"};
    std::filesystem::path json_path{"reports/index.json"};
    std::filesystem::path csv_path{"reports/index.csv"};
    std::filesystem::path log_path{"reports/file-indexer.log"};
    std::string host{"127.0.0.1"};
    int port{18280};

    app.add_option("--config", config_path, "JSON config path")->capture_default_str();
    app.add_option("--log", log_path, "log file path")->capture_default_str();

    auto* scan = app.add_subcommand("scan", "scan local files and write reports");
    scan->add_option("--json", json_path, "JSON report path")->capture_default_str();
    scan->add_option("--csv", csv_path, "CSV report path")->capture_default_str();

    auto* serve = app.add_subcommand("serve", "serve reports through a local HTTP API");
    serve->add_option("--host", host, "listen host")->capture_default_str();
    serve->add_option("--port", port, "listen port")->capture_default_str();

    app.require_subcommand(1);
    CLI11_PARSE(app, argc, argv);

    try {
        if (*scan) {
            return run_scan(config_path, json_path, csv_path, log_path);
        }
        if (*serve) {
            return run_serve(config_path, log_path, host, port);
        }
    } catch (const std::exception& error) {
        std::cerr << "error: " << error.what() << '\n';
        return 1;
    }
    return 0;
}
