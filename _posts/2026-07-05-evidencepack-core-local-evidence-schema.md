---
layout: post
title: "EvidencePack Core：证据包工具先要有一个稳定的数据骨架"
date: 2026-07-05 09:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [evidence, schema, local-first, documentation]
---

> 代码状态：暂未公开。本文记录一个本地 evidence-pack 渲染核心的设计。  
> 主题：本地工具 / 数据模型 / 证据整理

很多小工具一开始都能解决单个问题：搬家退租要整理照片，取消订阅要整理时间线，发票争议要整理行项目差异。把这些案例放在一起看，会发现它们共享同一个底层结构：参与方、时间线、证据清单、请求事项、备注和边界说明。

EvidencePack Core 的定位是抽出这部分共用能力：它提供一个本地优先的证据包骨架，读取结构化 JSON，校验基本字段，然后渲染成 Markdown/HTML。

## 证据包的最小模型

一个通用 evidence pack 不需要一开始就复杂。当前最小结构包含：

| 部分 | 作用 |
|---|---|
| summary | 说明这个包为什么存在、请求什么 |
| parties | 用 label 描述参与方，避免公开样例出现真实个人信息 |
| timeline | 把事件按时间排成可读顺序 |
| evidence manifest | 列出证据 ID、类型和说明 |
| neutral message | 生成克制的沟通文本，而不是情绪化投诉 |
| source notes | 标明样例数据来源和限制 |
| boundary | 明确不是法律、金融、医疗或专业建议 |

这几个字段并不花哨，但它们能防止证据工具变成散乱截图合集。

## 本地接口形状

代码整理公开后，使用方式会保持为本地命令：

```bash
python3 evidencepack.py examples/generic_repair_pack.json \
  --output reports/generic_repair_pack.md \
  --html-output reports/generic_repair_pack.html

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 -m unittest discover -s tests -v
```

测试重点很小：

- 合法输入能渲染核心章节；
- 重复 evidence ID 会被发现；
- CLI 能写出 Markdown 和 HTML；
- 输出保留边界声明，不把证据包包装成专业意见。

这类测试用于固定“工具到底保证什么”，避免后续改动破坏证据包语义。

## 为什么要统一 schema

如果每个 proof-style 小工具都自己拼字符串，很快会出现三个问题：

1. 同一种证据在不同工具里字段名不一致；
2. 静态展示页看起来相似，但无法复用测试；
3. 隐私边界和免责声明容易漏。

统一 schema 后，垂直工具只需要关心自己的业务字段。例如搬家场景关心房间、照片和押金扣款；取消订阅场景关心取消请求、后续扣费和沟通记录；发票场景关心 agreed line 和 invoiced line 的差异。它们最终都能落回同一套 evidence manifest 和 timeline。

## 隐私边界

EvidencePack Core 默认面向本地文件。它不上传数据，不调用外部 API，也不应该在公开样例里放真实账号、原始会话、浏览器配置、支付号或未脱敏个人材料。

这点比功能更重要。证据整理工具如果诱导用户把敏感材料集中到一个共享报告里，就会从“帮忙整理”变成“制造泄漏面”。所以样例数据必须是合成的，生成报告也必须要求分享前人工复核。

## 复用价值

这个核心模块的价值不在单独展示，而在让同类证据工具保持一致：所有 evidence-pack 类工具都可以复用同一种数据骨架、报告结构和测试思路。公开说明应让读者看到的不只是一个脚本，而是一组本地证据工具的公共底座。

## 设计目标与约束

EvidencePack Core 提供证据包的稳定数据骨架。很多小工具都需要保存文件、时间、来源、hash、备注和报告路径；如果每个项目都自定义格式，跨工具合并和审查会很困难。

## 实现细节

核心 schema 可以保持很小：

```json
{
  "schema_version": 1,
  "items": [
    {"id": "photo-001", "path": "photos/door.jpg", "sha256": "...", "captured_at": "2026-06-18T10:00:00+08:00", "note": "front door"}
  ]
}
```

`schema_version` 让格式可以演进；`sha256` 让材料可复查；`captured_at` 和 `note` 支撑时间线报告。

## 可复现示例

```bash
python3 evidencepack.py validate pack.json
python3 evidencepack.py report pack.json --output report.md
```

预期输出形状：

```text
schema_version=1
items=1
hashes_valid=true
report_ready=report.md
status=ok
```

## 输出怎么读

`hashes_valid=true` 说明 manifest 中记录的文件摘要与当前文件一致。它不能证明文件拍摄时就真实，只能证明打包后没有被静默改动。

## 常见误判

第一种误判是把 hash 当成事实证明。hash 只能说明“当前文件和 manifest 记录的字节一致”，不能证明文件内容的来源、拍摄时间或上下文真实。

第二种误判是把 schema 设计得过早复杂。证据包最先需要稳定的是 ID、时间、来源、文件摘要、说明和边界；如果一开始就塞入大量场景字段，垂直工具会难以复用。

第三种误判是把渲染报告当成脱敏报告。EvidencePack Core 只负责组织材料，不负责判断哪些字段可以公开；公开前仍要单独做隐私和本地路径检查。

## 可以怎样练习

可以先写一个三条记录的 `pack.json`：一张照片、一封邮件摘要、一条沟通记录。练习目标是让三条材料都能回答四个问题：它的 ID 是什么，来自哪里，如何校验，能支持哪一句请求。然后故意复制一个 evidence ID，观察 validator 应该怎样报告错误。

## 参考

- JSON Schema documentation: <https://json-schema.org/learn/getting-started-step-by-step>
- W3C PROV overview: <https://www.w3.org/TR/prov-overview/>

## 边界

schema 只描述材料结构，不替代事实核验、法律判断或隐私脱敏。公开展示时应使用合成路径和合成文件名。
