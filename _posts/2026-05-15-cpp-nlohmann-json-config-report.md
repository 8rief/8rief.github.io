---
layout: post
title: "C++ nlohmann/json：配置输入和结构化报告输出"
date: 2026-05-15 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, json, nlohmann-json, teaching]
---

## 学习目标

这一篇处理 JSON 边界。读完以后，你应该能做到：

1. 用 nlohmann/json 读取项目配置；
2. 把 C++ 结构体转换成稳定 JSON 报告；
3. 区分配置文件、汇总报告和 API JSON 的职责。

## 先修知识

需要知道 JSON 对象、数组和字符串的基本形式。C++ 里 JSON 库负责解析文本，但字段含义仍然要由项目代码验证。

## 为什么需要 JSON 边界

项目一旦有配置和报告，就需要一个稳定的数据格式。命令行参数适合临时覆盖，JSON 适合保存结构化输入和结构化输出。这个文件索引器用 JSON 解决两个不同问题。

1. **配置输入**：告诉程序扫描哪个目录、接受哪些扩展名。
2. **报告输出**：把 summary 和 files 明细写成可被脚本、API 或前端继续处理的数据。

这两个方向的信任边界不同。配置来自外部文件，字段可能缺失、类型可能错误、路径可能不存在，所以读取时要把 JSON 文本转换成经过验证的 `IndexerConfig`。报告来自程序内部结构体，重点是字段稳定、类型清楚、输出顺序可读。

把这两个方向都放在 JSON 层管理，可以避免每个入口各自手拼字符串，也方便测试锁住字段名称。


## 核心模型

JSON 在这个项目里有两个方向：配置输入和报告输出。

![C++ JSON 配置报告边界](/assets/diagrams/cpp-nlohmann-json-config-report.svg)

输入 JSON 是不可信文本，要解析成 `IndexerConfig`；输出 JSON 是审计结果，要从 `IndexResult` 生成。

## 逐步实现

样例配置：

```json
{
  "root": "sample_data/docs",
  "extensions": [".txt", ".md"]
}
```

读取配置：

```cpp
nlohmann::json value;
input >> value;
IndexerConfig config;
config.root = value.at("root").get<std::string>();
config.extensions = value.value("extensions", std::vector<std::string>{});
```

`at("root")` 会在字段缺失时报错，适合必填字段。`value("extensions", ...)` 给可选字段默认值，适合扩展名过滤。

报告 JSON 由 `IndexResult` 生成：

```cpp
nlohmann::json summary;
summary["files"] = result.summary.files;
summary["bytes"] = result.summary.bytes;
summary["lines"] = result.summary.lines;
summary["words"] = result.summary.words;

nlohmann::json value;
value["summary"] = summary;
value["files"] = files;
return value;
```

实验输出片段：

```json
{
  "summary": {
    "bytes": 304,
    "files": 3,
    "lines": 7,
    "words": 45
  }
}
```

同一个 `to_json_value` 也服务 `/api/summary` 和 `/api/files`。这让 CLI JSON 报告和 HTTP API 保持同一套字段语义。

## 输出怎么读

样例报告的核心结构是：

```json
{
  "summary": { "bytes": 304, "files": 3, "lines": 7, "words": 45 },
  "files": [
    { "path": "intro.txt", "bytes": 91, "lines": 2, "words": 13 }
  ]
}
```

`summary` 是聚合视图，适合 README、日志和 `/api/summary` 使用；`files` 是明细视图，适合审计某个文件为什么影响了总数。读输出时先看 `summary.files` 是否等于明细数组长度，再看 `summary.bytes/lines/words` 是否等于明细字段累计。

`at("root")` 和 `value("extensions", ...)` 的差异也要读懂：前者说明 `root` 是必填字段，缺失时应该尽早失败；后者说明扩展名列表可以有默认行为。

如果 JSON 解析失败，错误通常在配置输入；如果 JSON 成功生成但 API 字段不一致，错误通常在复用了不同转换函数。这个项目通过同一个 `to_json_value` 保持 CLI 报告和 HTTP API 的字段语义一致。


## 常见错误

1. **读取 JSON 后不检查必填字段**：后续路径为空时错误位置会更远。
2. **输出 JSON 时手拼字符串**：转义、数字类型和数组格式都容易出错。
3. **报告字段频繁改名**：JSON 字段是对外接口，应当稳定。

## 练习或延伸

- 给配置增加 `exclude_dirs` 字段，并在测试中覆盖它。
- 给 JSON 报告增加 `generated_at`，讨论可复现测试如何处理时间字段。

## 参考资料

- [nlohmann/json](https://github.com/nlohmann/json)
- [nlohmann/json API documentation](https://json.nlohmann.me/)
- [JSON format overview](https://www.json.org/json-en.html)
