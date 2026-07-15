---
layout: post
title: "数据清洗：把有效行和拒收行分开保存"
date: 2026-06-18 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用缺失地区、负数销量、非法日期和重复订单解释可复查的数据质量边界。"
tags: [data-quality, validation, python, teaching]
---
{% raw %}
> 主题：数据处理与可视化 / cleaning / validation / rejects
> 本文 lab 已验证：4 行被拒收，原因依次是 `missing_region`、`invalid_units`、`invalid_date`、`duplicate_order_id`。

清洗要把进入分析的数据和不能进入分析的数据分开保存，并记录原因。这样报告中的每个数字都能追溯：哪些行参与了计算，哪些行被挡在外面。

## 学习目标

1. 写出行级校验规则。
2. 把清洗行写到 `clean_sales.csv`，把拒收行写到 `rejected_sales.csv`。
3. 理解拒收原因为什么是报告可信度的一部分。

## 先修知识

已经知道 CSV 读入后字段都是字符串，需要校验和类型转换。

## 核心模型

![数据清洗和拒收边界](/assets/diagrams/data-cleaning-validation-rejects.svg)

每一行只有两个出口：clean 或 reject。clean 行增加计算字段 `revenue`，reject 行增加 `reason`。后续 SQLite 和图表只使用 clean 行。

## 为什么需要保存拒收表

数据清洗的目标不是让坏数据消失。如果报告只说 clean 行有 16 条，却不说明另外 4 条为什么被排除，读者无法判断指标是否可信。拒收表用来回答三个问题：哪些行没有参与计算，具体原因是什么，规则以后变更时哪些结果会受到影响。

本 lab 的四类拒收原因分别对应常见质量问题：

1. `missing_region`：分类维度缺失，无法归入地区汇总。
2. `invalid_units`：销量为负数，进入收入计算会扭曲结果。
3. `invalid_date`：日期无法解析，无法按月份汇总。
4. `duplicate_order_id`：订单重复，继续计算会造成收入重复。

这些原因写进 `rejected_sales.csv`，比只写进运行日志更适合复查和测试。

## 可信资料的关键结论

- Python `csv.DictWriter` 可以按固定字段顺序写回 CSV，适合保留清洗后的表结构。
- Python `unittest` 适合把拒收原因固定成测试断言，防止清洗规则被无意改坏。
- 数据质量规则应尽量给出具体原因，而不是统一写成 `invalid`。

## 逐步实现

校验函数的核心结构：

```python
def validate_row(row, seen_ids):
    order_id = (row.get("order_id") or "").strip()
    if not order_id:
        return None, "missing_order_id"
    if order_id in seen_ids:
        return None, "duplicate_order_id"
    ...
    return clean_row, None
```

拒收行写出：

```python
rejected = {field: row.get(field, "") for field in FIELDNAMES}
rejected["reason"] = reason
rejects.append(rejected)
```

运行后查看：

```bash
cat data/processed/rejected_sales.csv
```

关键原因：

```text
missing_region
invalid_units
invalid_date
duplicate_order_id
```

## 输出怎么读

lab 输出中有三组行数：

```text
raw_rows=20
clean_rows=16
rejected_rows=4
```

这三个数必须满足 `20 = 16 + 4`。如果不满足，说明清洗函数可能丢行、重复写行，或统计口径不一致。拒收原因的顺序也被测试固定：

```text
missing_region -> invalid_units -> invalid_date -> duplicate_order_id
```

顺序稳定是为了让回归测试能捕获规则变化。真实项目中也可以增加 `row_number` 字段，让拒收表直接定位到原始文件行号。

测试里也固定了这些原因：

```python
self.assertEqual(reasons, [
    "missing_region",
    "invalid_units",
    "invalid_date",
    "duplicate_order_id",
])
```

## 清洗规则的边界

本 lab 选择“发现重复订单时拒收后出现的重复行”。另一种策略是保留最后一条或合并重复行。不同策略会改变收入指标，因此必须写成显式规则并加测试。清洗规则没有绝对通用答案，关键是让规则、结果和证据一致。

## 常见错误

1. **默默跳过坏行。** 这样报告无法解释为什么原始行数和清洗行数不一致。
2. **把错误原因写进日志，不写进文件。** 文件才是后续审计和报告的稳定输入。
3. **重复 id 不检查。** 汇总时同一订单可能被重复计算。
4. **校验规则没有测试。** 后续改字段时很容易改变拒收逻辑。

## 练习或延伸

1. 增加一条 `discount_pct=1.20` 的行，并加入 `invalid_discount_pct` 测试。
2. 把重复 id 的规则改成保留第一条还是最后一条，并解释取舍。
3. 给 `rejected_sales.csv` 增加一列 `row_number`，方便回到原始文件定位。

## 参考资料

- Python 文档：[csv.DictWriter](https://docs.python.org/3/library/csv.html#csv.DictWriter)
- Python 文档：[unittest](https://docs.python.org/3/library/unittest.html)

{% endraw %}
