---
layout: post
title: "Capsule Memory Kit：把智能体记忆做成可迁移、自维护、缓存友好的本地胶囊"
date: 2026-06-18 03:20:00 +0800
categories: local-tools
tags: [agent-memory, local-first, prompt-cache, agent-workflow]
published: true
---

> 代码仓库：<https://github.com/8rief/capsule-memory-kit>
> 主题：Agent记忆系统 / 本地优先 / 可迁移工作流 / Prompt缓存友好设计

智能体记忆如果只存在于某个聊天产品内部，就很难成为长期资产。一次新会话、一个新工作目录、一次模型或客户端迁移，都可能让偏好、路径、项目状态和失败教训丢失。反过来，如果把所有记忆都塞进启动上下文，又会带来更高的首轮输入成本、更差的缓存复用，以及更难审计的隐私风险。

Capsule Memory Kit 是一个公开的最小实现，用来验证一种更工程化的记忆系统设计：把记忆做成一个本地文件夹胶囊，而不是某个运行时的隐藏状态。任何能够读文件、运行 Python 的 agent，都可以从同一个胶囊恢复上下文、检索细节、更新源记忆、重建索引并验证安全边界。

## 问题定义

一个可长期使用的 agent memory 系统至少要同时满足五个约束。

第一，可迁移。记忆不能依赖某一个聊天线程、某一个工作目录或某一个 vendor 的私有存储。新 agent 只要能读本地文件，就应该知道从哪里开始。

第二，可检索。启动时不应该读取全部历史。系统需要一个短入口和按需索引，让 agent 在任务明确之后再取最小相关记忆。

第三，可维护。记忆更新不能只靠手写 Markdown。生成包、索引、验证、提交这些步骤应该脚本化，否则很快漂移。

第四，可冲突处理。新的偏好和旧的偏好不一定兼容。普通追加可以自动做，但真正的 durable preference 冲突必须让用户确认。

第五，缓存友好。Prompt caching 依赖稳定前缀。启动注入里放时间戳、当前目录、会话 ID、大段动态清单，都会破坏可复用前缀。

这五个约束互相拉扯。最直接的坏方案是把全部记忆塞进一个巨大启动文件。它看似恢复最完整，实际会让每次首轮调用都重、慢、难缓存，而且泄露面更大。Capsule Memory Kit 选择相反方向：启动层极短，详细记忆本地索引化，任务出现后再检索。

## 核心抽象：memory capsule

胶囊本身就是一个目录，默认结构如下：

```text
memory-capsule/
  agent-memory-core.json
  AGENTS.md
  adapters/
    generic.md
  memory/
    user.md
    projects.md
    operations.md
  state/
    current/
      runtime/
      index/
      manifests/
  config/
    rules.json
```

其中只有 `memory/` 是人工维护的源记忆，`state/current/` 是生成状态。这个边界很重要：agent 应该修改源记忆，然后重新构建 runtime pack 和 index，而不是直接编辑生成包。

启动时只读两个稳定入口：

```text
agent-memory-core.json
AGENTS.md
```

然后根据任务读取 `state/current/` 下最小相关包。这个策略把记忆恢复拆成两步：先恢复路由规则，再按任务检索内容。

## 为什么要有 manifest

`agent-memory-core.json` 是机器入口。它不追求写得好看，而是给 agent 一个稳定协议：

```json
{
  "schema_version": 1,
  "entrypoint": "AGENTS.md",
  "generated_state": "state/current",
  "conflict_policy": "Ask the user when durable preferences or source-of-truth claims conflict.",
  "cache_policy": {
    "startup_context": "short-stable-prefix",
    "detailed_memory": "smallest-relevant-pack-on-demand",
    "generated_artifacts": "content-addressed-byte-stable"
  }
}
```

这里的重点不是字段多，而是字段稳定。一个陌生 agent 不需要理解全部历史，只要知道入口、生成层位置、冲突策略和缓存策略，就能安全开始。

## Agent-facing AGENTS.md

`AGENTS.md` 是人类和 agent 都能读的短契约。它应该短、稳定、少动态内容。

典型规则是：

1. 先读 manifest。
2. 再读 `AGENTS.md`。
3. 任务明确后，只读取最小相关 pack。
4. 不在启动时扫描全库。
5. 遇到 durable preference 冲突时请用户确认。

这里故意不放大段项目背景。项目背景可以进入 `memory/projects.md`，再由索引命中后加载。

## 源记忆与生成记忆

Capsule Memory Kit 把记忆分成两类。

源记忆是 agent 和用户共同维护的事实、偏好、路径、项目状态和操作规则。它们在 `memory/` 下，是审计对象。

生成记忆是为了运行效率产生的派生视图，包括：

- runtime bootstrap；
- JSONL index；
- SQLite FTS index；
- inventory manifest；
- conflict report；
- skipped unsafe file report。

生成层可以删除重建。只要源记忆不变，连续两次 build 应该得到字节一致的结果。这是缓存友好和工程可维护性的共同基础。

## 脚本闭环

最小使用方式如下：

```bash
python3 capsule_memory_kit.py init /tmp/my-agent-memory
python3 capsule_memory_kit.py build /tmp/my-agent-memory
python3 capsule_memory_kit.py validate /tmp/my-agent-memory
python3 capsule_memory_kit.py route /tmp/my-agent-memory "how should this agent handle conflicts"
python3 capsule_memory_kit.py audit-cache /tmp/my-agent-memory
```

这些命令覆盖一个完整闭环。

`init` 创建通用 capsule。

`build` 读取源记忆，过滤风险文件，生成 runtime pack、JSONL index 和 SQLite FTS index。

`validate` 检查必需文件、安全规则、content revision、未解决冲突和易变元数据。

`route` 根据任务 query 返回最小相关记忆。

`audit-cache` 检查启动面大小和易变字段。

`check-conflicts` 单独检查冲突标记，适合放进提交前检查或 agent 的 stop hook。

## 冲突处理

记忆系统最容易出错的地方不是存不下来，而是错误地合并。

如果用户说以后默认用高质量模式，而旧记忆说默认用快速模式，agent 不应该自动选择折中方案。因为这不是普通事实追加，而是 durable preference 冲突。

Capsule Memory Kit 用显式冲突标记建模：

```text
CONFLICT: old preference says X; new preference says Y.
```

只要源记忆里存在这类标记，`validate` 就会失败。失败不是系统错误，而是有意的停机点：需要用户确认偏好，然后把冲突改成新的稳定规则。

这个规则可以概括为：

普通非冲突更新自动做；偏好冲突、权威来源冲突、任务边界冲突必须问用户。

## 缓存友好设计

Prompt caching 的第一性原理很简单：越靠前、越稳定的前缀，越可能被复用。动态内容越早出现，后面的可复用性越差。

因此 capsule 的启动面避免这些内容：

- 当前时间；
- 当前工作目录；
- 会话 ID；
- Git dirty count；
- 最近文件清单；
- 全量 inventory；
- 大段历史摘要；
- 每次刷新都会变化的 generated_at。

取而代之的是内容寻址：

```text
content_revision = hash(generated_state_without_manifests)
```

如果源事实没有变化，build 不应该因为墙钟时间变化而产生 diff。这个性质很实用：agent 可以放心运行维护脚本，不会制造无意义提交。

## 为什么不用一个大数据库

数据库可以作为索引层，但不应该成为唯一源。

原因有三个。

第一，可迁移性。Markdown 源文件和 JSON manifest 更容易被陌生 agent、编辑器、Git 和普通脚本理解。

第二，可审计性。偏好和规则需要人能 review。SQLite 适合查询，不适合作为唯一可读契约。

第三，可恢复性。如果索引坏了，应该能从源记忆重建。生成层不能反过来成为 source of truth。

所以这个项目采用折中结构：源记忆是普通文本，索引层可以用 SQLite FTS 加速。

## 安全边界

记忆系统很容易误收不该保存的内容。公开模板里默认拒绝：

- `.env`；
- `auth.json`；
- credential JSON；
- raw session logs；
- browser profile；
- cookies；
- SQLite database；
- PEM/key 文件；
- API-key-shaped 字符串；
- JWT-shaped 字符串。

扫描报告只返回路径、规则名和原因，不打印匹配值。这个设计不是完整 DLP，但能拦住 agent 工作流里最常见的发布事故。

## 这不是 hosted memory service

Capsule Memory Kit 不是一个云端记忆服务，也不是向量数据库产品。它是一个更低层的本地协议模板。

它要解决的是：

- 记忆从哪里开始读；
- 记忆怎样生成可检索视图；
- 什么内容不能导出；
- 什么时候必须问用户；
- 怎样让刷新保持可重复；
- 怎样让启动上下文保持短而稳定。

在这个基础上，可以接不同 agent：Codex、Claude Code、本地脚本 agent、MCP 服务，甚至一个简单 shell assistant。只要它能读 `agent-memory-core.json` 和 `AGENTS.md`，就能接入。

## 最小实现的取舍

当前版本只用 Python 标准库，不依赖外部包。好处是可复制、可审计、可离线运行。代价是它不提供高级语义检索，也不内置复杂权限模型。

这个取舍是有意的。第一版的目标不是做全能记忆平台，而是把正确的边界跑通：

- source vs generated；
- startup vs task-specific；
- exact memory vs searchable index；
- automatic update vs user-confirmed conflict；
- local secret safety vs public export；
- cache-stable metadata vs volatile diagnostics。

这些边界比功能数量更重要。

## 后续方向

几个自然扩展方向：

- 多 agent adapter，例如 Codex、Claude Code、本地 MCP agent；
- 更强的 conflict schema，把偏好、事实、路径、项目状态分开审计；
- 可选向量索引，但仍保持文本源为权威；
- pre-commit hook；
- GitHub Action 验证 capsule 是否可重建；
- 可视化 memory health report；
- 对 prompt-cache 命中率做长期数值审计。

但即使没有这些扩展，当前最小版本已经能支撑一个实用原则：记忆应该是可迁移、可验证、可重建的本地资产，而不是一次聊天里的隐性上下文。

## 参考命令

```bash
git clone https://github.com/8rief/capsule-memory-kit
cd capsule-memory-kit
python3 capsule_memory_kit.py init /tmp/capsule-demo --build
python3 capsule_memory_kit.py validate /tmp/capsule-demo
python3 capsule_memory_kit.py route /tmp/capsule-demo "conflicting preferences"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

如果这套模式用于真实个人记忆，建议先私有运行，确认敏感路径、身份信息、凭据和 raw session 都不会进入导出层，再考虑公开模板或衍生工具。
