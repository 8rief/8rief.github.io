---
layout: post
title: "数据处理入门：从 CSV 到报告的最小流水线"
date: 2026-07-01 11:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用销售数据 lab 看清原始数据、清洗、汇总、图表和报告之间的边界。"
tags: [data-processing, python, csv, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / pipeline / CSV to report
> 本文 lab 已验证：20 行原始记录清洗出 16 行有效数据、4 行拒收数据，总收入 `736.30`。

数据处理的第一步是把流水线边界说清楚：原始数据从哪里来，哪些行可以进入分析，哪些行必须被拒收，汇总指标怎样生成，图表和报告如何从同一份结果导出。边界稳定后，后续再换 pandas、数据库或 BI 工具才不会迷路。

## 学习目标

1. 理解“原始数据 → 清洗数据 → 汇总结果 → 图表/报告”的基本链路。
2. 运行一个 Python 标准库数据流水线，并看到 CSV、SQLite、JSON、SVG 和 Markdown 产物。
3. 知道为什么数据处理必须保存拒收行和 transcript。

## 先修知识

需要会运行 `python3 --version` 和 `bash run_lab.sh`。不要求先会 pandas 或可视化库。

## 核心模型

![CSV 到报告流水线](/assets/diagrams/data-pipeline-csv-to-report-model.svg)

本包使用同一份确定性销售数据：先生成原始 CSV，再清洗和拒收，再导入 SQLite 查询，最后生成 JSON 摘要、SVG 柱状图和 Markdown 报告。

## 可信资料的关键结论

- Python `csv` 文档强调用 `csv.reader`/`DictReader` 按 CSV 规则处理文本，不要手写 `split(',')`。
- Python `json` 模块适合把结构化结果保存为机器可读文件，也能用命令行工具校验和格式化。
- Python `sqlite3` 是标准库里的 SQLite 接口，适合本地报表、原型和教学中的 SQL 汇总。
- SVG 是 XML 形式的矢量图，适合生成无需截图的可复查图表。

## 逐步实现

运行完整 lab：

```bash
bash run_lab.sh
```

核心输出：

```text
raw_rows=20
clean_rows=16
rejected_rows=4
total_units=154
total_revenue=736.30
top_region=East:202.25
top_product=Backpack:335.25
pipeline_status=ok
```

主要产物：

```text
data/raw/sales.csv
data/processed/clean_sales.csv
data/processed/rejected_sales.csv
data/processed/sales.sqlite3
reports/summary.json
reports/region_revenue.svg
reports/report.md
reports/transcript.txt
```

打开 `reports/report.md` 可以看到文字报告，打开 `reports/region_revenue.svg` 可以看到按地区汇总的柱状图。这个最小项目已经覆盖数据处理的完整闭环。

## 常见错误

1. **只保留清洗后的数据。** 拒收行和原因是审计证据，不能丢。
2. **图表和报告各算一遍。** 这会制造数字不一致。应从同一份 summary 派生。
3. **把图画出来就算完成。** 还要说明数据来源、清洗规则、单位和限制。
4. **没有 transcript。** 以后无法证明报告是怎样从原始 CSV 生成的。

## 练习或延伸

1. 新增一个原始销售行，重新运行流水线，观察总收入变化。
2. 删除一个无效行，确认 `rejected_rows` 下降。
3. 把 `reports/summary.json` 中的 `by_region` 手动转成 Markdown 表格。

## 参考资料

- Python 文档：[csv](https://docs.python.org/3/library/csv.html)
- Python 文档：[json](https://docs.python.org/3/library/json.html)
- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)
- MDN：[SVG](https://developer.mozilla.org/en-US/docs/Web/SVG)

{% endraw %}
