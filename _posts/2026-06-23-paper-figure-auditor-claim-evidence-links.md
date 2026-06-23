---
layout: post
title: "Paper Figure Auditor：把论文里的图表主张连回证据"
date: 2026-06-23 21:30:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [research, evidence, figures, local-first]
---

> 代码状态：暂未公开。本文只记录设计目标、检查边界和可复现的接口形状。  
> 主题：研究工程 / 图表证据 / 发布前检查

写论文或技术报告时，最容易出问题的地方不一定是代码，而是文字和证据之间的缝隙：正文说了一个结论，图表存在，但原始行、实验边界和必要限制没有被连起来。等到投稿、公开 README 或写博客时，这种缝隙会变成过度表述、图表误用或复现材料缺口。

Paper Figure Auditor 处理的就是这个小问题。它不判断论文是否创新，也不替代统计检验；它只要求每条主张在本地 manifest 中指向图、表、源证据和 caveat。缺文件、缺 evidence、引用不存在的 ID，或者把合成结果写成普遍结论，都会被提前暴露出来。

## 它检查什么

当前版本的检查范围很窄：

| 检查项 | 触发方式 | 结果 |
|---|---|---|
| 缺图或缺表 | claim 没有连接 figure/table | block |
| 缺源证据 | claim 没有 evidence | block |
| 引用未知 ID | claim 指向不存在的 figure/table/evidence | block |
| 本地文件不存在 | manifest 中的路径找不到文件 | block |
| 路径越界 | 使用绝对路径或 `..` 路径 | block |
| 表述过宽 | 出现最优、普遍、保证等说法但没有 caveat | needs-human-review |

这类 gate 的价值不在于复杂，而在于把“这句话凭什么说”变成一个可以复查的本地结构。

## 详细设计

Paper Figure Auditor 的核心是一个很小的 manifest。它只管理“主张—图表—证据—边界”的连接关系，不接管论文写作。manifest 里显式列出四类对象：

- `figures`：图表文件或图的 stand-in，包含 ID、路径和说明。
- `tables`：表格文件，包含 ID、路径和说明。
- `evidence`：原始行、分析说明、实验 contract 等证据对象。
- `claims`：正文主张，记录它引用哪些 figures、tables、evidence，以及 caveat。

检查规则按严重程度分成两类：

| 严重程度 | 含义 | 例子 |
|---|---|---|
| `block` | 结构性缺口，不能进入发布审查 | 缺 evidence、引用未知 ID、本地文件不存在、路径越界 |
| `review` | 需要人工确认，但不必自动阻断 | 使用最优、保证、普遍有效等强表述却没有 caveat |

这样拆分是为了避免两个极端：如果所有问题都 block，工具会变成噪声很大的 checklist；如果所有问题都只是提醒，又挡不住明显错误。结构性链接错误必须阻断，措辞和 caveat 的匹配则交给人工复核。

## 技术实现

实现只依赖 Python 标准库：

- `json` 读取 manifest，`pathlib` 检查本地文件存在性和路径安全。
- `dataclass` 表达 finding 和 audit summary，让 decision 由 findings 推导出来。
- CLI 提供 `--output`、`--html-output`、`--site-output` 和 `--fail-on-block`，适合接进发布前脚本。
- Markdown 报告保留完整 claim/figure/table/evidence 对照表，HTML 报告用于静态展示。
- 测试覆盖 clean manifest、缺文件、缺 evidence、未知 evidence、路径越界、过宽表述和 CLI 输出。

当前版本不接入 LaTeX、PDF 解析或统计检验，因为检查目标只限于“主张和证据对象是否连上”。图是否画对、统计是否充分、baseline 是否公平，属于另一层审查。

## 一个合成的公开风格例子

当前样例是一段合成的 forecasting note。它有两条主张、两个 figure stand-in、一个数据划分表、一份 raw rows CSV 和一份 analysis contract。运行方式保持为普通命令行：

```bash
cd projects/04-devtools/paper-figure-auditor
python3 paper_figure_auditor.py examples/public_paper_style_manifest.json \
  --root . \
  --output reports/public_paper_style_audit.md \
  --html-output reports/public_paper_style_audit.html \
  --site-output site/index.html \
  --fail-on-block
python3 -m unittest discover -s tests -v
```

这份合成样例的预期输出是：

```text
PAPER_FIGURE_AUDITOR_STATUS decision=ready-for-human-review claims=2 findings=0 blocks=0 review=0
```

`ready-for-human-review` 表示结构化链接没有发现阻塞项，可以进入人工审查。报告同时生成 Markdown、HTML 和一个静态页面，方便在公开前检查 claim、figure、table、evidence 和 caveat 是否一致。

## 为什么把它单独保留

这批工程资产中，有很多小工具更适合被合并到套件里。Paper Figure Auditor 被保留下来，是因为它对应一个独立、稳定、容易复现的研究工程问题：在论文或技术报告公开之前，先把图表主张和证据边界对齐。

它也适合和其他流程配合：实验表格完成后，可以先跑这个 gate；博客或 README 发布前，再检查文字是否超过图表和原始数据能支持的范围。它不需要外部服务，也不要求把私有论文或原始数据提交进工具仓库。

## 边界

Paper Figure Auditor 覆盖结构化链接、本地文件存在性、过宽表述和 caveat 覆盖。同行评审、统计验证、绘图正确性、实验设计、baseline 公平性和论文贡献仍然需要单独审查。
