---
layout: post
title: "安全时序实验先统一 trace：一个小型 fixture library 的作用"
date: 2026-07-09 18:00:00 +0800
categories: research-tools
column: project-showcase
column_title: "项目展示"
tags: [datasets, fixtures, time-series, reproducibility]
---

> 代码状态：暂未公开。库内只有合成 JSON，不包含用户记录或生产遥测。

当多个侧信道模拟器各自定义输入格式时，同一个“事件”会被写成不同字段：有的用整数时间，有的用 ISO 时间；有的把 cohort 放在标签里，有的直接省略；更严重的是，hidden label 和 public metadata 可能混在一起，实验脚本无意中读到了攻击者本不该看到的信息。

Secure Trace Fixture Library 提供一个很小的统一入口。它不追求大数据量，只负责验证 trace 的结构和泄漏边界。

## 设计约束

这个库需要同时满足三个约束：

1. **输入足够小。** 一个 fixture 应能被人工逐字段审阅，不用海量数据掩盖实验假设。
2. **隐藏与公开视图显式分离。** 攻击代码只应获得 `public_metadata`；`hidden_label` 仅供评估器计算指标。
3. **错误必须中止流水线。** 重复 ID、无效时间或缺失边界说明时，`--fail-on-findings` 返回非零退出码，下游模拟器不应继续跑。

最小记录的形状如下：

```json
{
  "id": "t1",
  "timestamp": "2026-06-01T00:00:00Z",
  "cohort": "factory-a",
  "hidden_label": "event",
  "public_metadata": {"count": 17, "window": "w1"}
}
```

`cohort` 在当前包中仍属于评估记录；具体实验是否允许攻击者看到 cohort，要由该实验自己的观察合同决定。fixture 存储了字段，不等于每个攻击函数都有权读取它。

## 最小接口

`secure-timeseries-lab` 仍是私有仓库，所以下面记录的是已在本地重跑的 CLI 形状，不暗示读者现在可以 clone。公开版本需保留这组参数和样例数据。

```bash
python3 trace_fixture_library.py examples/fixture_pack.json \
  --output reports/fixture_pack.md \
  --html-output reports/fixture_pack.html \
  --emit-json reports/normalized_traces.json \
  --fail-on-findings
python3 -m unittest discover -s tests -v
```

当前 fixture pack 只有三条记录：时间戳、cohort、hidden label，以及一个只允许公开字段进入的 metadata map。规模很小，足够测试解析、排序、字段约束和负面边界。

## 实现流程

工具的数据流保持简单：

```text
fixture_pack.json
  -> parse JSON
  -> validate IDs / timestamps / required fields / claim boundary
  -> sort by (timestamp, id)
  -> normalized_traces.json + Markdown report + static HTML
```

排序发生在规范化阶段，使不同书写顺序的等价 fixture 生成稳定输出。Markdown 适合代码审查，HTML 用于展示，JSON 交给下游脚本。三份产物来自同一份规范化对象，避免报告和机器输入各自实现一套规则。

## 正向与负向验证

对当前三条合成记录重跑 CLI 后，关键输出为：

```text
TRACE_FIXTURE_LIBRARY_STATUS traces=3 findings=0
Ran 3 tests in 0.002s
OK
```

三个测试分别检查正常规范化、负向边界和 CLI 三类输出。为了验证发现问题后真会阻断，另一轮临时输入复制 `t1` 并把 claim boundary 改成不合格文本，结果为：

```text
TRACE_FIXTURE_LIBRARY_STATUS traces=4 findings=2
exit status: 1
- claim boundary must state synthetic negative boundary
- duplicate trace id: t1
```

这个负向用例比成功生成报告更能验证工具边界。如果 validator 只会接受正常样例，就没有证据说明它能在真正的字段越界前停下流水线。

## 为什么 hidden/public 分离很重要

一个时间侧信道实验至少有三层数据：

1. **hidden ground truth**：用于给攻击结果打标签；
2. **public observation**：攻击者真正能读取的时间、数量或分组元数据；
3. **evaluation metadata**：种子、场景说明、许可证和预处理记录。

如果攻击函数直接拿到 hidden label，AUC 再高也没有意义。fixture validator 应在实验开始前拒绝字段越界，而不是等论文审稿时才靠人工发现。

## 常见误判

第一个误判是把 fixture 当成数据集贡献。三条合成记录只能证明输入合同和 validator 运行正常，不能证明攻击有效，也不能代表真实时间序列分布。

第二个误判是把字段存在当成攻击者可见。`cohort`、`hidden_label`、评估种子和场景说明可能都在同一份 pack 里，但攻击函数只能读取 observation contract 允许的 public view。

第三个误判是只跑正向样例。fixture 工具的价值很大一部分来自负向测试：重复 ID、缺失边界、非法时间或 hidden/public 混用时，流水线必须停止。

## 可以怎样练习

拿三条合成 trace，先写出攻击者允许看到的字段列表，再写 hidden ground truth。然后故意把 `hidden_label` 放进 `public_metadata`，或复制一个 trace ID。练习目标是让 validator 在实验开始前报错，而不是让攻击脚本跑出一个虚假的高分。

## 当前边界

三条合成记录只能证明格式和测试能运行，不能证明攻击有效。若接入公开数据，每个 pack 还必须先增加：

- source URL 与 license；
- 下载版本或 hash；
- preprocessing 脚本；
- 时间单位、缺失值和重采样规则；
- hidden/public 字段映射；
- 不允许公开的原始标识符。

这个小库的价值在于让 TimeLeaks、participation leakage 和 timing shaper 使用同一份输入合同。研究结果是否成立要由攻击、baseline 和真实实验回答；fixture library 只保证这些问题建立在可复查的数据边界上。

## 参考资料

- [RFC 8259: The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259)
- [Python `datetime.fromisoformat`](https://docs.python.org/3/library/datetime.html#datetime.datetime.fromisoformat)
