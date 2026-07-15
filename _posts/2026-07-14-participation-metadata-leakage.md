---
layout: post
title: "参与者集合也是数据：安全聚合之外的时间侧信道"
date: 2026-07-14 09:00:00 +0800
categories: research-notes
column: problem-exploration
column_title: "问题探究"
tags: [federated-learning, secure-aggregation, metadata, privacy]
---

> 代码状态：暂未公开。实验只使用合成参与记录，不涉及真实用户或生产系统。

安全聚合可以隐藏每个客户端上传的内容，但系统往往还会暴露每轮有多少客户端参与、来自哪些分组、哪些客户端持续掉线。这些序列可能对应区域故障、设备停机或组织活动。

Temporal Participation Leakage Lab 检查一个窄问题：观察者只看到 active-set 元数据时，能否定位隐藏事件及其目标分组？

## 为什么聚合值安全还不够

安全聚合的核心目标是让服务器只得到聚合结果，无法读取单个客户端的更新。这个目标并不会自动约束系统在调度层公开什么：参与总数、分组计数、稳定客户端标识和发布时间都可能位于协议声明的泄漏边界之外。

因此，分析前要先写观察契约。这个实验让攻击者读取发布策略产生的计数序列，不读取模型更新、原始设备状态或隐藏事件标签。需要保护的秘密是“某轮是否发生事件”以及“事件影响哪个分组”。若具体系统已经把参与日程声明为公共信息，这项攻击不构成对该系统安全声明的反例。

## 实验接口

下面的命令是当前私有研究仓库中的实验入口，用于说明结果如何生成；代码公开前，它还不能充当读者可直接克隆的复现说明。

```bash
cd projects/02-academic/frontier-crypto-timeseries/temporal_participation_leakage_lab
python3 participation_leakage.py examples/federated_outage_participation.json \
  --output reports/federated_outage_participation.md \
  --html-output reports/federated_outage_participation.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

样例包含 96 轮、四个区域分组和两个隐藏事件：北部区域参与率下降，西部区域参与率上升。内容始终不可见，攻击只读取 roster 或计数序列。

实验使用固定随机种子，对每个客户端逐轮做 Bernoulli 采样。隐藏事件只改变对应分组的参与概率，随后发布策略把私有分组计数转换为观察值：

```text
隐藏事件与基础参与率
        ↓
逐客户端采样得到私有分组计数
        ↓
总数 / 分组桶 / 时间窗口 / 固定 envelope
        ↓
攻击分数 → 事件 AUC、目标分组 AUC
        ↘ padding、延迟、utility
```

当前攻击分数为：

\[
S=1.4\log(1+g)+0.9\log(1+n)+1.8\log(1+r),
\]

其中 \(g\) 是目标分组的公开计数，\(n\) 是公开总数，\(r\) 是 roster 代理信号。这里的 `linkable-client-roster` 仍是简化模型：代码把各组公开计数的最大值作为稳定 roster 信号，并未实现真实客户端 ID 的跨轮链接。因此，这一行可以用于敏感性测试，不能支持“已经完成重识别攻击”的结论。

## 元数据粒度改变了什么

| 发布策略 | 事件 AUC | 目标分组 AUC | padding | 延迟 | utility |
|---|---:|---:|---:|---:|---:|
| linkable-client-roster | 0.584 | 1.000 | 0.000 | 0 | 1.000 |
| per-group-counts | 0.730 | 1.000 | 0.000 | 0 | 1.000 |
| total-count-only | 0.555 | 0.995 | 0.000 | 0 | 1.000 |
| bucketed-group-counts-k16 | 0.676 | 1.000 | 0.137 | 0 | 0.879 |
| windowed-total-count-w4 | 0.514 | 0.548 | 0.000 | 3 | 1.000 |
| fixed-envelope-per-group | 0.500 | 0.500 | 0.197 | 0 | 0.835 |

分组计数在这条 trace 上足以定位目标区域。只发布总数降低了事件区分度，却仍可能通过各组对总量的影响猜测目标。四轮窗口把 AUC 拉近随机水平，但引入三轮延迟。固定 envelope 达到 0.5，同时消耗约 19.7% padding，并把 utility 降到 0.835。

这组结果说明“内容保密”和“参与模式保密”需要分开建模。它不表示安全聚合协议失效；participation metadata 可能本来就位于协议泄漏边界之外。

## 怎样读 AUC

程序先计算普通方向 AUC，再报告 \(\max(\mathrm{AUC},1-\mathrm{AUC})\)。因此，无论事件使参与数上升还是下降，只要两类分数可区分，结果都会高于 0.5；0.5 才表示当前打分器接近随机猜测。

“目标分组 AUC”目前只评估场景中第一个事件所属分组，也就是 `north`。表格不能据此证明攻击能在任意数量的候选分组中完成归因。事件 AUC 则把两个事件的活跃轮次合并为正类。目标定义不同，二者不能互换。

本次复跑得到：

```text
Ran 4 tests in 0.014s

OK
```

测试覆盖三项关键关系：分组计数比仅总数泄漏更多；固定 envelope 以 padding 和 utility 损失换取更低 AUC；四轮窗口确实增加延迟。它们验证实现约束，没有把单条合成 trace 提升为一般规律。

## 下一步：怎样形成可比较的研究实验

当前只有内部策略之间的比较。要进入论文实验，至少要补齐：

- 公开系统实际暴露哪些 roster/count/timing 字段；
- 与固定 cadence、window batching、正式 timing privacy 机制的直接比较；
- 多条公开或可发布 trace，而不是单个合成事件；
- 一个清楚的 adjacency 与攻击者辅助信息模型。

当前表格属于受控消融，不是公开基线比较。原因很具体：这些策略共享同一模拟器和成本口径，而现有安全聚合论文的主要目标通常是更新内容与多轮协议安全，不能直接拿论文中的通信数字替代 active-set 攻击指标。最近的合适锚点是多轮安全聚合工作；后续需要先复现其威胁模型，再把双方放到同一观察契约下测量。

下一轮实验还应加入“多候选分组识别”任务，并用真实可链接标识与辅助信息替换 roster 代理。若该攻击在公开 trace、统一通信预算和更强基线下回到随机水平，这条路线应停止扩展。

如果目标应用明确把参与日程视为公共信息，这条攻击就没有安全意义。反过来，如果参与变化对应敏感事件，系统设计就不能只检查 update payload。

## 常见误判

第一类误判是把安全聚合的内容安全扩展到调度元数据。安全聚合隐藏的是客户端更新内容；参与计数、轮次、重试和掉线模式是否公开，需要由系统泄漏合同单独声明。

第二类误判是把目标分组 AUC 读成多类归因能力。当前表格只评估样例里第一个事件的目标分组，不能证明攻击可以在任意候选集合中稳定定位所有事件。

第三类误判是把单条合成 trace 当成普遍规律。合成 trace 的价值是做受控消融；正式研究需要多个 trace、公开预处理、统一预算和公开 baseline。

## 可以怎样练习

复查这类实验时先写四行：

```text
observed_fields=total/per_group/roster/timing
secret=event_presence/event_group/client_identity
positive_label_definition=
baseline_to_compare=fixed_cadence/window_batching/timing_privacy_system
```

然后分别计算事件检测和目标归因。若两个任务混在同一个分数里，结论会很容易越界。

## 参考入口

- [Practical Secure Aggregation for Privacy-Preserving Machine Learning](https://eprint.iacr.org/2017/281)
- [Differentially Private Federated Learning: A Client Level Perspective](https://arxiv.org/abs/1712.07557)
- [Securing Secure Aggregation: Mitigating Multi-Round Privacy Leakage in Federated Learning](https://arxiv.org/abs/2106.03328)
