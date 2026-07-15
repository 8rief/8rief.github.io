---
layout: post
title: "CancelProof：取消订阅时，最先缺的往往是一条时间线"
date: 2026-07-06 09:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [local-first, evidence, subscription, consumer-tools]
---

> 代码状态：暂未公开。本文讨论的是本地证据整理，不是法律、金融、银行或消费者权益建议。  
> 主题：本地工具 / 订阅取消 / 证据时间线

取消订阅失败时，用户通常有一些证据，但证据没有排成一条可复核的线：哪天提交了取消表单，哪天发了邮件，哪天出现了后续扣费，截图和账单分别在哪里。等到要和商家、发卡机构或投诉渠道沟通时，材料越乱，越容易把问题说成情绪。

CancelProof 针对的是这个小问题：把取消请求、后续扣费、截图、邮件和下一步动作整理成一个本地 evidence pack。它不登录任何服务，不替用户取消，不联系银行，也不判断争议一定成立。

## 一个取消证据包的结构

当前样例是一个合成的 gym membership 场景。报告里最关键的是四块：

| 部分 | 作用 |
|---|---|
| timeline | 按日期列出取消表单、确认邮件、后续扣费 |
| charge review | 区分取消前正常扣费和取消请求后的待复核扣费 |
| evidence manifest | 把截图、邮件、账单行分别列为证据项 |
| neutral notice | 生成要求书面确认的克制文本 |

这个结构避免了两种极端：一是只写“商家乱扣费”，没有材料；二是把一堆截图直接发出去，让对方自己猜重点。

## 本地接口形状

代码整理公开后，最小命令会保持成这种形式：

```bash
python3 cancelproof.py examples/gym_membership_cancel.json \
  --output reports/gym_membership_cancelproof.md \
  --html-output reports/gym_membership_cancelproof.html \
  --site-output site/index.html

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 -m unittest discover -s tests -v
```

测试覆盖几个可机械验证的点：

- CLI 能生成 Markdown、HTML 和本地静态页；
- 后续扣费能被标记为 disputed review item；
- 报告包含 timeline、evidence、notice 和 boundary；
- 静态表单不上传数据，也不引用外部脚本；
- 缺少 timeline 的输入会被拒绝。

这类工具的可信度来自简单约束，而不是复杂自动化。

## 为什么不做“一键取消”

“一键取消”听起来更有吸引力，但它会立刻引入登录、cookie、支付信息、站点自动化和责任边界问题。CancelProof 先选择更窄的目标：不碰账号，不碰支付凭据，只把用户已经拥有的本地证据整理清楚。

这个选择牺牲了自动化程度，但换来两个好处：一是隐私边界清楚，二是输出更容易审查。用户可以打开生成的 Markdown/HTML，确认每一条材料是否适合分享。

## 使用边界

CancelProof 不是法律建议、金融建议、银行建议、消费者权益建议，也不保证退款或取消成功。订阅规则、争议流程和时限会随地区、商家、发卡机构、卡组织和合同变化。

它能提供的是一个更干净的事实包：我在什么时间做过什么、有什么文件能证明、还需要对方书面确认什么。

## 参考

- FTC consumer advice on free trials, auto-renewals and negative option subscriptions: <https://consumer.ftc.gov/articles/getting-and-out-free-trials-auto-renewals-and-negative-option-subscriptions>
- FTC consumer advice on disputing credit-card charges: <https://consumer.ftc.gov/articles/disputing-credit-card-charges>

## 设计目标与约束

CancelProof 关注取消订阅、退款或服务关闭过程中的时间线。争议出现时，关键问题通常关键在于每一步请求、回复、确认号和扣费记录能否按时间连起来。

## 实现细节

事件可以用统一结构记录：

```json
{
  "time": "2026-06-18T10:00:00+08:00",
  "kind": "cancel_request",
  "channel": "web",
  "evidence": "screenshots/cancel-button.png",
  "note": "submitted cancellation form"
}
```

报告生成器按时间排序，并标记缺口：例如有扣费记录但没有续费提醒，有取消请求但没有确认号。

## 可复现示例

```bash
python3 cancelproof.py add sample.json --kind cancel_request --evidence screenshots/cancel.png
python3 cancelproof.py report sample.json --output cancellation-timeline.md
```

预期输出形状：

```text
events=3
missing_confirmation=true
report_ready=cancellation-timeline.md
status=review-needed
```

## 输出怎么读

`missing_confirmation=true` 是行动提示：需要继续查邮件、网页记录或客服记录，补上取消确认。工具只整理证据缺口，不直接判断责任归属。

## 常见误判

第一个误判是把“我点过取消”当成完整证据。取消争议里通常还需要时间、渠道、确认号、后续扣费和原始截图之间能互相对应。

第二个误判是把自动生成的 notice 写成情绪化投诉。这个工具应输出克制的材料请求：哪天取消、哪笔扣费需要复核、希望对方提供什么书面说明。

第三个误判是把账单争议、合同条款和取消流程混成一个结论。CancelProof 只把事件排成可检查时间线；是否退款、是否超期、该走哪条渠道，需要按商家规则和相关机构流程另行判断。

## 可以怎样练习

构造三条合成事件：一次取消请求、一封确认邮件、一笔取消后的扣费。先不写结论，只给每条事件补 `time`、`channel`、`evidence_id` 和 `note`。然后删除确认邮件，观察报告是否能把问题从“商家乱扣费”收敛成“缺少取消确认，需要补证据或请求书面说明”。

## 边界

不要把账号密码、完整付款信息或个人敏感信息写入公开报告。公开展示时应使用脱敏样例。
