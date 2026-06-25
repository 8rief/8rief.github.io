---
layout: post
title: "Python 项目收尾：结构、配置、日志和 README"
date: 2026-06-25 16:37:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 Python 教学项目收成可展示形态：目录结构、配置边界、日志入口、README、demo 命令和验证清单。"
tags: [python, project-structure, config, logging, readme, capstone]
---
{% raw %}


> 主题：Python 从0到可运行项目 / 项目结构 / 配置 / 日志 / README / 结课项目  
> 本文是 Python 包的结课文章。配套 lab 已完成 CLI、API、HTTP client、pytest 和 transcript。

项目收尾的目标是让别人能理解、运行、验证和修改。很多教程在“代码能跑”处结束，实际交付还需要目录结构、配置入口、日志格式、README、测试命令和 demo 输出。本文把前七讲收束成一个可展示的小项目。

## 学习目标

1. 解释一个小型 Python 项目的目录结构。
2. 区分源码、测试、脚本、样例数据和报告。
3. 用环境变量承载可变配置，但不把敏感值写进源码。
4. 给 CLI/API 准备统一日志入口。
5. 写出能被复跑的 README/demo 命令。

## 先修知识

需要完成前七讲，或至少理解虚拟环境、dataclass、文件扫描、CLI、pytest 和 FastAPI 的基本作用。

## 核心模型

结课项目的收尾链条如下：

![项目收尾检查链](/assets/diagrams/python-project-structure-config-logging-readme.svg)

目录结构让文件位置可解释；配置让可变参数离开代码；日志让问题可定位；测试让改动可回归；README/demo 让项目能被展示。

## 目录结构

最终 lab 结构：

```text
local-evidence-kit/
├── README.md
├── pyproject.toml
├── run_lab.sh
├── sample_data/
│   ├── events.json
│   ├── metrics.csv
│   └── notes/hello.txt
├── scripts/
│   ├── api_smoke.py
│   └── http_client_smoke.py
├── src/local_evidence/
│   ├── api.py
│   ├── cli.py
│   ├── config.py
│   ├── http_client.py
│   ├── logging_utils.py
│   ├── models.py
│   ├── scanner.py
│   └── storage.py
└── tests/
```

这个结构对应清楚的职责：源码放在 `src`，测试放在 `tests`，样例输入放在 `sample_data`，演示脚本放在 `scripts`，验证入口放在 `run_lab.sh`。

## 配置和日志

配置模块从环境变量读取可变参数：

```python
@dataclass(frozen=True)
class AppConfig:
    evidence_root: Path
    log_level: str = "INFO"
    timeout_seconds: float = 2.0

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            evidence_root=Path(os.getenv("LOCAL_EVIDENCE_ROOT", ".")).expanduser().resolve(),
            log_level=os.getenv("LOCAL_EVIDENCE_LOG_LEVEL", "INFO").upper(),
            timeout_seconds=float(os.getenv("LOCAL_EVIDENCE_TIMEOUT", "2.0")),
        )
```

配置值通过环境变量进入程序。涉及敏感值时，应只读运行环境，不写进源码、README、报告或截图。

日志入口保持集中：

```python
def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
```

当前项目日志很少，但预留统一入口能避免后续模块各自配置日志格式。

## README 要回答什么

一个能展示的 README 至少回答五个问题：

1. 项目解决什么问题。
2. 如何安装和运行。
3. 主要命令是什么。
4. 预期输出长什么样。
5. 测试和边界在哪里。

本 lab 的最小 README 说明了项目能力，并给出唯一入口：

```bash
./run_lab.sh
```

执行后 transcript 中应出现：

```text
.......                                                                  [100%]
scanned root=sample_data files=3 bytes=119
api /manifest sample_data -> {'file_count': 3, 'total_bytes': 119}
http client mock -> files=3 bytes=42
```

这比“运行成功”更可检查，因为输出绑定了测试、CLI、API 和 HTTP client 四个边界。

## 结课项目验收清单

- 环境：`python3 --version` 已记录，虚拟环境可重建。
- 依赖：`pyproject.toml` 描述运行依赖和开发依赖。
- 核心逻辑：扫描、哈希、排序、汇总在独立模块中。
- 文件输出：JSON 和 CSV 来自同一份 manifest。
- CLI：`scan` 和 `summary` 可执行，可测试。
- API：`/health` 和 `/manifest` 可本地验证，并限制路径边界。
- HTTP client：设置 timeout，统一错误类型，可 mock 测试。
- 测试：7 个 pytest 用例覆盖关键边界。
- README/demo：提供单入口命令和可检查输出。

## 常见错误

1. **README 只写功能列表。** 读者需要运行步骤和预期输出。
2. **配置散落在模块里。** 可变值应有集中入口。
3. **日志随手 print。** CLI 可以 print 用户结果，诊断信息应走日志。
4. **demo 没有测试支撑。** 展示用输出应该来自可复跑命令。

## 练习

1. 把 `run_lab.sh` 拆成 `make test`、`make demo` 两个目标，比较哪种入口更适合你的读者。
2. 给 README 增加一段“设计边界”，说明本项目只扫描本地普通文件并跳过符号链接。
3. 增加一个 GitHub Actions workflow，在 push 时执行 `python -m pytest -q`。

## 参考资料

- PyPA docs source：[Packaging Python Projects](https://github.com/pypa/packaging.python.org/blob/main/source/tutorials/packaging-projects.rst)
- Python 文档：[logging](https://docs.python.org/3/library/logging.html)
- Twelve-Factor App：[Config](https://12factor.net/config)
- PyPA docs source：[src layout vs flat layout](https://github.com/pypa/packaging.python.org/blob/main/source/discussions/src-layout-vs-flat-layout.rst)


{% endraw %}
