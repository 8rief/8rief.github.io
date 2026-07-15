---
layout: post
title: "C++ spdlog 和 cpp-httplib：把索引结果发布成本地 API"
date: 2026-05-17 18:00:00 +0800
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

## 为什么需要日志和本地 API

CLI 报告适合一次性生成文件，服务接口适合让浏览器、脚本或前端按需读取结果。把同一个索引结果发布为 HTTP API，可以展示 C++ 项目从库、命令行工具到本地服务的完整形态。

服务化会带来新的可观测性需求。进程启动后不一定立刻有终端输出，用户需要通过日志确认扫描了哪个目录、生成了多少文件、API 监听在哪里。spdlog 负责把这些关键状态写成时间戳和字段；cpp-httplib 负责把只读结果暴露成简单端点。

默认绑定 `127.0.0.1` 是交付边界的一部分。教学项目先证明本机交互，不把端口暴露给局域网。等需要真实部署时，再单独讨论认证、反向代理、TLS、限流和日志脱敏。


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

## 输出怎么读

日志输出先确认扫描边界：

```text
[info] scan root=sample_data/docs json=reports/index.json csv=reports/index.csv
[info] scan done files=3 bytes=304 lines=7 words=45
```

第一行告诉你输入目录和两个报告路径，第二行告诉你核心统计结果。两行合在一起，才能把“扫了什么”和“得到什么”对应起来。

API smoke 输出确认服务边界：

```text
http://127.0.0.1:18280/health 200
http://127.0.0.1:18280/api/summary 200
http://127.0.0.1:18280/api/files 200
```

`/health` 只证明进程活着；`/api/summary` 证明聚合结果可读；`/api/files` 证明明细数组可读。三者都返回 200，才说明服务层和数据层都可用。

如果 `/health` 成功但 `/api/summary` 失败，先检查启动时是否成功扫描和加载结果。如果所有请求都连接失败，先检查 host、port、进程生命周期和是否被旧进程占用端口。


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
