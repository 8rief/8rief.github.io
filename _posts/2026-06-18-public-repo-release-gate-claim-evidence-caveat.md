---
layout: post
title: "Public Repo Release Gate：测试通过之后，还差一条发布门"
date: 2026-06-18 02:40:00 +0800
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

报告会返回 findings 数量、blocking findings 数量，以及 `block` 或 `ready-for-human-review`。后者不是“可以无脑公开”，而是“当前 manifest 声明的本地门没有发现阻塞项”。

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
