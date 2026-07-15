---
layout: post
title: "JSON 摘要：让图表、报告和测试共享同一份结果"
date: 2026-06-19 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把清洗后的汇总写成 summary.json，避免图表和文字报告各算各的。"
tags: [json, data-report, python, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / JSON summary / report contract
> 本文 lab 已验证：`reports/summary.json` 中总收入为 `736.3`，地区第一名为 East。

数据项目最容易出现的错误之一，是图表里一个数字、文字报告里另一个数字。解决办法是把汇总结果先写成一个机器可读的 JSON 摘要，让图表、Markdown 报告和测试都读取同一份结果。

## 学习目标

1. 理解 summary 文件作为图表和报告的共享契约。
2. 用 `json.dumps(..., ensure_ascii=False, indent=2)` 写出可读 JSON。
3. 从 JSON 中检查关键指标。

## 先修知识

已经知道 clean CSV 是后续分析的输入。

## 核心模型

![JSON 摘要作为共享契约](/assets/diagrams/data-json-summary-contract.svg)

SQLite 查询生成 summary，summary 再派生出 SVG 和 Markdown。测试也读取 summary。这样所有展示层都围绕同一份指标。

## 为什么需要 summary 契约

数据报告常见的失误是多个展示层各自计算指标：图表查一次数据库，文字报告再查一次，测试又读另一个文件。只要其中一个查询条件或排序规则不同，最终展示就会出现互相矛盾的数字。summary 契约用来把已经确认的指标固定下来。

本 lab 让 `summary.json` 承担三项职责：

1. 给 SVG 图表提供 `by_region`。
2. 给 Markdown 报告提供 headline 和分组表。
3. 给测试提供稳定断言入口。

这样修改图表样式不会改变汇总口径，修改报告模板也不会重新计算收入。展示层只负责展示，指标生成由 SQLite 查询集中完成。

## 可信资料的关键结论

- Python `json` 模块可以把 Python 字典、列表等对象序列化为 JSON 字符串。
- `python -m json` 可以在命令行验证和格式化 JSON，适合检查报告中间产物。
- JSON 适合做机器可读契约，但不适合承载复杂查询；查询部分仍交给 SQLite。

## 逐步实现

写 JSON：

```python
def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

摘要结构：

```json
{
  "raw_rows": 20,
  "clean_rows": 16,
  "rejected_rows": 4,
  "total_units": 154,
  "total_revenue": 736.3,
  "by_region": [
    { "region": "East", "revenue": 202.25 }
  ]
}
```

命令行查看：

```bash
python3 -m json.tool reports/summary.json | head
```

## 输出怎么读

`summary.json` 的顶层字段分成两类：

- 质量和规模字段：`raw_rows`、`clean_rows`、`rejected_rows`。
- 指标字段：`total_units`、`total_revenue`、`by_region`、`by_month`、`by_product`、`by_channel`。

当前结果里：

```json
{
  "total_revenue": 736.3,
  "by_region": [
    { "region": "East", "revenue": 202.25 },
    { "region": "South", "revenue": 197.25 }
  ]
}
```

这表示折扣后总收入是 736.30，地区收入第一名是 East。`736.3` 在 JSON 中省略末尾 0 是正常的数值表示；在 Markdown 报告中会格式化成 `736.30`，方便人读。

测试读取：

```python
payload = json.loads(summary_path.read_text(encoding="utf-8"))
self.assertEqual(payload["by_month"][1], {"month": "2026-02", "revenue": 301.25})
```

## 契约变更怎么做

如果要新增 `average_order_value`，先在 summary 中增加字段，再让报告、图表或测试读取它。不要在报告模板里临时计算。契约变更的顺序应是：

```text
SQL/汇总逻辑 -> summary.json -> 测试断言 -> 展示层
```

这样每次增加指标都能留下明确的证据链。

## 常见错误

1. **图表直接重新查询，报告也重新查询。** 多个入口会让数字容易不一致。
2. **JSON 不缩进。** 机器能读，人复查困难。
3. **把本地路径写进公开 JSON。** 公开报告只保留相对产物和指标。
4. **JSON 当数据库用。** 它适合交换结果，不适合复杂筛选和聚合。

## 练习或延伸

1. 给 summary 增加 `by_channel` 的百分比字段。
2. 用 `python3 -m json.tool` 校验一个故意写坏的 JSON。
3. 写一个小脚本只读取 `summary.json` 并打印 top region。

## 参考资料

- Python 文档：[json](https://docs.python.org/3/library/json.html)
- JSON 官方站点：[json.org](https://json.org/)

{% endraw %}
