---
layout: post
title: "Dataset Governance Suite：数据集发布前先过一遍本地治理门"
date: 2026-06-23 22:05:00 +0800
categories: local-tools
tags: [dataset, governance, release, local-first]
---

> 代码状态：暂未公开。本文只记录设计目标、检查边界和可复现的接口形状。  
> 主题：数据集治理 / 发布前检查 / 本地工具

数据集发布的问题通常不是“能不能写一个 README”，而是几件事被拆散了：数据卡写了来源和用途，license 检查在另一个表里，敏感领域或个人数据风险又靠人工记忆。等到 benchmark、demo data 或博客材料准备公开时，最容易漏掉的就是这些边界。

Dataset Governance Suite 的收尾方式不是把两个小工具分别包装，而是把 Dataset Card Forge 和 Dataset License Gate 合成一条本地流程。输入是一份共享的 dataset-release manifest，输出是数据卡报告、license gate 报告、组合 Markdown/HTML 报告和一个静态页面。

## 这条流程检查什么

| 步骤 | 模块 | 作用 |
|---:|---|---|
| 1 | Dataset Card Forge | 记录来源、license、隐私、consent、用途、禁用场景、split 和 release finding |
| 2 | Dataset License Gate | 检查 redistribution、commercial use、personal data、sensitive domain、attribution 和 terms review |

这不是为了替代法律或隐私审查，而是为了让“数据集为什么可以公开、哪些部分必须 review”在发布前变成可复查的本地证据。

## 本地接口形状

代码整理公开后，最小使用方式会保持成这种形式：

```bash
cd suites/dataset-governance-suite
python3 dataset_governance_suite.py --output-root .
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

当前样例是一份合成的 sensor benchmark release manifest。它包含一个可以进入人工发布审查的合成 benchmark，以及一个只用于演示 review routing 的 public sensitive-domain reference row。预期结果是：

| 检查 | 结果 |
|---|---|
| suite decision | ready-with-review-notes |
| dataset card findings | 0 |
| license publish-ok datasets | 1 |
| license review datasets | 1 |
| license blocked datasets | 0 |

这里的 `ready-with-review-notes` 表示：合成 benchmark 的结构化材料没有发现阻塞项，但敏感领域参考行必须继续人工审查，不能被默认为可直接打包发布。

## 为什么这样收尾

Dataset Card Forge 和 Dataset License Gate 单独看都只是小工具。真正有展示价值的是把它们连起来：先说清数据是什么，再判断发布风险。这样比两个分散 README 更接近真实的数据发布动作，也更容易和后续 benchmark、论文实验或公开 demo 对接。

这也是整个工程资产收尾的原则：能合并成一条清楚流程的，就不要拆成多个看似独立的产品；没有足够差异化或边界成本过高的工具，就归档或停止投入。

## 边界

Dataset Governance Suite 不是法律建议、隐私认证、SPDX 合规证明，也不能替代阅读原始数据条款。它适合做公开前的本地治理预检，让明显的来源、用途、license 和敏感领域问题先被看见；最终能否发布，仍然要根据具体数据来源和风险做人工判断。
