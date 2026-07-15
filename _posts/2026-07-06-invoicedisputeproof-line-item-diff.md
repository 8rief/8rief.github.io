---
layout: post
title: "InvoiceDisputeProof：发票争议先从行项目差异开始"
date: 2026-07-06 18:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [local-first, evidence, invoice, documentation]
---

> 代码状态：暂未公开。本文讨论的是本地证据和算术整理，不是法律、会计或金融建议。  
> 主题：本地工具 / 发票核对 / 证据包

发票争议里，最容易产生分歧的是总金额背后的行项目：合同里写了什么，发票多了什么，某一项为什么从 300 变成 450，新增费用有没有被提前确认。只盯着总数，很容易让沟通变成“我觉得不对”。

InvoiceDisputeProof 的目标很窄：把 agreed line items 和 invoiced line items 做本地对比，算出每一行 delta，再生成一份中性 evidence pack。它不替用户判断合同、不做账务意见，也不保证争议结果。

## 先把差异拆到行

当前合成样例里，总差异是 270：

| Item | Agreed | Invoiced | Delta |
|---|---:|---:|---:|
| Brand guide | 300.00 | 450.00 | 150.00 |
| Logo design | 500.00 | 500.00 | 0.00 |
| Rush fee | 0.00 | 120.00 | 120.00 |

这个表比一句“多收了 270”更有用。它把问题分成两个可沟通的点：Brand guide 为什么增加了 150，Rush fee 是否有事先确认。接下来才需要看合同、消息记录和对方解释。

## 证据包结构

报告包含几块固定内容：

- agreed total、invoiced total 和 delta total；
- 每个行项目的 agreed / invoiced / delta；
- evidence manifest，例如 redacted scope、确认无 rush fee 的消息；
- neutral dispute message；
- claim boundary。

这种结构的价值在于克制。它不把输出写成控诉信，而是把可核对的数字和证据 ID 放在前面。

## 本地接口形状

代码整理公开后，最小命令会保持成这种形式：

```bash
python3 invoicedisputeproof.py examples/design_invoice_case.json \
  --output reports/design_invoice_case.md \
  --html-output reports/design_invoice_case.html

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 -m unittest discover -s tests -v
```

测试当前覆盖三类行为：

- CLI 能生成 Markdown/HTML 报告；
- 对比逻辑能发现 overcharge 和 extra line；
- 报告必须包含中性消息和边界说明。

在样例里，测试输出会给出类似 `rows=3 delta_total=270.00` 的状态行。这个数字是本地算术结果，不能直接当作争议结论。

## 隐私和边界

发票材料可能包含银行信息、付款凭据、客户资料、合同原文和邮件原件。公开样例不能包含这些内容；真实使用时，也应优先用 label、证据 ID 和脱敏说明。

InvoiceDisputeProof 不提供法律、会计或金融意见，也不判断一项费用是否一定不该收。它只是让沟通从“总额不对”变成“这几行和已确认材料不一致，请逐项说明”。

## 当前收尾边界

当前展示聚焦行项目差异，不把完整发票系统、税务规则或付款状态管理混进来。若进入公开代码发布，最低边界应先固定金额精度、币种、税费、折扣、部分付款、证据 ID 唯一性，以及从 CSV 导入的最小路径。

这些都还是同一个原则：先把事实表整理清楚，再谈判断。

## 设计目标与约束

InvoiceDisputeProof 处理的是发票争议中的行项目差异。总价不一致时，直接讨论“贵了多少”很容易失焦；把每一行的数量、单价、税费和折扣拆开，争议点才清楚。

## 实现细节

输入可以是两份 CSV：

```csv
item,qty,unit_price,total
storage,2,10,20
support,1,30,30
```

比较器按 `item` 对齐，输出新增项、删除项、数量变化、单价变化和总价变化。这样报告能直接指出“哪一行导致差异”。

## 可复现示例

```bash
python3 invoice_diff.py expected.csv actual.csv --output reports/invoice-diff.md
```

预期输出形状：

```text
matched_items=2
changed_items=1
unexpected_items=1
total_delta=15.00
status=review-needed
```

## 输出怎么读

`unexpected_items=1` 表示实际账单中有一行不在预期清单里；`total_delta=15.00` 是金额差异汇总。下一步应回到原始合同或订单确认记录，而不是只看总价。

## 常见误判

第一个误判是只比较总金额。总金额相同也可能存在错误行项目：一项多收，另一项少收，最后抵消。行级 diff 才能让对方逐项说明。

第二个误判是用浮点数直接处理金额。金额比较应该使用固定小数或 decimal 语义，避免二进制浮点误差把一分钱级差异变成噪声。

第三个误判是把 `unexpected_items=1` 直接写成“对方多收”。工具只能说明实际发票出现了一行预期清单没有的项目；是否合理，要回到合同、订单确认、变更记录或后续授权。

## 可以怎样练习

准备两份三行 CSV：预期清单里有 `design`、`review`、`hosting`，实际清单把 `review` 单价提高，并新增 `rush_fee`。练习时先手算每行 delta，再看报告是否能同时给出 `changed_items=1` 和 `unexpected_items=1`。如果只输出一个总差额，这个工具就没有解决沟通问题。

## 参考

- Python `decimal` module: <https://docs.python.org/3/library/decimal.html>
- RFC 4180 common CSV format: <https://www.rfc-editor.org/rfc/rfc4180>

## 边界

这个工具不判断收费是否合法，只把行项目差异整理成可沟通材料。公开样例应使用虚构金额和虚构供应商。
