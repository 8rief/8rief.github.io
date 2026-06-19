---
layout: post
title: "参与者集合也是数据：安全聚合之外的时间侧信道"
date: 2026-06-19 12:20:00 +0800
categories: research-notes
tags: [federated-learning, secure-aggregation, metadata, privacy]
---

> 代码状态：暂未公开。实验只使用合成参与记录，不涉及真实用户或生产系统。

安全聚合可以隐藏每个客户端上传的内容，但系统往往还会暴露每轮有多少客户端参与、来自哪些分组、哪些客户端持续掉线。这些序列可能对应区域故障、设备停机或组织活动。

Temporal Participation Leakage Lab 检查一个窄问题：观察者只看到 active-set 元数据时，能否定位隐藏事件及其目标分组？

## 实验接口

```bash
cd projects/02-academic/frontier-crypto-timeseries/temporal_participation_leakage_lab
python3 participation_leakage.py examples/federated_outage_participation.json \
  --output reports/federated_outage_participation.md \
  --html-output reports/federated_outage_participation.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

样例包含 96 轮、四个区域分组和两个隐藏事件：北部区域参与率下降，西部区域参与率上升。内容始终不可见，攻击只读取 roster 或计数序列。

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

## 论文比较需要补什么

当前只有内部策略之间的比较。要进入论文实验，至少要补齐：

- 公开系统实际暴露哪些 roster/count/timing 字段；
- 与固定 cadence、window batching、正式 timing privacy 机制的直接比较；
- 多条公开或可发布 trace，而不是单个合成事件；
- 一个清楚的 adjacency 与攻击者辅助信息模型。

如果目标应用明确把参与日程视为公共信息，这条攻击就没有安全意义。反过来，如果参与变化对应敏感事件，系统设计就不能只检查 update payload。

## 参考入口

- [Practical Secure Aggregation for Privacy-Preserving Machine Learning](https://eprint.iacr.org/2017/281)
- [Differentially Private Federated Learning: A Client Level Perspective](https://arxiv.org/abs/1712.07557)

