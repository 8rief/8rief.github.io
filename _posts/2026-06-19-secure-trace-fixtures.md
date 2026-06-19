---
layout: post
title: "安全时序实验先统一 trace：一个小型 fixture library 的作用"
date: 2026-06-19 12:50:00 +0800
categories: research-tools
tags: [datasets, fixtures, time-series, reproducibility]
---

> 代码状态：暂未公开。库内只有合成 JSON，不包含用户记录或生产遥测。

当多个侧信道模拟器各自定义输入格式时，同一个“事件”会被写成不同字段：有的用整数时间，有的用 ISO 时间；有的把 cohort 放在标签里，有的直接省略；更严重的是，hidden label 和 public metadata 可能混在一起，实验脚本无意中读到了攻击者本不该看到的信息。

Secure Trace Fixture Library 提供一个很小的统一入口。它不追求大数据量，只负责验证 trace 的结构和泄漏边界。

## 最小接口

```bash
cd projects/02-academic/frontier-crypto-timeseries/secure_trace_fixture_library
python3 trace_fixture_library.py examples/fixture_pack.json \
  --output reports/fixture_pack.md \
  --html-output reports/fixture_pack.html \
  --emit-json reports/normalized_traces.json
python3 -m unittest discover -s tests -v
```

当前 fixture pack 只有三条记录：时间戳、cohort、hidden label，以及一个只允许公开字段进入的 metadata map。规模很小，足够测试解析、排序、字段约束和负面边界。

## 为什么 hidden/public 分离很重要

一个时间侧信道实验至少有三层数据：

1. **hidden ground truth**：用于给攻击结果打标签；
2. **public observation**：攻击者真正能读取的时间、数量或分组元数据；
3. **evaluation metadata**：种子、场景说明、许可证和预处理记录。

如果攻击函数直接拿到 hidden label，AUC 再高也没有意义。fixture validator 应在实验开始前拒绝字段越界，而不是等论文审稿时才靠人工发现。

## 当前边界与下一步

三条合成记录只能证明格式和测试能运行，不能证明攻击有效。将来接入公开数据时，每个 pack 还要增加：

- source URL 与 license；
- 下载版本或 hash；
- preprocessing 脚本；
- 时间单位、缺失值和重采样规则；
- hidden/public 字段映射；
- 不允许公开的原始标识符。

这个小库的价值在于让后续 TimeLeaks、participation leakage 和 timing shaper 使用同一份输入合同。研究结果是否成立要由攻击、baseline 和真实实验回答；fixture library 只保证这些问题建立在可复查的数据边界上。

