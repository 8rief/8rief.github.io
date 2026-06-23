---
layout: post
title: "给参与计数加 Laplace 噪声，为什么仍藏不住事件时间"
date: 2026-06-19 12:30:00 +0800
categories: research-notes
column: problem-exploration
column_title: "问题探究"
tags: [differential-privacy, metadata, federated-learning, benchmarking]
---

> 代码状态：暂未公开。本文中的 epsilon 是单次计数发布参数，不代表端到端隐私保证。

发现参与计数会泄漏事件后，一个自然想法是给每轮计数加入 Laplace 噪声。DP Timing Shaper Workbench 用同一条合成 outage trace 比较噪声、分桶、窗口、随机 drop/dummy 和固定 envelope，检查泄漏、误差、延迟与开销是否真的形成可用折中。

## 复现实验

```bash
cd projects/02-academic/frontier-crypto-timeseries/dp_timing_shaper_workbench
python3 dp_timing_shaper.py examples/federated_outage_shaping.json \
  --output reports/federated_outage_shaping.md \
  --html-output reports/federated_outage_shaping.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

## 当前样例的结果

| shaper | 事件 AUC | 目标 AUC | RMSE | padding | delay | utility |
|---|---:|---:|---:|---:|---:|---:|
| raw-group-counts | 0.738 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| laplace-eps1-group | 0.730 | 1.000 | 1.394 | 0.009 | 0.000 | 0.984 |
| laplace-eps0.5-group | 0.704 | 1.000 | 2.955 | 0.020 | 0.000 | 0.963 |
| bucketed-k16 | 0.676 | 1.000 | 8.720 | 0.137 | 0.000 | 0.879 |
| windowed-w4-total | 0.514 | 0.548 | 189.119 | 0.000 | 0.757 | 1.000 |
| fixed-envelope-per-group | 0.500 | 0.500 | 21.034 | 0.331 | 0.000 | 0.745 |

单次计数噪声增加了误差，却没有改变“哪个分组发生了事件”这一分类结果：目标 AUC 仍为 1.0。原因并不神秘。攻击利用的是跨轮次的结构和分组差异，单轮独立噪声未必足以隐藏持续事件。

窗口总量明显降低了时间定位能力，但把多轮信息合并在一起；表里的 delay 是归一化指标，不应和系统毫秒延迟混用。固定 envelope 在样例上达到随机水平，代价是 33.1% padding、少量 drop 和 utility 损失。

## epsilon 不能孤立解释

`eps=1` 和 `eps=0.5` 只描述每次 Laplace 计数发布。96 轮连续发布会发生 composition，且发布时刻本身仍然可能泄漏。没有 adjacency relation、正式 accountant 和部署泄漏合同，就不能把这份报告写成“系统满足 epsilon-DP”。

这个负结果反而有用：它阻止我们把“加噪”当成自动有效的防御。论文实验应把 privacy、RMSE、padding、drop、delay 和 utility 放在同一张 frontier 表中。

## 继续条件

下一步先复现公开 timing-privacy 或 traffic-shaping baseline。若所有有意义的点最终都退化为固定 envelope，这条路线应收缩为 benchmark 和工程边界分析；复杂 shaper 没有独立贡献。

## 参考入口

- [The Algorithmic Foundations of Differential Privacy](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf)
- [Practical Secure Aggregation for Privacy-Preserving Machine Learning](https://eprint.iacr.org/2017/281)

