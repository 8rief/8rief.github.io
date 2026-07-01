---
layout: post
title: "结课项目：做一个可复查的销售数据报表和 SVG 图表"
date: 2026-07-01 11:49:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 CSV 清洗、SQLite 汇总、JSON 摘要、SVG 柱状图和 Markdown 报告合成一个小项目。"
tags: [data-processing, visualization, capstone, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / capstone / reproducible report
> 本文 lab 已验证：一条命令生成清洗数据、拒收表、SQLite 数据库、JSON 摘要、SVG 图表、Markdown 报告和 transcript。

这个结课项目的目标是完成一个可复查的数据报表小项目。它不依赖 pandas 或绘图库，故意使用 Python 标准库把每一步摊开：读 CSV、清洗、入库、查询、写 JSON、画 SVG、写报告、跑测试。

## 学习目标

1. 从零运行一个完整数据处理和可视化项目。
2. 解释每个产物的作用和来源。
3. 用测试和 transcript 证明报告数字可信。
4. 知道下一步如何扩展到 pandas、matplotlib 或更大的数据库。

## 先修知识

建议按顺序读完本包前七篇，并确认 Python 3 可用。

## 核心模型

![数据处理与可视化结课项目](/assets/diagrams/data-processing-visualization-capstone.svg)

结课项目的证据链是：原始 CSV 生成，清洗规则固定，拒收原因保存，SQLite 查询汇总，summary 派生图表和报告，测试验证关键指标，transcript 保存完整过程。

## 可信资料的关键结论

- Python 标准库已经足够完成小型本地数据报表：`csv` 读写表格文本，`json` 保存结构化摘要，`sqlite3` 做本地 SQL 汇总，`unittest` 固定关键结果。
- SVG 图表是文本文件，适合教学、版本控制和自动生成；复杂绘图可以在理解映射关系后再引入绘图库。
- 数据报告的可信度来自输入、清洗规则、汇总 SQL、图表生成和测试证据的一致链路。

## 逐步实现

完整运行：

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

项目结构：

```text
data-processing-visualization/
  scripts/pipeline.py
  scripts/test_pipeline.py
  data/raw/sales.csv
  data/processed/clean_sales.csv
  data/processed/rejected_sales.csv
  data/processed/sales.sqlite3
  reports/summary.json
  reports/region_revenue.svg
  reports/report.md
  reports/transcript.txt
```

可展示产物：

```text
reports/report.md
reports/region_revenue.svg
reports/summary.json
```

可审计产物：

```text
data/processed/rejected_sales.csv
reports/transcript.txt
data/processed/sales.sqlite3
```

这说明项目不仅能“出图”，还能解释图的数字从哪里来。

## 常见错误

1. **只交付最终图。** 数据处理项目还需要原始输入、清洗产物和报告证据。
2. **图表和报告数字不共享来源。** 本包用 `summary.json` 作为共同来源。
3. **拒收数据没有解释。** `rejected_sales.csv` 是质量边界，不是临时垃圾。
4. **测试没有覆盖关键业务指标。** 总收入、行数、top region、拒收原因都应被断言。

## 练习或延伸

1. 用 matplotlib 重新生成同一张地区收入柱状图，并对比 SVG 手写版。
2. 把 SQLite 查询结果导出为 `reports/region_revenue.csv`。
3. 增加一个折扣后平均客单价指标。
4. 把这条流水线包装成命令行参数，例如 `--input raw.csv --out reports/`。

## 参考资料

- Python 文档：[csv](https://docs.python.org/3/library/csv.html)
- Python 文档：[json](https://docs.python.org/3/library/json.html)
- Python 文档：[sqlite3](https://docs.python.org/3/library/sqlite3.html)
- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)
- MDN：[SVG](https://developer.mozilla.org/en-US/docs/Web/SVG)

{% endraw %}
