---
layout: post
title: "RedactProof：黑框遮住内容，不等于文件已经脱敏"
date: 2026-06-18 02:10:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [redaction, pdf, privacy, local-first]
---

> 代码状态：暂未公开。本文只记录设计目标、检查边界和可复现的接口形状。  
> 主题：安全数据系统 / 工程实践 / 本地工具

很多人做 PDF 脱敏时会先想到“画一个黑框”。这个动作在屏幕上有效，但在文件层面未必有效：文字可能仍然可选择，批注层可能还在，文档属性里可能保留作者或标题，表单字段和附件也可能没有被清掉。

RedactProof 针对的就是这个窄问题：分享 PDF 或截图前，先在本地做一次红线检查，看看文件里是否还有常见的脱敏残留迹象。它的定位是发布前预检：把“看起来遮住了”和“文件结构里已经清掉了”这两件事分开检查，帮助用户在进入正式 redaction/sanitize 流程前发现低级残留。

## 设计边界

RedactProof 的输入是本地文件，输出是本地 Markdown/HTML 报告。报告只说明命中的规则和修复建议，不复制敏感原文。

第一版重点检查几类常见失败模式：

| 检查项 | 风险 |
|---|---|
| selectable text operators | 视觉上被盖住的文字仍可能被复制 |
| black-box overlay | 黑色矩形可能只是覆盖层，底层对象仍可能保留 |
| metadata object | 文档属性中可能残留作者、标题、软件信息 |
| annotations/comments | 批注、评论、高亮可能作为单独对象保留 |
| form/widget markers | 表单字段可能还在 |
| embedded-file markers | 附件或命名对象可能被忽略 |

报告里的 `risk-found` 表示发现了这些迹象；`no-obvious-risk` 只表示当前规则没有命中，不等于文件已经安全。

## 技术实现细节

RedactProof 的实现刻意保持在文件结构层。原因很直接：视觉遮挡是否充分需要图像语义判断；PDF 是否还包含可选择文字、批注对象、metadata 或 embedded file marker，则可以用确定性的字节/对象规则先挡掉一批低级错误。

当前流程分成四层：

1. **输入层**：只读取本地文件，不上传、不调用外部服务；样例由脚本生成，避免把真实隐私文件带进仓库。
2. **规则层**：对 PDF 常见对象和操作符做启发式扫描，例如文本绘制操作、annotation/form/embed 标记、metadata 对象和黑色矩形覆盖迹象。
3. **报告层**：把命中的规则、风险说明和修复建议写成 Markdown/HTML；报告描述风险，不复制疑似敏感原文。
4. **展示层**：生成静态 `site/index.html`，让结果可以在没有服务端的情况下直接打开。

第一版没有引入完整 PDF parser 或 OCR，因为目标是发布前本地预检，而非还原全部 PDF 语义。启发式规则依赖少、速度快、可解释；相应代价是覆盖范围有限，只能发现“常见残留迹象”。

## 本地接口形状

代码整理公开后，最小使用方式会保持成这种形式：

```bash
python3 redactproof.py \
  --write-sample examples/bad_redaction.pdf \
  examples/bad_redaction.pdf \
  --output reports/bad_redaction_report.md \
  --html-output reports/bad_redaction_report.html \
  --site-output site/index.html

python3 redactproof.py \
  --write-sample-image examples/flattened_redaction.png \
  examples/flattened_redaction.png \
  --output reports/flattened_redaction_report.md \
  --html-output reports/flattened_redaction_report.html \
  --site-output site/index.html

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

示例文件都是合成的：一个是不安全的 PDF 覆盖层，另一个是扁平化 PNG。这样演示不依赖真实隐私文件，也能稳定复现两种结果：前者应得到 `risk-found`，后者在当前 PDF 标记规则下应得到 `no-obvious-risk`。

## 更稳妥的工作流

一个可执行的低风险流程是：

1. 能在源文件中删除的内容，优先在源文件中删除；
2. 图片类输出应导出为扁平化 PNG，避免保留可编辑图层；
3. PDF 应使用真正的 redact/sanitize 流程，避免用形状覆盖代替删除；
4. 分享前检查文本选择、文档属性、批注、表单字段和附件；
5. 原始文件和公开文件分开保存。

RedactProof 只负责第 4 步中的一部分机器检查。它不能证明“没有问题”，但能把很多低级错误提前暴露出来。

## 为什么先做这个小工具

这个问题足够具体，用户也容易验证。它不像一个大平台，需要复杂部署；也不像纯 checklist，靠人记忆执行。一个本地脚本、一份报告和一个静态页面就能覆盖最常见的误用场景。

更重要的是，它提醒所有发布流程都要区分两层事实：视觉结果和文件结构。许多泄漏来自发布前文件处理流程粗糙，和底层加密或访问控制本身无关。

## 参考

- Adobe Acrobat redaction documentation: <https://helpx.adobe.com/acrobat/desktop/protect-documents/redact-pdfs/redact.html>
- Adobe note on hidden information, comments and metadata: <https://experienceleague.adobe.com/en/docs/document-cloud-learn/acrobat-learning/advanced-tasks/protect/redact>
- U.S. bankruptcy court training note on PDF redaction mistakes: <https://racer.casb.uscourts.gov/ECF_train/ECF_Videos/manual/XXMiscellaneous_File/Adobe_Acrobat/redactingsensitiveinfofrompdffile.htm>
