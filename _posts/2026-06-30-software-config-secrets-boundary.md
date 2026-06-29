---
layout: post
title: "配置和敏感信息边界：示例能提交，真实值留在本地环境"
date: 2026-06-30 03:43:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 example config、.env ignore、默认值和校验解释项目如何把可公开配置与本机私有值分开。"
tags: [software-engineering, configuration, gitignore, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / configuration boundary
> 本文 lab 已验证：demo 项目生成 `config/example.json`，并在 `.gitignore` 中排除 `.env`。

项目需要配置，但配置分两类：可公开的示例和值域说明，留在本机或部署环境里的真实值。工程上要让新人能用 example config 跑起来，同时避免把本机私有信息写进仓库、日志或报告。

## 学习目标

1. 区分默认配置、示例配置、环境变量和运行时配置。
2. 用 `.gitignore` 固定本机私有文件边界。
3. 给配置加校验，尽早发现空值和危险路径。
4. 避免在日志和报告中输出私有值。

## 先修知识

需要知道 JSON、环境变量和 Git ignore 的基本作用。

## 核心模型

![配置边界和本地私有值](/assets/diagrams/software-config-secrets-boundary.svg)

公开仓库中保留 defaults、schema 或 example config；真实值从本地环境或部署系统注入；配置进入程序前先校验；日志只输出安全摘要，例如配置来源和字段是否存在。

## 逐步实现

lab 生成的 `.gitignore` 片段：

```text
__pycache__/
*.pyc
.env
reports/*.tmp
```

示例配置：

```json
{"log_level":"info","data_file":"data/tasks.json"}
```

配置对象负责基本校验：

```python
@dataclass(frozen=True)
class ProjectConfig:
    root: Path
    name: str

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("project name must not be empty")
```

这个结构保证公开示例足够运行，真实值不进入版本库。若后续接数据库、外部 API 或云服务，也应保持同样边界。

## 常见错误

1. **把真实环境文件提交到仓库。** `.env`、token、cookie 和本机路径都应该留在本地。
2. **没有 example config。** 新读者无法知道需要哪些字段。
3. **配置校验太晚。** 程序运行很久后才因空值失败，会增加定位成本。
4. **日志打印完整配置。** 日志适合打印字段名、来源和校验结果，不适合打印私有值。

## 练习或延伸

1. 给 example config 增加 `output_format`，并在配置校验中限制可选值。
2. 写一个 `load_config()`，按 defaults、file、environment 的顺序合并配置。
3. 检查一个已有项目的 `.gitignore` 是否覆盖 `.env`、缓存和临时报告。

## 参考资料

- The Twelve-Factor App：[Config](https://12factor.net/config)
- Git 文档：[gitignore](https://git-scm.com/docs/gitignore)
- Python 文档：[os.environ](https://docs.python.org/3/library/os.html#os.environ)

{% endraw %}
