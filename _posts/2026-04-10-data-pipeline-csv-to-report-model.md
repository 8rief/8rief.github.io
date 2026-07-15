---
layout: post
title: "数据处理入门：从 CSV 到报告的最小流水线"
date: 2026-04-10 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用销售数据 lab 看清原始数据、清洗、汇总、图表和报告之间的边界。"
tags: [data-processing, python, csv, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/data-processing-visualization/README.md`](/assets/labs/data-processing-visualization/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

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

## 为什么需要先画出流水线

初学数据处理时，最容易把“读文件”“改字段”“画图”“写报告”混在一个脚本里。脚本短的时候还能看懂；一旦数字出错，就很难判断错误来自原始数据、清洗规则、汇总 SQL，还是图表生成。流水线图用来解决这个定位问题。

本包把状态变化拆成六层：

1. `data/raw/sales.csv`：保留原始输入和表头。
2. `clean_sales.csv`：只保存通过校验的行，并增加 `revenue`。
3. `rejected_sales.csv`：保存不能进入分析的行和拒收原因。
4. `sales.sqlite3`：把 clean 行放进本地表，统一用 SQL 汇总。
5. `summary.json`：把汇总结果固化成共享契约。
6. `region_revenue.svg` 与 `report.md`：从 summary 派生展示产物。

这样设计后，每个数字都能反查来源。比如 `total_revenue=736.30` 有问题，可以先看 clean 行数是否为 16，再查 SQLite 汇总，再看 JSON 和报告是否读取了同一份结果。

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

## 输出怎么读

这段输出给出流水线的主账本：

- `raw_rows=20`：原始 CSV 中有 20 条销售记录。
- `clean_rows=16`：16 条通过字段校验、类型转换和重复订单检查。
- `rejected_rows=4`：4 条进入拒收表，原因可在 `rejected_sales.csv` 中复查。
- `total_units=154`：clean 行里的销量合计。
- `total_revenue=736.30`：折扣后收入合计。
- `top_region=East:202.25`：地区收入第一名是 East。
- `pipeline_status=ok`：脚本、测试和报告生成完成。

这些字段之间应该能相互解释。`raw_rows` 应等于 `clean_rows + rejected_rows`；`top_region` 应出现在 `summary.json` 的 `by_region[0]`；报告和图表只使用 clean 行派生的结果。

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

## 最小排错顺序

如果报告数字不符合预期，按下面顺序查：

```bash
wc -l data/raw/sales.csv data/processed/clean_sales.csv data/processed/rejected_sales.csv
python3 -m json.tool reports/summary.json | head
sqlite3 data/processed/sales.sqlite3 'SELECT COUNT(*) FROM sales;'
grep -F 'pipeline_status=ok' reports/transcript.txt
```

先看行数，再看 summary 是否能解析，再看 SQLite 表行数，最后看 transcript 是否记录了完整运行。

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
