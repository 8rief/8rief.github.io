---
layout: post
title: "项目配置文件与日志边界：让开发、测试和发布环境都可解释"
date: 2026-03-18 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个零依赖 Python lab 讲清 defaults/file/env/CLI 优先级、schema 校验、secret 边界、dry-run、JSONL 日志和 run_id。"
tags: [configuration, logging, python, software-engineering, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-config-logging-boundary/README.md`](/assets/labs/project-config-logging-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
前面的文章已经处理了 shell 环境变量、脚本参数和退出状态。项目开始跨开发机、测试环境和 CI 运行后，会出现一组新的问题：端口到底从哪里来的？命令行参数为什么没有生效？配置里多写了一个字段，程序为什么悄悄忽略？一次运行失败后，怎样把同一任务的日志串起来？调试输出里是否泄露了 token？

这些问题共享一个根因：程序缺少明确的配置输入边界和日志输出边界。本文用一个只依赖 Python 标准库的可复现实验，把配置解析、类型校验、优先级、secret 处理、`--dry-run`、stdout/stderr 分工和 JSON Lines 日志连成一个完整项目接口。

## 学习目标

完成本文后，你应该能够：

1. 解释 `defaults < config file < environment < CLI` 的覆盖顺序，并追踪每个最终值的来源。
2. 在程序启动阶段拒绝未知字段、错误类型、越界端口和非法日志级别。
3. 区分公开配置、部署时配置和 secret，保证 secret 值不进入源码、报告或日志。
4. 用 `--dry-run` 在产生业务副作用前检查最终配置。
5. 让正常结果走 stdout，让诊断事件走 stderr 或日志收集器。
6. 生成一行一个事件的 JSONL 日志，并用 `run_id` 关联同一次运行。

## 先修知识和实验产物

你需要会运行 Linux 命令、阅读 JSON，并知道环境变量只对子进程可见。本文的实验目录可以组织成：

```text
project-config-logging-boundary/
├── config/
│   ├── defaults.json
│   └── development.json
├── src/
│   └── demo_app.py
├── scripts/
│   └── config_log_probe.py
├── tests/
│   └── test_demo_app.py
├── reports/
└── run_lab.sh
```

实验会保留六类证据：单元测试输出、最终公开配置、JSONL 事件、成功与失败 transcript、机器可读 probe 报告和摘要。它不会安装第三方包，也不会把 secret 值写进任何生成文件。

## 为什么需要配置与日志边界

配置回答“这一次程序要按什么参数运行”，日志回答“程序实际经历了什么状态变化”。两者如果没有边界，会产生三种典型混乱：

- 值散落在代码常量、JSON、环境变量和脚本中，最后生效来源无法解释。
- 输入不校验，拼错字段或写错类型后，错误推迟到业务执行阶段。
- 正常结果、调试文本、异常堆栈和敏感值混在一个输出流里，调用者无法稳定解析。

本文采用下面的启动模型：

```text
public defaults
      ↓
environment config file
      ↓
environment variables
      ↓
CLI overrides
      ↓
schema + type + range validation
      ↓
resolved public config + source map
      ↓
dry-run or execution
      ↓
stdout result + structured event stream
```

每一层只覆盖它明确提供的键。合并完成后统一校验；校验失败就返回非 0，业务逻辑不会启动。

## 第一步：先定义允许变化的公开配置

默认配置包含服务名、监听地址、端口、日志级别和输出目录：

```json
{
  "service_name": "config-log-demo",
  "host": "0.0.0.0",
  "port": 8000,
  "log_level": "INFO",
  "output_dir": "/tmp/project-config-log-lab/output/default"
}
```

开发环境文件只覆盖确实不同的部分：

```json
{
  "host": "127.0.0.1",
  "port": 8080,
  "log_level": "WARNING",
  "output_dir": "/tmp/project-config-log-lab/output/development"
}
```

`service_name` 没有在第二个文件中重复，因此继续使用 defaults。这个做法让差异可见，也避免每个环境复制一整份配置后逐渐漂移。

配置文件适合保存可公开、可审查、需要多个字段共同表达的默认值。数据库密码、API token 和私钥不属于公开配置文件；它们应由部署环境或 secrets manager 注入。

## 第二步：优先级必须固定并可追踪

本文固定以下顺序：

```text
defaults < file < env < CLI
```

含义是右侧覆盖左侧。理由来自使用场景：

| 层 | 典型用途 | 生命周期 |
| --- | --- | --- |
| defaults | 仓库内安全默认值 | 随代码版本变化 |
| file | 某一环境的一组公开配置 | 随部署环境变化 |
| env | 单个部署单元的覆盖值或 secret | 随进程启动变化 |
| CLI | 本次运行的显式临时覆盖 | 随一次命令变化 |

实验故意让同一个端口经过多次覆盖：defaults 是 `8000`，development file 是 `8080`，环境变量是 `18080`，CLI 最终给出 `19090`。最终值和来源必须同时保留：

```text
RESOLVED_PORT=19090
SOURCE_PORT=cli
```

只记录最终值无法回答“为什么变成了 19090”。source map 会把 `service_name=defaults`、`output_dir=file`、`host=env`、`port=cli` 和 `log_level=cli` 一并写入 dry-run 结果。

## 第三步：在启动边界完成 schema 校验

配置加载器先要求 JSON 顶层是 object，再拒绝不在 allowlist 中的键：

```python
CONFIG_KEYS = {
    "service_name", "host", "port", "log_level", "output_dir"
}

unknown = sorted(set(value) - CONFIG_KEYS)
if unknown:
    raise ConfigError(f"config has unknown keys: {', '.join(unknown)}")
```

拒绝未知键比静默忽略更安全。假设用户写成 `log_levle`，静默忽略会沿用默认 `INFO`，直到排查日志时才发现配置从未生效；启动即失败能把错误定位在输入边界。

类型和范围也要统一检查：

```python
if isinstance(port, bool) or not isinstance(port, int):
    raise ConfigError("port must be an integer")
if not 1 <= port <= 65535:
    raise ConfigError("port must be between 1 and 65535")
if log_level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    raise ConfigError("invalid log level")
```

Python 中 `bool` 是 `int` 的子类，所以端口判断显式排除布尔值。字符串、空值、范围和枚举都应在业务代码运行前完成验证。

实验包含两个负例：

```text
config error: config has unknown keys: unexpected
UNKNOWN_KEY_RC=2

config error: port must be an integer
INVALID_PORT_RC=2
```

返回码 2 表示配置/调用接口错误。调用脚本和 CI 可以直接根据退出码停止，不需要解析长日志来猜测启动是否成功。

## 第四步：环境变量和 CLI 只覆盖明确提供的值

环境变量进入进程时都是字符串。端口需要显式转换，日志级别需要规范成大写；转换失败后把错误交给统一校验器。CLI 使用 `argparse` 定义类型：

```python
parser.add_argument("--config", type=Path)
parser.add_argument("--host")
parser.add_argument("--port", type=int)
parser.add_argument("--log-level")
parser.add_argument("--output-dir")
parser.add_argument("--dry-run", action="store_true")
```

CLI 参数默认值应使用 `None` 表示“本层没有提供”。如果直接把 CLI 默认端口设成 `8000`，即使用户没有写 `--port`，CLI 层也会覆盖 file 和 env，优先级模型就失真了。

合并伪代码保持单向数据流：

```text
merged = read(defaults)
merged.update(read(optional_file))
merged.update(present_environment_values)
merged.update(explicit_cli_values)
validated = validate(merged)
```

不要在业务模块中再次读取环境变量。所有输入在入口合并成一个不可变配置对象，后续模块只接收这个对象，测试时也更容易构造固定输入。

## 第五步：用 dry-run 检查状态，不先产生副作用

实验的成功命令可以写成：

```bash
DEMO_HOST=127.0.0.1 \
DEMO_PORT=18080 \
DEMO_LOG_LEVEL=INFO \
DEMO_API_TOKEN='<injected-secret>' \
python3 src/demo_app.py \
  --config config/development.json \
  --port 19090 \
  --log-level DEBUG \
  --events-file reports/events.jsonl \
  --run-id config-lab-run \
  --dry-run
```

示例中的 `<injected-secret>` 是占位符，不要把真实值写入 shell history、文章或仓库。实际部署应通过受控的 secret 注入机制提供。

`--dry-run` 仍会解析、合并、校验配置并初始化日志，但不会执行项目的业务写入。机器可读 stdout 包含：

```json
{
  "status": "ok",
  "mode": "dry_run",
  "run_id": "config-lab-run",
  "config": {
    "service_name": "config-log-demo",
    "host": "127.0.0.1",
    "port": 19090,
    "log_level": "DEBUG",
    "output_dir": "/tmp/project-config-log-lab/output/development"
  },
  "sources": {
    "service_name": "defaults",
    "host": "env",
    "port": "cli",
    "log_level": "cli",
    "output_dir": "file"
  },
  "secret_configured": true
}
```

程序只暴露 `secret_configured=true`，不返回 secret 的值、长度或片段。dry-run 可用于 CI 的配置预检，也可以在真正创建数据库连接、发送请求或写业务文件前让操作者确认状态。

## 第六步：划分 stdout、stderr 和文件证据

CLI 的 stdout 只输出调用者需要消费的结果 JSON。诊断事件写 stderr；实验同时把同一事件流复制到 `events.jsonl`，便于检查和教学。在容器或服务环境中，也可以让运行平台直接收集事件流并负责存储、轮转和检索。

这种分工允许下面的管道稳定工作：

```bash
python3 src/demo_app.py --dry-run >resolved.json 2>events.jsonl
python3 -m json.tool resolved.json
```

若把提示文字、进度条和日志都写进 stdout，`resolved.json` 就不再是合法 JSON。若完全丢弃 stderr，配置错误又会失去原因。因此两个通道都应纳入测试。

日志文件采用 JSON Lines：每行是一个独立 JSON object。一次实验生成 4 条事件：

```json
{"level":"DEBUG","event":"config_resolved","run_id":"config-lab-run","message":"configuration resolved"}
{"level":"INFO","event":"config_validated","run_id":"config-lab-run","message":"configuration validated"}
{"level":"INFO","event":"execution_planned","run_id":"config-lab-run","message":"execution plan selected"}
{"level":"INFO","event":"run_complete","run_id":"config-lab-run","message":"run completed"}
```

真实记录还包含 UTC timestamp 和必要的 details。JSONL 适合逐行写入、流式收集和按字段查询；某一行损坏时也容易定位，不需要等待整个 JSON array 结束。

## 第七步：event、level、message 和 run_id 各有职责

一条可用日志至少回答：什么时候发生、严重度是什么、发生了哪类事件、属于哪次运行、给人看的摘要是什么。

- `timestamp` 用 UTC ISO 8601，跨机器汇总时减少时区歧义。
- `level` 控制可见性；`DEBUG` 记录配置来源，`INFO` 记录正常状态变化。
- `event` 使用稳定、可查询的机器标签，如 `config_validated`。
- `message` 给人阅读，可以调整措辞，但不应承担唯一的机器分类职责。
- `run_id` 贯穿同一次命令、请求或训练任务，用来关联跨模块事件。

实验检查 4 行日志拥有同一个 `run_id=config-lab-run`。如果服务处理并发请求，还应区分 process-level run id、request id 和业务实体 id，避免把所有事件错误地串成一个流程。

日志级别也属于配置。生产环境通常减少 `DEBUG`，但错误和关键状态不能依赖 DEBUG 才出现。改变级别只控制详细度，不应改变业务逻辑或错误处理路径。

## 第八步：secret 只在最窄边界内使用

secret 可以通过环境变量或专用 secrets manager 进入进程，但进入后仍要限制传播：

```text
secret source
  -> process boundary
  -> client constructor / authentication call
  -> never enter public config, repr, exception text, metrics label or log details
```

本文的 probe 给子进程注入一个仅用于测试的标记值，然后扫描 stdout、stderr、JSONL 和所有报告。稳定结果是：

```text
SECRET_VISIBLE=no
```

这项测试比“代码看起来没有 print token”更可靠，因为泄露也可能来自异常、对象序列化、debug repr 或失败 transcript。真实项目还要检查崩溃转储、APM payload、CI artifact 和 shell tracing；使用 `set -x` 时尤其容易把环境变量展开到日志。

`.env` 文件可以作为某些本地工具的输入格式，但它不应被提交到公开仓库，也不应成为唯一的 secret 管理机制。仓库可以提供只含键名和假值的 `.env.example`，并通过 `.gitignore` 和 secret scanning 降低误提交风险。

## 完整复现实验和输出解释

运行：

```bash
./run_lab.sh
```

本次实测摘要为：

```text
CONFIG_PRECEDENCE=defaults<file<env<cli
RESOLVED_HOST=127.0.0.1
RESOLVED_PORT=19090
RESOLVED_LOG_LEVEL=DEBUG
UNKNOWN_KEY_RC=2
INVALID_PORT_RC=2
SECRET_VISIBLE=no
LOG_EVENT_COUNT=4
RUN_STATUS=ok
```

其中 `RUN_STATUS=ok` 表示单元测试、成功路径、两个失败路径、事件解析和 secret 扫描全部通过。它不表示程序已经连接真实数据库或启动网络服务；本文只验收配置与日志边界。

`reports/` 中值得保留的文件是：

```text
config_log_probe.json       机器可读的成功/失败总报告
resolved_config.json        dry-run 的公开配置和 source map
events.jsonl                四条结构化事件
transcript.md               命令、返回码和稳定观察
config_logging_summary.md   人类可读摘要
run_lab_output.txt          一键运行输出
```

## 测试哪些行为

单元测试覆盖四个稳定契约：

1. 四层配置按固定顺序覆盖，并保留 source map。
2. 未知键在启动阶段被拒绝。
3. 非整数端口被拒绝。
4. JSON 结果采用临时文件加 rename 的方式完整写入。

probe 再通过子进程覆盖 CLI、环境变量、stdout、stderr、return code 和 JSONL 文件边界。单元测试负责纯配置逻辑，probe 负责真实进程接口；两层测试关注的风险不同。

如果项目使用 YAML、TOML、Pydantic、Spring Boot、Viper、Serde 或其他配置库，仍应保留同一组行为测试。换库不能改变优先级、失败策略和 secret 边界。

## 常见错误与定位方式

1. **CLI 默认值覆盖所有层**：未提供参数时必须保持 `None`，只覆盖显式值。
2. **多处直接读环境变量**：把读取集中在入口，后续代码只接收已验证配置对象。
3. **未知字段静默忽略**：拼写错误会延迟暴露；默认拒绝未知键。
4. **只验证类型，不验证范围**：整数端口仍可能是 0 或 70000。
5. **把 secret 放进通用 config dump**：公开输出只保留是否配置，避免值、片段和长度。
6. **日志全是自由文本**：稳定 `event` 和 `run_id` 才能可靠查询和关联。
7. **stdout 混入诊断文本**：机器结果走 stdout，诊断走 stderr 或事件流。
8. **每个模块各建一套 handler**：应用入口统一配置 handler，库模块只获取 logger，防止重复日志。
9. **捕获配置异常后继续运行**：输入无效时返回非 0，不要带着半有效状态进入业务逻辑。
10. **只测试成功配置**：至少保留未知键、错误类型、越界值和 secret 泄露负例。

## 练习

1. 增加 `timeout_seconds`：defaults 为 30，环境变量可覆盖，要求整数范围 1 到 300；补齐成功与失败测试。
2. 增加 `--print-config-sources`，只输出每个公开字段的来源，不输出值，比较它和 `--dry-run` 的用途。
3. 把 `events.jsonl` 中同一 `run_id` 的事件读入 Python，验证事件顺序恰好是 resolve、validate、plan、complete。
4. 增加一个模拟业务失败事件，要求返回非 0、保留同一 run id、stderr 有结构化错误，但 stdout 不输出成功结果。
5. 将文件日志关闭，只保留 stderr 事件流，再用 shell 重定向收集；解释这种部署方式与应用自行管理 logfile 的取舍。

## 边界

本文的 JSON 配置适合小型项目和教学实验，不处理远程动态配置、配置热更新、分布式一致性、secret 轮换、日志采样、日志轮转或集中式 tracing。JSON 本身也不支持注释；大型配置需要权衡 TOML/YAML、schema 工具和框架集成。

日志可观测性不等于完整审计。安全审计日志还要定义访问控制、完整性、保留周期、时间同步和隐私要求。`run_id` 也不是认证凭据，不能用它代替用户身份或授权检查。

本文的最终结论可以压缩成一句话：先把配置解析成可验证、可追踪来源的公开状态，再让日志以结构化事件描述真实状态变化；secret 始终留在最窄的使用边界内。

## 参考资料

- Python 官方文档：[argparse — Parser for command-line options](https://docs.python.org/3/library/argparse.html)
- Python 官方文档：[logging — Logging facility for Python](https://docs.python.org/3/library/logging.html)
- Python 官方文档：[Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- Python 官方文档：[json — JSON encoder and decoder](https://docs.python.org/3/library/json.html)
- The Twelve-Factor App：[Config](https://12factor.net/config) 与 [Logs](https://12factor.net/logs)
- OWASP Cheat Sheet Series：[Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- OWASP Cheat Sheet Series：[Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

{% endraw %}
