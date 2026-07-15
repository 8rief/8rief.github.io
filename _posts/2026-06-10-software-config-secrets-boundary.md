---
layout: post
title: "配置和敏感信息边界：示例能提交，真实值留在本地环境"
date: 2026-06-10 09:00:00 +0800
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

## 为什么要引入配置边界

配置边界要解决的核心问题是“同一份代码在不同环境下运行”。项目名、数据文件、日志级别、端口、数据库连接和外部服务地址经常随环境变化；把这些值写死在源码里，会让测试、本地运行和部署互相干扰。

可以把配置分成三层：

```text
默认值       -> 让程序在最小场景能启动
示例配置     -> 让读者知道有哪些字段和值域
真实本地配置 -> 留在环境变量、部署系统或未提交文件中
```

公开仓库只应该包含前两层。第三层可能包含个人路径、账号、token、内网地址或真实业务数据，应该默认排除。

## 好配置和危险配置的区别

可提交的示例配置：

```json
{
  "log_level": "info",
  "data_file": "data/tasks.json"
}
```

不应该提交的真实运行值：

```text
DATABASE_URL=postgres://user:password@example.internal/app
API_TOKEN=<real token>
HOME_CACHE=/Users/someone/private-cache
```

判断标准很简单：读者拿到示例配置能理解字段和跑通 demo，但无法得到真实凭据、真实账号或本机私有路径。

## 配置加载顺序

小项目可以采用明确的合并顺序：

```text
内置默认值 < config/example.json 或 config/local.json < 环境变量 < 命令行参数
```

越靠右越具体，优先级越高。这个顺序适合写进 README，避免读者猜测某个值为什么生效。

示例伪代码：

```python
def load_config(defaults, file_values, env_values, cli_values):
    config = defaults | file_values | env_values | cli_values
    validate(config)
    return config
```

`validate()` 应在程序真正读写文件或连接服务前运行。早失败能节省定位时间，也能避免用错误配置生成一堆无效报告。

## 输出怎么读

配置校验的输出适合打印安全摘要：

```text
config_source=example.json
log_level=info
data_file_present=true
secrets_loaded=false
```

这些字段说明程序用的是哪类配置、关键字段是否存在、是否读取了私有凭据。输出不包含真实 token、密码、cookie 或完整私有路径。这样的日志既能帮助排查，也不会把敏感值带进 transcript。

## 状态变化和 `.gitignore`

运行 demo 后，项目目录会同时出现可提交文件和本地状态文件：

```text
config/example.json  -> 可提交，说明字段和值域
data/tasks.json      -> demo 数据，可按项目策略决定是否提交
.env                 -> 本地私有，必须忽略
reports/*.tmp        -> 临时产物，通常忽略
```

`.gitignore` 固定的是版本库边界。它不能替代安全审查，但能阻止最常见的误提交。

## 检查清单

发布前至少检查：

```text
[ ] README 说明配置来源和优先级
[ ] 仓库有 example config 或 schema
[ ] `.env`、本地缓存、临时报告被 ignore
[ ] 程序启动时会校验必填字段
[ ] 日志只输出安全摘要
```

配置问题往往在交付后才暴露。把这几项放进 release checklist，比事后追查一次误提交成本低得多。

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
