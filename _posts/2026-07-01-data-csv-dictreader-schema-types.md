---
layout: post
title: "读 CSV：表头、字段类型和 DictReader 的入口边界"
date: 2026-07-01 11:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从 sales.csv 出发，解释为什么 CSV 先是文本，再由代码转成日期、整数和金额。"
tags: [python, csv, data-cleaning, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / CSV / schema / types
> 本文 lab 已验证：`data/raw/sales.csv` 有 20 行数据记录和 1 行表头。

CSV 文件看起来像表格，但它本质上仍是文本。表头只是字段名，后面的 `units`、`unit_price`、`discount_pct` 在读入时都是字符串。数据处理的入口边界就是：先按 CSV 规则读行，再按业务规则把字符串转换成日期、整数和金额。

## 学习目标

1. 知道 CSV 表头如何映射成字段名。
2. 会用 `csv.DictReader` 逐行读取字典。
3. 理解类型转换要放在显式校验阶段。

## 先修知识

知道文件路径和命令输出的基本概念。

## 核心模型

![CSV 表头到字段类型](/assets/diagrams/data-csv-dictreader-schema-types.svg)

CSV 入口先得到字符串字典，再进入校验函数。校验函数负责把字段转成真正的类型，并决定该行进入 clean 还是 reject。

## 可信资料的关键结论

- Python `csv` 文档说明，文件对象应使用 `newline=''` 打开，避免换行处理干扰 CSV 解析。
- `DictReader` 会用第一行表头作为字典 key，让代码按字段名读取，而不是按列下标猜含义。
- CSV 没有自动类型系统，金额、日期和整数都需要代码显式转换。

## 逐步实现

原始 CSV 的表头：

```text
order_id,date,region,channel,product,units,unit_price,discount_pct
```

读取方式：

```python
with raw_path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        clean, reason = validate_row(row, seen_ids)
```

此时 `row['units']` 仍是字符串，例如 `'2'`。校验阶段再转换：

```python
units = int((row.get("units") or "").strip())
unit_price = Decimal((row.get("unit_price") or "").strip())
parsed_date = date.fromisoformat(raw_date)
```

运行后确认行数：

```bash
wc -l data/raw/sales.csv
```

预期输出是 `21`，其中 1 行表头和 20 行记录。

## 常见错误

1. **用 `line.split(',')` 解析 CSV。** 遇到引用、逗号、换行时容易错。
2. **按列下标读字段。** 字段顺序变化会让代码悄悄错位。
3. **读入时就相信类型正确。** CSV 入口只能保证文本结构，不能保证业务有效。
4. **金额直接用 float 做源数据。** 本包用 `Decimal` 处理金额，再在入 SQLite 时转成报表数值。

## 练习或延伸

1. 给 CSV 增加一列 `coupon_code`，观察 `DictReader` 是否能读到新字段。
2. 把一行 `units` 改成 `abc`，重新运行流水线，设计新的拒收原因。
3. 打印第一行 `row`，确认每个值都是字符串。

## 参考资料

- Python 文档：[csv](https://docs.python.org/3/library/csv.html)
- Python 文档：[decimal](https://docs.python.org/3/library/decimal.html)
- Python 文档：[datetime.date.fromisoformat](https://docs.python.org/3/library/datetime.html#datetime.date.fromisoformat)

{% endraw %}
