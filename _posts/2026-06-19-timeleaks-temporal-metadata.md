---
layout: post
title: "TimeLeaks Lab：内容加密后，发布时间仍可能泄漏事件"
date: 2026-06-19 12:10:00 +0800
categories: research-notes
tags: [time-series, metadata, traffic-shaping, privacy]
---

> 代码状态：暂未公开。本文使用合成数据，只讨论可复现的攻击指标和研究边界。

设想一个私有告警服务：传感器原始值被加密，告警内容也不可见，外部观察者只能看到什么时候有输出、一次输出多少条。这样的接口仍可能暴露事故的开始时间、持续时长和严重程度。

TimeLeaks Lab 把这个问题缩成一个确定性模拟实验。输入是一段合成告警序列和发布策略，输出是攻击指标、延迟和额外流量。实验关注发布节奏，不接触真实工业数据。

## 最小实验

```bash
cd projects/02-academic/frontier-crypto-timeseries/timeleaks_lab
python3 timeleaks.py examples/industrial_alert_scenario.json \
  --output reports/industrial_alert_timeleaks.md \
  --html-output reports/industrial_alert_timeleaks.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

示例包含 144 个时间点和三段合成异常，共有 41 个时间点触发私有阈值。观察者不知道阈值和告警内容，只读取发布后的时间与数量元数据。

## 五种发布策略

| 策略 | 含义 |
|---|---|
| event-triggered | 一有告警就发送 |
| random-delay-8 | 在 8 个时间点内随机延迟 |
| batch-8-leaky-size | 每 8 个时间点批量发送，但保留真实批大小 |
| bucketed-batch-8x4 | 固定窗口，并把数量填充到桶边界 |
| fixed-cadence-8-pad6 | 固定节奏，每次填充到固定数量 |

合成样例的结果很直观：

| 策略 | 活跃窗口 F1 | 起点误差 | 平均延迟 | 输出开销 |
|---|---:|---:|---:|---:|
| event-triggered | 0.988 | 0.333 | 0.000 | 1.000× |
| random-delay-8 | 0.479 | 4.000 | 4.561 | 1.000× |
| batch-8-leaky-size | 0.857 | 0.000 | 3.854 | 1.000× |
| bucketed-batch-8x4 | 0.857 | 0.000 | 3.854 | 1.171× |
| fixed-cadence-8-pad6 | 0.000 | 26.000 | 4.559 | 2.634× |

事件触发几乎直接暴露活跃窗口。随机延迟降低了时间定位能力，但严重程度与输出数量的相关性仍然存在。固定节奏在这条样例上把当前攻击分数压到最低，同时付出 2.634 倍输出和少量丢弃。

这个表不能支持“固定节奏最好”的一般结论。它只说明三个变量必须同时报告：泄漏、延迟和额外流量。只展示隐私分数，会把 padding 成本藏起来；只展示延迟，也会忽略发布时间本身携带的信息。

## 当前研究边界

这是一段合成 trace 上的攻击显微镜，不是对任何已部署告警系统的测量。表中的策略也是内部基线，还没有复现公开 traffic-shaping 或 timing-privacy 系统。

下一步需要完成三件事：

1. 在不同事件密度、持续时间和 padding 预算下做参数扫描；
2. 引入许可证清楚的公开 trace，并记录预处理过程；
3. 复现公开的 timing defense，在同一观察面和 utility budget 下比较。

如果简单固定节奏在统一预算下始终支配复杂策略，这条路线就应该停在 benchmark，而不是继续发明更复杂的 shaper。

