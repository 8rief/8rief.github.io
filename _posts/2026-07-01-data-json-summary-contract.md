---
layout: post
title: "JSON 摘要：让图表、报告和测试共享同一份结果"
date: 2026-07-01 11:21:00 +0800
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

测试读取：

```python
payload = json.loads(summary_path.read_text(encoding="utf-8"))
self.assertEqual(payload["by_month"][1], {"month": "2026-02", "revenue": 301.25})
```

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
