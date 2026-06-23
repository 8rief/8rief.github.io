---
layout: post
title: "Time-Series Attack Zoo：把隐私侧信道实验变成可比较的攻击卡片"
date: 2026-06-19 12:40:00 +0800
categories: research-tools
column: project-showcase
column_title: "项目展示"
tags: [time-series, privacy, benchmark, reproducibility]
---

> 代码状态：暂未公开。攻击卡片汇总合成实验，不指向任何生产服务。

隐私研究很容易积累一批互不相容的小脚本：一个报告 AUC，一个报告延迟，另一个只写“存在泄漏”。Time-Series Attack Zoo 统一这些实验的描述方式，让每条攻击都回答同一组问题：隐藏事实是什么、观察者看见什么、分数如何计算、防御是什么、代价在哪里、结论边界到哪一步。

## 一张攻击卡应包含什么

当前 schema 要求以下字段：

- hidden fact；
- observable metadata；
- attacker 与 metric；
- baseline score 与 defended score；
- defense 和 cost；
- source artifact；
- claim boundary。

只有攻击分数，没有防御成本，无法判断研究价值。只有一个 defense，也无法知道它保护了什么观察面。claim boundary 用来阻止合成实验被误写成生产漏洞。

## 运行方式

```bash
cd projects/02-academic/frontier-crypto-timeseries/time_series_attack_zoo
python3 attack_zoo.py examples/frontier_attacks.json \
  --output reports/frontier_attack_zoo.md \
  --html-output reports/frontier_attack_zoo.html \
  --fail-on-findings
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

`--fail-on-findings` 检查的是卡片字段和边界缺失，不代表对生产系统做了漏洞扫描。当前五张卡通过 schema 校验。

## 当前五类问题

| 攻击卡 | 隐藏事实 | 观察面 | 当前简单防御 |
|---|---|---|---|
| temporal-release-cadence | 事故开始和持续时间 | 发布时间与数量 | fixed cadence + padding |
| multi-client-conflict-retry | 同一事件冲突和突发结构 | retry、queue、version bucket | constant-rate envelope |
| semilattice-lifecycle-residue | 事件生命周期阶段 | lifecycle count、merge/writeback shape | fixed merge/writeback schedule |
| active-set-participation | 分组事件时间 | cohort participation count | fixed per-group envelope |
| dp-timing-shaper-frontier | 噪声发布后的事件时间 | noisy/windowed counts | window 或 fixed envelope |

这些卡片共享一个明显现象：固定 envelope 往往能把合成攻击分数压到随机水平，同时带来 dummy work、吞吐余量、延迟或 utility 损失。它因此是必须保留的朴素 baseline。若一个新防御不能在相同 utility budget 下优于它，就没有必要继续增加复杂度。

## 这个工具解决的是研究管理问题

Attack Zoo 本身不构成论文贡献。它更像实验注册表：保证不同模拟器使用可比字段，并记录哪些结果仍是 synthetic、哪些 defense 尚未复现、哪些方向应被 kill。

下一阶段要把摘要分数下沉为 raw rows，并让每张卡都绑定公开 trace、明确 threat model 和外部 baseline。完成这些工作后，它才可能成为 benchmark artifact 的入口。

