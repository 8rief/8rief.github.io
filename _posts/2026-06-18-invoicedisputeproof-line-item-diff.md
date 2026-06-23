---
layout: post
title: "InvoiceDisputeProof：发票争议先从行项目差异开始"
date: 2026-06-18 03:16:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [local-first, evidence, invoice, documentation]
---

> 代码状态：暂未公开。本文讨论的是本地证据和算术整理，不是法律、会计或金融建议。  
> 主题：本地工具 / 发票核对 / 证据包

发票争议里，最容易吵起来的部分往往不是总金额，而是总金额背后的行项目：合同里写了什么，发票多了什么，某一项为什么从 300 变成 450，新增费用有没有被提前确认。只盯着总数，很容易让沟通变成“我觉得不对”。

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

在样例里，测试输出会给出类似 `rows=3 delta_total=270.00` 的状态行。这个数字不是争议结论，而是本地算术结果。

## 隐私和边界

发票材料可能包含银行信息、付款凭据、客户资料、合同原文和邮件原件。公开样例不能包含这些内容；真实使用时，也应优先用 label、证据 ID 和脱敏说明。

InvoiceDisputeProof 不提供法律、会计或金融意见，也不判断一项费用是否一定不该收。它只是让沟通从“总额不对”变成“这几行和已确认材料不一致，请逐项说明”。

## 适合继续扩展的地方

后续如果公开代码，最值得补的不是更复杂的争议模板，而是更可靠的输入校验和导出格式：金额精度、币种、税费、折扣、部分付款、证据 ID 唯一性，以及从 CSV 导入的最小路径。

这些都还是同一个原则：先把事实表整理清楚，再谈判断。
