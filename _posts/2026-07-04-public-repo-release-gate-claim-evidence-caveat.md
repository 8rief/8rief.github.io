---
layout: post
title: "Public Repo Release Gate：测试通过之后，还差一条发布门"
date: 2026-07-04 09:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [release, repository-hygiene, evidence, local-first]
---

> 代码状态：暂未公开。本文记录公开仓库前的本地质量门设计。  
> 主题：安全数据系统 / 工程实践 / 开源发布

测试通过不等于适合公开。一个仓库可能所有 unit tests 都是绿色，但 README 的 claim 没有证据，静态 demo 不存在，报告路径断了，许可证和引用缺失，或者文案里出现 “guaranteed”“certified” 之类过度承诺。

Public Repo Release Gate 解决的是最后一步私有审查：在仓库真正公开前，把文件 hygiene、必要 artifact、静态展示入口和 claim/evidence/caveat 放到同一份本地报告里。

## Manifest 思路

这个工具不试图替人判断项目好坏，而是要求发布者把公开声明写清楚：每个 claim 对应哪些证据，边界条件是什么。一个简化 manifest 可以长这样：

```json
{
  "release_id": "example-release",
  "require_static_site": true,
  "required_artifacts": ["reports/self_release_gate.md"],
  "claims": [
    {
      "id": "local_gate",
      "text": "combines local hygiene, artifact checks, and claim caveat checks",
      "evidence": ["tests/test_release_gate.py"],
      "caveat": "preflight only, not a security audit"
    }
  ]
}
```

没有 evidence 的 claim 会阻塞；没有 caveat 的 claim 会进入 review。这样设计是为了避免公开页面只剩宣传语。

## 本地接口形状

代码整理公开后，最小使用方式会保持为：

```bash
python3 release_gate.py examples/self_release_manifest.json \
  --root . \
  --output reports/self_release_gate.md \
  --html-output reports/self_release_gate.html

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

报告会返回 findings 数量、blocking findings 数量，以及 `block` 或 `ready-for-human-review`。后者表示“当前 manifest 声明的本地门没有发现阻塞项”，仍然需要人工复查公开语境。

## 三层发布检查

这条 release gate 可以和两个更小的工具配合：

1. Agent Leak Sentinel：先扫发布候选目录里的高风险残留；
2. ReproBadge Lite：检查基本可审查材料是否齐；
3. Public Repo Release Gate：检查 claim、证据、caveat 和展示入口。

这三步不复杂，但能把“我觉得差不多了”改成“我已经按清单检查过”。

## 使用边界

它不是法律审查、安全审计、漏洞扫描或合规认证。它只是本地、确定性、可复跑的发布前报告。真正公开前仍然需要人读 README、报告、代码和示例输出。

## 参考

- GitHub secret scanning overview: <https://docs.github.com/code-security/secret-scanning/about-secret-scanning>
- GitHub documentation on repository citation files: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files>

## 痛点和设计目标

测试通过只能说明当前测试集没有失败，不能说明 README 里的公开声明都有证据。Release Gate 关注的是“准备公开给别人看”时最容易出错的三件事：声明过强、证据缺失、限制条件没有写。

## 实现细节

每条公开声明都拆成三列：

```yaml
claim: "tool detects common release residue"
evidence: "reports/leak-scan.json"
caveat: "regex scan has false positives and does not prove absence of secrets"
```

发布门要求每条 claim 至少有一个 evidence，并且高风险 claim 必须有 caveat。这样 README、博客和 release note 就不会只剩宣传语。

## 可复现示例

```bash
python3 release_gate.py check claims.yaml --output reports/release-gate.md
```

预期输出形状：

```text
claims=6
missing_evidence=0
missing_caveat=1
status=blocked
```

## 输出怎么读

`status=blocked` 表示公开前还不能发。这里阻断的原因阻断点是有一条声明缺少限制条件，读者可能误解工具能力。

## 常见误判

最常见的误判是把 release gate 当成测试框架。测试验证代码行为，release gate 检查公开材料是否可审查；两者缺一不可，但回答的问题不同。

第二个误判是把 `ready-for-human-review` 写成 `ready-to-publish`。前者只表示机器清单没有发现当前 manifest 定义的阻断项；README、demo、license、引用和风险措辞仍需要人读。

第三个误判是只检查 claim 有没有 evidence，却不检查 caveat。没有 caveat 的“检测常见风险”很容易被读者理解成“证明没有风险”，这正是 release gate 要拦住的表达。

## 可以怎样练习

拿一个自己的 README，划出三句最像结论的话。为每句话补三列：`evidence`、`caveat`、`review owner`。如果某句话找不到证据，就不要先改工具；先把公开语句降级，或者明确标成待验证计划。

## 边界

Release Gate 不替代安全审计，也不保证项目质量。它只保证公开材料中的 claim、evidence 和 caveat 之间存在可检查连接。
