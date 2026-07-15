---
layout: page
title: 项目案例
permalink: /project-showcase/
---

这里用已经产生具体输入、输出、报告或静态页面的项目讲工程设计。重点是从需求和约束推导模块、数据流、验证方式与边界。

## 怎样读一个项目案例

1. 先写下项目要解决的失败场景，以及明确不解决什么。
2. 找出输入、状态变化、输出和外部副作用。
3. 追踪一个样例经过哪些模块，观察每个模块为什么存在。
4. 对照复现接口和输出证据，判断文章的结论是否过界。
5. 尝试改变一个约束，推导设计需要怎样变化。

## 按学习目标选择

| 学习目标 | 案例方向 | 重点观察 |
| --- | --- | --- |
| 学公开发布与质量门禁 | Release Integrity Suite、Public Repo Release Gate、Dataset Governance Suite、Paper Figure Auditor、Agent Leak Sentinel | 规则怎样映射到机器检查，自动化判断在哪里必须停下 |
| 学本地证据与可追溯输出 | EvidencePack Core、MoveOutProof、CancelProof、InvoiceDisputeProof、RedactProof、ReproBadge Lite | 原始观察、哈希、清单、报告和人工判断如何分层 |
| 学研究工程的数据边界 | Research Claim Ledger、Secure Trace Fixtures、Time-Series Attack Zoo | claim、trace、样本、模型值和实测结果如何保持可追溯 |
| 学 Agent 记忆系统 | Capsule Memory Kit | 工作记忆、长期资产、索引、同步和安全边界如何组合 |

[计算机技术教学](/computer-science-teaching/)中的语言路线提供可运行项目基础；项目案例适合在具备本地测试经验后阅读。

## 当前案例地图

项目案例已经按问题收束成几类。读的时候重点看“为什么需要这个工具”和“它把判断留给机器还是人”。

| 问题 | 案例 | 应重点观察什么 |
| --- | --- | --- |
| 公开仓库前怎样避免残留 | [Agent Leak Sentinel](/local-tools/2026/07/03/agent-leak-sentinel-release-residue-scan.html)、[Public Repo Release Gate](/local-tools/2026/07/04/public-repo-release-gate-claim-evidence-caveat.html)、[Release Integrity Suite](/local-tools/2026/07/04/release-integrity-suite-local-preflight.html) | 高风险文件、claim/evidence/caveat、最终 block/review 决策怎样分层 |
| 证据包怎样保持可追溯 | [EvidencePack Core](/local-tools/2026/07/05/evidencepack-core-local-evidence-schema.html)、[MoveOutProof](/local-tools/2026/07/05/moveoutproof-local-evidence-pack.html)、[CancelProof](/local-tools/2026/07/06/cancelproof-cancellation-evidence-timeline.html)、[InvoiceDisputeProof](/local-tools/2026/07/06/invoicedisputeproof-line-item-diff.html) | 时间线、manifest、hash、请求事项和边界声明怎样组成报告 |
| 隐私和脱敏预检怎样落地 | [RedactProof](/local-tools/2026/07/07/redactproof-redaction-residue-check.html) | 视觉遮挡、文件结构、metadata、annotation 和报告输出之间的差异 |
| 研究材料怎样防止过度声明 | [ReproBadge Lite](/local-tools/2026/07/07/reprobadge-lite-reproducibility-preflight.html)、[Research Claim Ledger](/local-tools/2026/07/08/research-claim-ledger-overclaim-audit.html)、[Paper Figure Auditor](/local-tools/2026/07/08/paper-figure-auditor-claim-evidence-links.html) | README、测试、引用、图表主张和证据链接能否互相追溯 |
| 数据集和研究实验怎样收口 | [Dataset Governance Suite](/local-tools/2026/07/09/dataset-governance-suite-release-gate.html)、[Secure Trace Fixtures](/research-tools/2026/07/09/secure-trace-fixtures.html)、[Time-Series Attack Zoo](/research-tools/2026/07/10/time-series-attack-zoo.html) | 样本来源、trace fixture、攻击卡片、负结果和发布边界怎样写清楚 |
| Agent 记忆资产怎样迁移 | [Capsule Memory Kit](/local-tools/2026/07/10/capsule-memory-kit-portable-agent-memory.html) | 源记忆、生成记忆、manifest、索引、同步和安全排除列表怎样配合 |

## 全部项目案例

{% assign posts = site.posts | where: "column", "project-showcase" %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}{% if post.categories %} · {{ post.categories | join: ", " }}{% endif %}
{% endfor %}
