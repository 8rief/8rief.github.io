---
layout: post
title: "Agent Leak Sentinel：公开项目之前，先检查智能体工作流残留"
date: 2026-06-18 02:20:00 +0800
categories: local-tools
tags: [agent-security, secret-scanning, release, local-first]
---

> 代码状态：暂未公开。本文记录发布前安全门的设计，不包含真实凭据、会话或导出包。  
> 主题：安全数据系统 / Agent安全 / 工程实践

智能体辅助开发会产生比普通源码更多的副产物：运行日志、会话摘要、浏览器状态、认证配置、临时导出包、本地绝对路径。把项目从私有工作区整理成公开仓库时，风险不只是一串 API key，也可能是这些工作流残留。

Agent Leak Sentinel 的目标是做一道本地预检门：扫描候选发布目录，找出高风险文件名和 token 形状字符串；报告只写规则名、严重级别、相对路径、行号和修复建议，不打印匹配内容。

## 为什么不能只靠肉眼清理

手工清理有两个问题。第一，文件树一大就容易漏掉 `.env`、`auth.json`、session JSONL 或浏览器 profile。第二，人很容易为了排查问题在报告里保留片段，但这些片段本身可能就是风险。

这个工具因此选择了一个克制的输出 contract：

```text
rule name, severity, relative path, line number, recommendation
```

没有 snippet，没有 matched value，没有 JSON payload，也没有 transcript 内容。

## 第一版规则

| 规则 | 覆盖面 |
|---|---|
| `env_file` | `.env` 和 `.env.*`，排除 `.env.example` 等模板 |
| `auth_json_file` | 认证 JSON 文件 |
| `agent_session_jsonl` | 原始会话或 transcript JSONL |
| `browser_cookie_or_profile_path` | 浏览器 cookie/profile 路径 |
| `jwt_token_shape` | JWT 形状字符串 |
| `api_token_shape` | API/access token 形状字符串 |
| `refresh_token_shape` | refresh token 形状字符串 |
| `account_pool_path` | account-pool、auth-dir、credential-pool 等目录组件 |
| `suspicious_local_absolute_path` | 常见本地 home/user 路径 |

这不是完整安全审计，只是把发布前最不该出现的东西先拦下来。

## 本地接口形状

代码整理公开后，最小使用方式会保持为：

```bash
python3 leak_sentinel.py examples/safe-fixture \
  --markdown-out reports/safe-fixture.md \
  --html-out reports/safe-fixture.html

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

演示报告使用合成风险样例。合成样例的意义是验证规则覆盖，而不是把真实敏感文件拿来做展示。

## 正确使用方式

这个工具适合扫描项目目录、发布候选目录和已经脱敏的导出包；不适合直接扫描真实凭据库、浏览器 profile 或整个 home 目录。

如果报告出现 high/critical，正确动作不是把报告删掉，而是删除相关文件、轮换可能泄露的凭据，再重新生成公开材料。平台 secret scanning 仍然应该打开；本地预检只是把问题尽量前移。

## 参考

- GitHub secret scanning overview: <https://docs.github.com/code-security/secret-scanning/about-secret-scanning>
- GitHub supported secret scanning patterns: <https://docs.github.com/en/code-security/reference/secret-security/supported-secret-scanning-patterns>