---
layout: post
title: "Release Integrity Suite：把发布前检查合成一条本地流水线"
date: 2026-06-23 17:20:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [release, reproducibility, local-first, evidence]
---

> 代码状态：暂未公开。本文只记录设计目标、检查边界和可复现的接口形状。  
> 主题：工程实践 / 本地工具 / 发布前检查

很多小工具单独看都有用，但如果每个都包装成一个产品，读者很难理解它们解决的真实问题。发布前检查就是这种场景：泄漏扫描、复现材料、主张证据、证据包和最终发布门禁天然属于同一条流水线；拆成五个互相分散的 README，反而会削弱问题主线。

Release Integrity Suite 做的就是把这些动作合成一条本地流程。输入是一个准备发布的样例仓库，输出是一组 Markdown/HTML 报告和一个总览页面。它不上传代码，不读取账户，不打印密钥内容，也不声称能证明仓库安全；它只回答一个更朴素的问题：在公开之前，常见的发布阻塞项有没有被看见。

## 这条流水线检查什么

当前设计包含五步：

| 步骤 | 模块 | 作用 |
|---:|---|---|
| 1 | Agent Leak Sentinel | 检查 agent/export 相关泄漏面，但不输出命中的敏感内容 |
| 2 | ReproBadge Lite | 检查 README、许可证、环境、测试、CI、引用、数据说明、结果目录和 secret-like pattern |
| 3 | Research Claim Ledger | 检查主张是否有范围、限制和已验证证据 |
| 4 | EvidencePack Core | 把发布证据整理成可审阅的 evidence pack |
| 5 | Public Repo Release Gate | 根据必要文件、报告、静态页和 claims 给出最终 block/review 结论 |

这五步放在一起后，故事比单独发布五个小工具更清楚：先看有没有不该公开的东西，再看别人能不能复现或审阅，再看说法是否超过证据，最后才决定是否进入人工发布审查。

## 设计目标和取舍

这个 suite 的核心取舍是“本地、可解释、可拆开检查”。它解决发布前预检的组合问题，不扩展成覆盖一切的发布平台。原因有三点。

第一，发布前检查经常涉及敏感上下文。泄漏扫描如果把命中的内容原样输出，反而可能制造新的泄漏面。因此 leak-surface 模块只记录规则和位置级别的风险，不把疑似 secret 内容复制进报告。

第二，复现性和发布安全需要分层处理。README、license、测试、CI 和 citation 决定别人能否审阅；claim ledger 和 evidence pack 决定公开说法是否有证据；release gate 负责把这些信号合成最终的 block/review 状态。流水线保留每个 component report，避免一个总分掩盖具体问题。

第三，样例仓库必须是合成的。它要覆盖真实发布流程会遇到的文件形态：README、license、项目元数据、引用元数据、测试、CI、报告、静态页和安全的 `.env.example`；但不能依赖任何私有代码或账户状态。

## 技术实现

实现上，suite orchestrator 复用已有组件的 CLI，然后统一收敛结果：

- 用 `subprocess` 依次运行五个 component CLI，保证每个模块仍可独立复现。
- 每个组件都写出 Markdown 和 HTML 报告，suite 只解析报告中的少量稳定字段，例如 score、grade、blocked claims、validation findings 和 release decision。
- 运行后会做文本 sanitization，把本地工作区绝对路径替换成 `<local-workspace>`，避免公开报告带出机器路径。
- suite 级报告再生成 `reports/release_integrity_suite.md`、`reports/release_integrity_suite.html` 和 `site/index.html`。
- 单元测试检查组件数量、最终 decision、报告存在性和本地路径不泄漏。

这种设计的原因是：component 是事实来源，suite 是编排和摘要层。后续如果某个模块规则变了，只需要保持报告字段稳定，suite 不需要复制那一套判断逻辑。

## 本地接口形状

代码整理公开后，最小使用方式会保持成这种形式：

```bash
cd suites/release-integrity-suite
python3 release_integrity_suite.py --output-root .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

样例输入是一个合成的待发布仓库，包含 README、license、项目元数据、引用元数据、测试、CI、报告和静态页面。当前样例的预期结果是：

| 检查 | 预期结果 |
|---|---|
| 泄漏扫描 | no configured leak-risk rule fired |
| 复现预检查 | 100/100，grade ready |
| 主张账本 | ready 2，blocked 0 |
| 证据包 | validation findings 0 |
| 发布门禁 | ready-for-human-review，blocking findings 0 |

这里的 `ready-for-human-review` 很重要：它表示材料已经适合进入人工审查，最终发布仍由人根据风险和场景决定。

## 为什么这样收尾

这批工程资产里有不少工具是同一类思路的变体。如果继续把它们分别包装，会显得数量很多，但展示价值反而下降。更合理的方式是：

1. 保留真正独立的展示项目；
2. 把相邻小工具合成套件；
3. 对重复或边界成本高的工具停止投入；
4. 用一张收尾矩阵记录每个工程为什么保留、合并、归档或丢弃。

Release Integrity Suite 属于第二类：它把五个已存在的小模块收束成一个可理解、可复跑的发布前检查路径。

## 边界

这套流程适合做发布前的本地预检，让明显问题在公开前暴露出来。它覆盖不了法律审查、安全审计、合规认证或同行评审；最终是否发布，仍然需要人根据场景、风险和证据做判断。
