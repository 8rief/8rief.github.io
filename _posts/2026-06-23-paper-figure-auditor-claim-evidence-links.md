---
layout: post
title: "Paper Figure Auditor：把论文里的图表主张连回证据"
date: 2026-06-23 21:30:00 +0800
categories: local-tools
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

`ready-for-human-review` 不是“可以直接发表”，而是“结构化链接没有发现阻塞项，可以进入人工审查”。报告同时生成 Markdown、HTML 和一个静态页面，方便在公开前检查 claim、figure、table、evidence 和 caveat 是否一致。

## 为什么把它单独保留

这批工程资产中，有很多小工具更适合被合并到套件里，而不是单独展示。Paper Figure Auditor 被保留下来，是因为它对应的是一个独立、稳定、容易复现的研究工程问题：在论文或技术报告公开之前，先把图表主张和证据边界对齐。

它也适合和其他流程配合：实验表格完成后，可以先跑这个 gate；博客或 README 发布前，再检查文字是否超过图表和原始数据能支持的范围。它不需要外部服务，也不要求把私有论文或原始数据提交进工具仓库。

## 边界

Paper Figure Auditor 不是同行评审、统计验证、绘图正确性检查或创新性判断。它只检查结构化链接、本地文件存在性、过宽表述和 caveat 覆盖。真正的实验设计、baseline 公平性、统计方法和论文贡献，仍然需要单独审查。
