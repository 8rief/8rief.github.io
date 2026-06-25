---
layout: post
title: "C++ spdlog 和 cpp-httplib：把索引结果发布成本地 API"
date: 2026-06-25 21:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, spdlog, httplib, api, teaching]
---

## 学习目标

这一篇把 C++ 核心逻辑服务化。读完以后，你应该能说明：

1. spdlog 如何记录输入、输出和汇总结果；
2. cpp-httplib 如何暴露 `/health`、`/api/summary`、`/api/files`；
3. 为什么教学 API 默认绑定 `127.0.0.1`。

## 先修知识

需要知道 HTTP server 是长时间运行的进程。服务一旦监听非本机地址，就可能被局域网其他机器访问，所以入门项目先限制在 loopback。

## 核心模型

服务入口先扫描一次目录，把结果放进共享对象，然后每个 HTTP handler 只读结果。

![C++ spdlog httplib API](/assets/diagrams/cpp-spdlog-httplib-local-api.svg)

CLI scan 和 HTTP serve 都使用同一个 `build_index`。差异只在输出边界：scan 写文件，serve 返回 HTTP JSON。

## 逐步实现

日志初始化：

```cpp
auto logger = spdlog::basic_logger_mt("file-indexer", path.string(), true);
logger->set_pattern("%Y-%m-%dT%H:%M:%S%z [%l] %v");
```

scan 命令写日志：

```cpp
logger->info("scan root={} json={} csv={}", config.root.string(), json_path.string(), csv_path.string());
logger->info("scan done files={} bytes={} lines={} words={}",
             result.summary.files, result.summary.bytes, result.summary.lines, result.summary.words);
```

实验日志片段：

```text
[info] scan root=sample_data/docs json=reports/index.json csv=reports/index.csv
[info] scan done files=3 bytes=304 lines=7 words=45
```

HTTP API 使用 cpp-httplib：

```cpp
httplib::Server server;
server.Get("/health", [](const httplib::Request&, httplib::Response& response) {
    response.set_content(R"({"status":"ok"})", "application/json");
});
```

API smoke 覆盖三个端点：

```text
http://127.0.0.1:18280/health 200
http://127.0.0.1:18280/api/summary 200
http://127.0.0.1:18280/api/files 200
```

`/api/summary` 返回：

```json
{
  "bytes": 304,
  "files": 3,
  "lines": 7,
  "words": 45
}
```

## 常见错误

1. **handler 每次请求都重新扫描目录**：入门 API 先用启动时快照，行为更稳定。
2. **默认监听所有地址**：教学项目先绑定 `127.0.0.1`，避免误暴露。
3. **日志没有字段**：只写“scan done”不够，文件数、字节数、路径都应进入日志。

## 练习或延伸

- 增加 `/api/files?ext=.txt` 过滤接口，说明 query 参数如何进入核心筛选逻辑。
- 给服务加入 `/api/report.json`，直接返回完整 `to_json_value`。

## 参考资料

- [spdlog](https://github.com/gabime/spdlog)
- [cpp-httplib](https://github.com/yhirose/cpp-httplib)
- [HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
