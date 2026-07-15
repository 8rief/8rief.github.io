---
layout: post
title: "Time-Series Attack Zoo：把隐私侧信道实验变成可比较的攻击卡片"
date: 2026-07-10 09:00:00 +0800
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

如果你想把它推进成可比较的 benchmark artifact，关键工作是把摘要分数下沉为 raw rows，并让每张卡都绑定公开 trace、明确 threat model 和外部 baseline。只有这样，读者才能判断结果来自攻击能力、防御开销，还是实验数据本身。

## 设计目标与约束

这个工具的核心目标是把“时间侧信道实验”整理成同一种攻击卡片，避免把每个实验都写成散落的脚本说明。卡片需要固定记录攻击假设、输入 trace、泄漏变量、评估指标和复现实验命令。这样做的原因很直接：没有统一字段时，不同攻击之间无法比较，也很难说明某个结果到底来自数据、模型还是实验边界。

约束有三条：第一，默认只使用合成 trace 或公开样例；第二，卡片先服务于比较和复查，不直接声称真实系统风险等级；第三，每张卡片必须能给出最小可运行命令和一段可解释输出。

## 实现细节

一张攻击卡片可以用 YAML 表示：

```yaml
id: burst-timing-baseline
threat_model: observer sees event timestamps only
input_trace: synthetic_bursts.csv
leakage_signal: inter_arrival_time
metric: auc
baseline: shuffled_timestamp
boundary: synthetic trace, no real user data
```

生成器读取卡片后做三件事：校验字段、运行指定实验、把结果写成 Markdown 表格。卡片字段固定后，同一个报告可以接入多类攻击，减少为每个实验单独写解释页面的重复工作。

## 可复现示例

```bash
python3 attack_zoo.py cards/burst-timing-baseline.yaml --output reports/burst_card.md
```

预期输出形状：

```text
card=burst-timing-baseline
trace=synthetic_bursts.csv
metric_auc=0.81
baseline_auc=0.50
status=reviewable
```

## 输出怎么读

`metric_auc=0.81` 说明在这个合成 trace 上，攻击特征确实比随机 baseline 更能区分事件状态；`baseline_auc=0.50` 给出随机参照；`status=reviewable` 只表示卡片字段和结果齐全，不表示真实系统已经被证明存在同等风险。

## 常见误判

第一个误判是把 AUC 写成漏洞等级。AUC 只是在给定 trace、攻击者观察面和标签定义下的区分能力；真实系统风险还取决于数据生成过程、攻击者能力、重复实验和防御成本。

第二个误判是只报告 defended score。防御把分数压低之后，还要同时报告延迟、dummy work、吞吐余量或 utility 损失，否则无法和固定 envelope 这类朴素 baseline 比较。

第三个误判是让每张攻击卡自己定义字段。字段不统一时，结果看似丰富，实际无法比较：有的卡缺 threat model，有的卡缺 baseline，有的卡缺 claim boundary。

## 可以怎样练习

写两张攻击卡：一张只观察发布时间，一张观察窗口计数。两张卡必须使用同一组字段：hidden fact、observable metadata、attacker、metric、baseline、defense、cost、boundary。练习目标是让读者能直接比较“攻击强度”和“防御代价”，而不是在两段散文里寻找口径。

## 参考

- The Turing Way reproducible research guide: <https://book.the-turing-way.org/reproducible-research/reproducible-research/>
- scikit-learn ROC/AUC metrics documentation: <https://scikit-learn.org/stable/modules/model_evaluation.html#roc-metrics>

## 边界

这个项目展示的是实验组织方式，不发布真实用户 trace，不把合成数据上的 AUC 外推为真实攻击成功率。若要进入研究报告，还需要写清数据生成过程、攻击者能力、重复实验和置信区间。
