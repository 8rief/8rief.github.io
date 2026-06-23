---
layout: post
title: "Research Claim Ledger：先把结论和证据绑在一起"
date: 2026-06-18 03:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [research, reproducibility, evidence, local-first]
---

> 代码状态：暂未公开。本文记录一个本地 claim 审查工具的设计边界。  
> 主题：研究工程 / 证据链 / 公开写作

研究和工程展示里有一种很常见的失真：实验报告只支持一个很窄的结论，README、摘要或演示文案却慢慢写成了更大的承诺。这个问题不一定来自故意夸大，更多时候是材料分散造成的：图在一个目录，测试在另一个目录，边界条件写在笔记里，最后公开页面只留下了一句“效果很好”。

Research Claim Ledger 想解决的就是这件小事：每一个准备公开的 claim，都必须带上证据、适用范围和 caveat。没有证据的结论不自动通过；没有边界的结论也不应直接进入论文、README 或展示页。

## 账本里应该有什么

一个 claim 不是一句孤立的宣传语。它至少应该能回答四个问题：

| 字段 | 作用 |
|---|---|
| claim text | 准备公开说什么 |
| scope | 这句话在哪个数据集、攻击模型、系统版本或实验设置下成立 |
| evidence | 哪些测试、报告、原始数据、证明草稿或用户反馈支撑它 |
| caveat | 这句话不能推出什么 |

最小账本可以是一个 JSON 文件，也可以是 YAML 或表格。关键不在格式，而在约束：claim 不能脱离 evidence 单独存活。

## 一个典型失败样例

工具样例里故意放了一个会被阻塞的 claim：

```text
ES-ORAM provides a full malicious-client multi-client ORAM construction.
```

它的问题不是语法，而是边界过大。若当前材料只证明了某个语法约束下的局部泄漏闭包，或者只展示了合成 workload 上的某个指标，就不能把它写成完整 ORAM 构造。正确做法通常有两个：要么补齐证明和实验，要么把 claim 降级成 hypothesis 或 narrower result。

这类检查最好发生在公开之前，而不是论文投稿、项目发布或答辩展示之后。

## 本地接口形状

代码整理公开后，最小复现方式会保持成这种形式：

```bash
python3 claim_ledger.py examples/outcome_claims.json \
  --output reports/outcome_claims.md \
  --html-output reports/outcome_claims.html

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 -m unittest discover -s tests -v
```

当前样例测试覆盖几类行为：

- 没有 evidence 的 supported claim 会被阻塞；
- ready claim 必须有 verified evidence、scope 和 caveat；
- product claim 若没有用户反馈或使用证据，不能写得像已经验证；
- CLI 会输出 Markdown/HTML 报告，并在存在阻塞项时给出失败状态。

这不是证明系统，而是发布 hygiene 工具。

## 为什么不用普通 checklist

Checklist 的问题是它经常和材料分离。Research Claim Ledger 选择把 claim 和 evidence 写在同一个可运行输入里，再由脚本生成报告。这样有三个好处：

1. 公开文案改强了，账本会暴露出证据缺口；
2. 证据文件移动或失效，报告能提醒重新审查；
3. 多个项目共用同一种 claim/evidence/caveat 结构，后续更容易审计。

这也符合更大的研究工程原则：可复现不只是“代码能跑”，还包括“结论能回到证据”。

## 使用边界

Research Claim Ledger 不能判断一个理论证明是否正确，也不能替代同行评审。它只做一个更早、更机械的检查：公开语句有没有超出当前证据范围。

如果一个 claim 被标记为 ready，也只表示账本所声明的 evidence、scope 和 caveat 是完整的；它不等于结论真实，更不等于可以免读原始报告。

## 参考

- ACM Artifact Review and Badging: <https://www.acm.org/publications/policies/artifact-review-and-badging-current>
- SLSA provenance concepts: <https://slsa.dev/provenance/>
- The Turing Way reproducible research guide: <https://book.the-turing-way.org/reproducible-research/reproducible-research/>
