---
layout: post
title: "模块边界：把 domain、storage、config 和 CLI 分开"
date: 2026-06-09 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 workflow_kit 的 domain/storage/config/layout/cli 拆分解释为什么核心逻辑应该少依赖边界细节。"
tags: [software-engineering, modules, architecture, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / module boundaries
> 本文 lab 已验证：domain validation、layout 创建、storage round trip 和 CLI contract 都有 unittest 覆盖。

项目变大后，最容易混乱的是模块职责。一个可维护的小项目通常把核心规则和外部边界分开：domain 负责业务对象和规则，storage 负责读写，config 负责配置校验，CLI 负责把用户输入转成函数调用。

## 学习目标

1. 区分核心逻辑和边界适配器。
2. 理解为什么 domain 模块应该尽量少依赖文件系统和命令行。
3. 用测试覆盖模块边界，而不是只测最终脚本。
4. 能为一个小项目画出模块调用方向。

## 先修知识

需要理解函数、模块和单元测试。本文示例使用 Python，但边界思想适用于 Java、Go、C++ 和 Rust 项目。

## 核心模型

![核心逻辑和边界适配器](/assets/diagrams/software-module-boundaries-domain-adapters.svg)

`domain` 在中间，定义 `Task`、状态和摘要规则；`storage` 把对象保存成 JSON；`config` 校验项目根和名称；`layout` 创建目录；`cli` 把命令行参数传给这些模块。测试可以分别验证每条边界。

## 逐步实现

核心对象：

```python
@dataclass(frozen=True)
class Task:
    task_id: int
    title: str
    status: str = "todo"
    owner: str = "unassigned"
```

存储边界：

```python
def save_state(path: Path, state: dict[str, object]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
```

CLI 不直接拼 JSON，不直接实现业务规则；它只解析参数、调用模块、输出结果。这样改 storage 时不用改 domain，改 CLI 文案时不用改核心规则。

## 为什么要引入模块边界

模块边界要解决的核心问题是“改一个地方牵动全项目”。如果 CLI 直接读写 JSON、拼路径、校验状态、生成报告，任何需求变化都会落在同一个文件里：新增字段会影响命令解析，存储格式变化会影响业务规则，错误处理也会混在用户输出中。

更稳的做法是让依赖方向单向流动：

```text
cli -> config/layout/storage -> domain
```

`domain` 定义任务、状态和摘要规则；边界模块负责把外部世界转换成 domain 能理解的数据。domain 越干净，测试越容易写，后续替换 CLI 或 storage 的成本越低。

## 一次命令经过哪些模块

执行下面命令时：

```bash
python3 -m workflow_kit.cli add --root demo_project --owner dev --status doing "separate domain and storage"
```

调用链可以理解为：

```text
cli.py      解析 argv，得到 root/owner/status/title
config.py   校验 root 和项目名等配置
storage.py  读取 data/tasks.json
 domain.py  创建 Task，检查 status 是否合法，计算下一个 id
storage.py  原子写回 JSON
cli.py      打印 added id=2 ...
```

这条链路中，只有 `cli.py` 关心命令行文本；只有 `storage.py` 关心 JSON 文件；只有 `domain.py` 关心任务规则。定位问题时可以沿着链路逐层缩小范围。

## 用测试观察边界

测试名称本身就是边界地图：

```text
test_domain_validation_and_summary ... ok
test_layout_creates_expected_directories ... ok
test_storage_round_trip ... ok
test_cli_contract ... ok
```

读这些输出时，可以按失败位置判断修复入口：

| 失败测试 | 优先检查 | 常见原因 |
|---|---|---|
| `domain_validation` | `domain.py` | 状态枚举、摘要计数、字段校验 |
| `layout_creates` | `layout.py` | 目录名、缺少父目录、权限假设 |
| `storage_round_trip` | `storage.py` | JSON schema、临时文件、编码 |
| `cli_contract` | `cli.py` 与端到端链路 | 参数解析、输出字段、退出码 |

测试分层让失败变成可定位的工程信号。

## 状态变化示例

添加一条任务前后，项目状态发生的是数据变化，不应该改变模块依赖关系：

```json
{
  "before": {"tasks": []},
  "after": {"tasks": [{"task_id": 1, "status": "todo", "owner": "product"}]}
}
```

如果新增字段 `priority`，合理修改路径是：先扩展 domain 的数据结构和校验，再让 storage 保存字段，最后让 CLI 暴露参数。反过来先改 CLI 输出，很容易让内部规则和持久化格式不同步。

## 边界命名建议

小项目可以从下面命名开始：

```text
domain.py   纯规则和数据结构
storage.py  文件或数据库读写
layout.py   目录创建和路径约定
config.py   配置加载与校验
cli.py      用户入口和输出 contract
```

命名不是重点，职责稳定才是重点。一个模块的名字如果无法说明“它为什么变化”，通常需要继续拆分。

## 常见错误

1. **CLI 里堆所有逻辑。** 后续测试、复用和迁移都会困难。
2. **domain 依赖本地路径。** 纯规则应能在内存中测试。
3. **storage 静默吞错。** schema 版本、字段类型和文件格式错误应该显式失败。
4. **循环依赖。** 模块之间互相导入会让边界失效。

## 练习或延伸

1. 给 `Task` 增加 `priority` 字段，判断要改哪些模块。
2. 把 JSON storage 替换成 CSV storage，尽量保持 domain 测试不变。
3. 为 CLI 的错误输出增加一条测试。

## 参考资料

- Python 文档：[dataclasses](https://docs.python.org/3/library/dataclasses.html)
- Python 文档：[json](https://docs.python.org/3/library/json.html)
- Python 文档：[os.replace](https://docs.python.org/3/library/os.html#os.replace)

{% endraw %}
