---
layout: post
title: "ES-ORAM 研究札记：先把证明边界写成可检查清单"
date: 2026-07-15 18:00:00 +0800
categories: research-notes
column: problem-exploration
column_title: "问题探究"
tags: [oram, privacy, proof-engineering, research-notes]
---

> 代码状态：暂未公开。本文只讨论证明写作中的边界管理，不展开未公开构造细节。  
> 主题：安全数据系统 / 隐私计算 / 研究札记

密码协议研究里有一种常见风险：一个局部引理看起来成立，于是写作时不自觉地把更多问题也归到这个引理下面。等到最后整理 theorem，才发现后端假设、消息长度假设、生命周期条件和模拟器输入边界混在了一起。

ES-ORAM 这条研究线目前先做一件基础工作：把证明边界写成可检查清单。这个清单用于防止过度声明，完整证明仍然需要单独完成。

## 先区分结构残差和委托假设

一个安全性结论里通常同时出现几类项：

- 由当前语义层自己负责闭合的结构残差；
- 交给后端 ORAM 或类似底层组件的访问模式隐藏假设；
- 交给定长密文、定长确认消息等原语的不可区分性假设；
- 交给公开 workload 条件或 overflow/reconfiguration 语义的生命周期条件。

如果这些项在文字里混成一句“固定 envelope 隐藏了所有东西”，后面很难审查。更稳妥的写法是把可闭合项和仍需委托的项分开列出。

一个抽象的 residual bound 可以写成这种形状：

\[
Adv(A) \le Adv_{backend}(A_1) + Adv_{primitive}(A_2) + Pr[Bad] + negl(\lambda).
\]

这里真正关键的是每一项来源可追溯：哪些是语义层引理给出的零残差，哪些只是被委托给下层假设。

## 为什么要做成 gate

手写证明容易出现四类错误：

1. 把后端访问隐藏项误写成语义层已经证明；
2. 模拟器使用了声明泄漏以外的输入；
3. lifecycle overflow 或 backlog 被静默忽略；
4. 性能或实现状态被提前写成安全结论。

因此，研究原型里先放一个 gate：输入是结构化 manifest，输出是检查报告。报告不证明协议安全，只回答几个更基础的问题：

- 哪些引理声称把结构残差降为零；
- 每个引理依赖哪些 grammar 条件；
- theorem 的 hybrid sequence 有没有吞掉后端或原语项；
- negative controls 是否能拒绝过强 claim。

这类 gate 更像 proof engineering，不是 cryptographic proof assistant。它的价值在于把“作者脑子里知道的边界”变成文件和测试。

## 写作上的收益

这种做法至少带来三个收益。

第一，论文草稿不会过早把 backend、primitive、lifecycle 条件合并成一个大而含糊的安全声明。

第二，相关工作定位会更清楚：如果某个既有 ORAM 或多客户端存储方案只是后端压力或可选 substrate，就不应该写成被当前方案“替代”。

第三，实验段落不会越界。没有具体后端和 workload envelope 之前，成本表只能是模型或设计压力，不能写成真实性能优势。

## 当前边界

这份研究工件目前只适合放在内部 proof-spine 阶段：它不是完整密码学证明，不是 ORAM 实现，不是性能结果，不覆盖恶意客户端安全，也不应该被写成通用 ORAM 替代方案。

下一步应把后端假设语法、公开 workload 条件、overflow/reconfiguration 语义和相关工作位置写得更可审查；标题强度只能跟随这些材料。等这些边界稳定之后，再考虑公开更多代码和实验。

## 为什么这个问题不平凡

密码协议的证明边界一旦写晚，就容易出现两个问题：实现已经固定，但安全定义还在变化；实验结果看起来很好，但没有说明保护了什么、允许泄漏什么。先写证明边界清单，是为了在方法扩展前锁定 claim 的对象。

## 证据路径

一个最小证明边界清单至少包含：

```text
asset=queried index, payload, update position, access pattern
adversary=semi-honest non-colluding servers
allowed_leakage=database size, operation count, public epoch
protected=logical target, plaintext, token linkability
proof_object=simulator or hybrid argument
```

这类清单不能替代证明，但能阻止把“实现能跑”写成“安全已经成立”。

## 当前结论与置信度

```text
conclusion=claim_boundary_must_precede_performance_claim
confidence=high_for_writing_process
open_item=formal_simulator_still_required
```

当前结论是写作和研究流程判断，不是对某个具体协议的最终安全证明。

## 下一步验证

把每条公开 claim 映射到一个证明对象：定义、引理、模拟器、实验或限制说明。无法映射的句子要么删除，要么降级成待验证假设。

## 常见误判

第一类误判是把实现状态当成安全状态。某个 gate 能生成报告，只说明它能拒绝一部分过强 claim；它没有给出模拟器，也没有完成 hybrid argument。

第二类误判是把后端假设写丢。若安全性依赖 ORAM、定长消息或外部 workload envelope，公开 claim 中必须保留这些项，不能把它们压缩成一句“本层已经隐藏访问模式”。

第三类误判是把负例检查当成证明。negative controls 能说明 gate 不会接受明显错误的声明；它们不能说明所有正确声明都被覆盖。

## 可以怎样练习

拿一段准备公开的 claim，逐句填表：

```text
claim_sentence=
protected_secret=
allowed_leakage=
proof_object=definition/lemma/simulator/experiment/limitation
delegated_assumption=
status=proved/modeled/experiment_only/open
```

练习的目标是删掉或降级没有 proof object 的句子。若某句话只能由性能实验支撑，就不要把它写成安全定理。

## 参考入口

- Path ORAM: <https://eprint.iacr.org/2013/280>
- Universally Composable Security: <https://eprint.iacr.org/2000/067>
- EasyCrypt project: <https://www.easycrypt.info/>
