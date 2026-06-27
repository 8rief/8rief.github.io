---
layout: page
title: 项目展示
permalink: /project-showcase/
---

这个栏目只放已经有具体输入、输出、报告或静态展示页的项目。文章从真实痛点开始，讲清为什么值得做、为什么这样设计、用了什么技术，以及如何复现。

## 写作结构

每篇项目展示文章默认包含：

1. **痛点**：真实失败场景或使用场景是什么，为什么 checklist 或口头约定不够。
2. **设计目标**：输入、输出、边界、非目标，以及为什么不做成更大的平台。
3. **详细设计**：数据结构、规则、流水线、模块拆分和关键取舍。
4. **技术实现**：CLI、文件格式、报告渲染、测试、静态页、hygiene 或其他用到的技术。
5. **复现方式**：最小命令、样例输入、预期输出。
6. **边界**：工具覆盖哪些判断，哪些判断必须交给人工或外部审查。


## 阅读分组

项目展示不追求线性学习顺序，适合按用途阅读：

| 分组 | 文章方向 | 阅读目的 |
| --- | --- | --- |
| 发布与治理门 | Release Integrity Suite、Public Repo Release Gate、Dataset Governance Suite、Paper Figure Auditor、Agent Leak Sentinel | 理解公开发布前如何检查证据、残留、数据集和图表主张 |
| 本地证据工具 | EvidencePack Core、MoveOutProof、CancelProof、InvoiceDisputeProof、RedactProof、ReproBadge Lite | 理解如何把现实争议或复现要求转成可保存的本地证据包 |
| 研究支撑工具 | Research Claim Ledger、Secure Trace Fixtures、Time-Series Attack Zoo | 理解研究实验如何保留 claim-evidence、trace 和攻击卡片 |
| Agent 记忆工具 | Capsule Memory Kit | 理解本地优先、可迁移、可维护的 agent 记忆胶囊设计 |

这些文章分类合理，但早期文章多用自定义小标题，不完全等同于后来的“痛点、设计目标、详细设计、技术实现、复现方式、边界”固定标题。后续新项目展示应继续使用固定结构。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "project-showcase" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
