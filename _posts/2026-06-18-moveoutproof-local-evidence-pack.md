---
layout: post
title: "MoveOutProof：退租前先做一份本地证据包"
date: 2026-06-18 03:08:00 +0800
categories: local-tools
tags: [local-first, evidence, privacy, consumer-tools]
---

> 代码状态：暂未公开。本文讨论的是证据整理工具，不是法律建议。  
> 主题：本地工具 / 隐私 / 文档自动化

退租争议里最麻烦的常常不是某一条规则，而是材料散：入住照片在相册里，退租照片在另一个文件夹，房东消息在聊天记录里，押金扣款又出现在邮件或账单里。真正需要沟通时，用户很难快速回答三个问题：什么时间发生了什么、有哪些照片或文件能对应上、对方还缺哪些支持材料。

MoveOutProof 的目标很窄：在交钥匙前，把退租证据整理成一份本地 Markdown/HTML 包。它不上传照片，不替用户判断法律结论，也不承诺拿回押金；它只把时间线、房间检查、照片槽位、扣款问题和中性沟通模板放到同一份报告里。

## 证据包里应该有什么

当前样例围绕一个合成的 Apartment 4B 场景，报告结构包括：

| 部分 | 解决的问题 |
|---|---|
| 30-second summary | 快速说明房屋、日期、押金和争议点 |
| move-out timeline | 把检查请求、搬出日期、后续 statement 目标日期放在一起 |
| room-by-room checklist | 每个房间对应条件说明和照片文件名 |
| deduction challenge table | 每项扣款对应已有证据、缺失证明和应问问题 |
| photo coverage slots | 提醒保留搬入前、搬出后、对方维修后的照片 |
| neutral message | 生成克制的材料请求文本 |
| boundary | 明确这只是证据整理，不是法律意见 |

这里最重要的不是模板，而是“证据 ID 能对上问题”。比如一项清洁费扣款，如果已有厨房和浴室退租照片，报告会把这些照片列在 matching evidence 里，同时把发票、清洁前照片等缺失材料列为 missing proof。

## 本地接口形状

代码整理公开后，最小命令会保持成这种形式：

```bash
python3 moveoutproof.py examples/california_moveout_pack.json \
  --output reports/california_moveout_pack.md \
  --html-output site/index.html

PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest discover -s tests -v
```

测试覆盖的是工具行为，不是法律结论：

- 合成样例能生成 Markdown 和 HTML；
- 时间线字段能被计算和渲染；
- 扣款问题要足够具体，不能只写“请解释”；
- 邮箱、电话、token-like 字符串和常见敏感本地标记不会被直接渲染进报告。

## 为什么坚持 no-upload

退租材料往往包含住址、房间照片、账单、聊天截图和私人联系方式。把这些东西上传到一个不明确的数据处理服务里，本身就会引入新的风险。

MoveOutProof 的设计选择是：输入文件、生成报告和静态页面都留在本地。用户如果要分享，应先人工复核报告，只保留必要材料和 label。公开 demo 也只能使用合成数据，不能使用真实租赁文件。

## 使用边界

MoveOutProof 不判断扣款是否合法，也不替用户写正式争议函。它只帮助用户把材料组织得更可读：哪些事实已经有文件支持，哪些地方需要向对方索要书面依据。

如果涉及真实纠纷，规则会受州、市、租约和具体事实影响，必须查当前官方材料或咨询专业人士。工具能做的是降低材料混乱，而不是替代判断。

## 参考

- California Courts security-deposit guide: <https://selfhelp.courts.ca.gov/guide-security-deposits-california>
