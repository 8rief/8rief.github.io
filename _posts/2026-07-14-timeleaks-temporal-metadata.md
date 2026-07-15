---
layout: post
title: "TimeLeaks Lab：内容加密后，发布时间仍可能泄漏事件"
date: 2026-07-14 18:00:00 +0800
categories: research-notes
column: problem-exploration
column_title: "问题探究"
tags: [time-series, metadata, traffic-shaping, privacy]
---

> 代码状态：暂未公开。本文使用合成数据，只讨论可复现的攻击指标和研究边界。

设想一个私有告警服务：传感器原始值被加密，告警内容也不可见，外部观察者只能看到什么时候有输出、一次输出多少条。这样的接口仍可能暴露事故的开始时间、持续时长和严重程度。

TimeLeaks Lab 把这个问题缩成一个确定性模拟实验。输入是一段合成告警序列和发布策略，输出是攻击指标、延迟和额外流量。实验关注发布节奏，不接触真实工业数据。

## 先写清观察面

原始分数和阈值判定都发生在私有侧。外部观察者只获得每个时间点的消息数量，以及策略预先公开的固定基线。程序从观察数量中减去基线，再把正差值覆盖到对应发布窗口，得到对“事件是否活跃”的预测。

```text
合成私有分数 → 私有阈值 → 告警
                         ↓
                    发布策略
                         ↓
时间/数量元数据 → 减去公开基线 → 推断活跃窗口
                         ↘ 延迟、额外流量、丢弃
```

这个观察面很窄，但可以检验一个常被忽略的边界：内容密文没有变化，并不意味着输出节奏与事件无关。反过来，若生产接口还泄漏包长、连接标识或重试行为，当前模拟会低估攻击者能力。

## 最小实验

以下命令记录私有研究仓库的实验入口。公开代码与固定版本数据之前，读者还无法仅靠本文从零复现。

```bash
cd projects/02-academic/frontier-crypto-timeseries/timeleaks_lab
python3 timeleaks.py examples/industrial_alert_scenario.json \
  --output reports/industrial_alert_timeleaks.md \
  --html-output reports/industrial_alert_timeleaks.html
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

示例包含 144 个时间点和三段合成异常，共有 41 个时间点触发私有阈值。观察者不知道阈值和告警内容，只读取发布后的时间与数量元数据。

本次复跑的单元测试输出为：

```text
Ran 3 tests in 0.002s

OK
```

测试固定了三类行为：事件触发策略的活跃窗口 F1 高于固定填充；批处理引入延迟且仍保留可见信号；命令行能够生成 Markdown 与 HTML 报告。

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

## 指标怎样产生

- **活跃窗口 F1**：比较真实事件活跃位与观察者恢复的位；越高表示当前攻击越有效。
- **起点误差**：在事件前后有限搜索区间内，计算首个预测活跃点与真实起点的距离；完全漏检会得到惩罚值。
- **平均延迟**：只对实际交付的告警计算发布时间减原始时间。
- **输出开销**：发布消息数除以 41 条私有告警；固定填充发出 108 条，因此为 \(108/41=2.634\)。

`fixed-cadence-8-pad6` 每八个时间点公开发送六条消息。观察者知道六条是公开基线，减法后的差值始终为零，所以**当前这一种攻击**得到 F1=0。与此同时，每个窗口最多承载六条真实告警，样例中有七条被丢弃。这个结果描述的是一次容量受限实验，不构成 timing privacy 的通用证明。

## 当前研究边界

这是一段合成 trace 上的攻击显微镜，不是对任何已部署告警系统的测量。表中的策略也是内部基线，还没有复现公开 traffic-shaping 或 timing-privacy 系统。

当前五行只适合做同一实现内的 sanity baseline。Pacer 和 NetShaper 提供了更接近公开方案的比较锚点，但它们面向各自的系统与威胁模型。直接抄录论文吞吐量没有可比性；下一步要把机制适配到相同的告警发布接口，并统一带宽、延迟、丢弃和攻击者观察面。

## 下一步验证

接下来需要完成四件事：

1. 在不同事件密度、持续时间和 padding 预算下做参数扫描；
2. 引入许可证清楚的公开 trace，并记录预处理过程；
3. 复现 Pacer、NetShaper 一类公开 timing defense，在同一观察面和 utility budget 下比较；
4. 增加不依赖“公开固定基线”的攻击，检查包间隔、跨窗口相关性和容量溢出是否重新暴露事件。

如果简单固定节奏在统一预算下始终支配复杂策略，这条路线就应该停在 benchmark，而不是继续发明更复杂的 shaper。

## 常见误判

第一类误判是把内容加密等同于事件隐藏。密文内容不可读，发布时间、批大小、连接重试和容量溢出仍可能对应真实事件。

第二类误判是只报告 F1。固定节奏能压低当前攻击分数，但它同时增加输出、延迟和丢弃；没有 utility 口径的隐私分数不适合做设计结论。

第三类误判是把当前攻击失败写成通用安全。`fixed-cadence-8-pad6` 只让“减去公开基线”的这一种攻击失败；换成包间隔、容量溢出或跨窗口相关性攻击后，结论需要重新检查。

## 可以怎样练习

先固定一条 20 个时间点的玩具事件序列，手工跑三种策略：

```text
event_triggered_messages=
batch_messages=
fixed_cadence_messages=
active_window_score=
delay=
extra_messages=
drop_count=
```

练习时不要急着选最优策略。先确认每个指标回答的问题不同：F1 衡量当前攻击，delay 衡量可用性，extra messages 衡量带宽，drop 衡量业务损失。

## 参考资料

- [Pacer: Comprehensive Network Side-Channel Mitigation in the Cloud](https://www.usenix.org/conference/usenixsecurity22/presentation/mehta)
- [NetShaper: A Differentially Private Network Side-Channel Mitigation System](https://www.usenix.org/conference/usenixsecurity24/presentation/sabzi)
