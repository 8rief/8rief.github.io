---
layout: post
title: "CancelProof：取消订阅时，最先缺的往往是一条时间线"
date: 2026-06-18 03:12:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [local-first, evidence, subscription, consumer-tools]
---

> 代码状态：暂未公开。本文讨论的是本地证据整理，不是法律、金融、银行或消费者权益建议。  
> 主题：本地工具 / 订阅取消 / 证据时间线

取消订阅失败时，用户通常不是完全没有证据，而是证据没有排成一条可复核的线：哪天提交了取消表单，哪天发了邮件，哪天出现了后续扣费，截图和账单分别在哪里。等到要和商家、发卡机构或投诉渠道沟通时，材料越乱，越容易把问题说成情绪。

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
- CFPB guidance on disputing a credit-card charge: <https://www.consumerfinance.gov/ask-cfpb/how-do-i-dispute-a-charge-on-my-credit-card-bill-en-61/>
