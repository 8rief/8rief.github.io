---
layout: post
title: "C++ nlohmann/json：配置输入和结构化报告输出"
date: 2026-06-25 21:02:00 +0800
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
