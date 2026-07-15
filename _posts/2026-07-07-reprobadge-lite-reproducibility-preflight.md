---
layout: post
title: "ReproBadge Lite：先问仓库有没有被别人检查的基本材料"
date: 2026-07-07 18:00:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [reproducibility, research-code, release, citation]
---

> 代码状态：暂未公开。本文记录轻量 reproducibility preflight 的设计。  
> 主题：安全数据系统 / 工程实践 / 研究代码整理

很多研究原型或小工具往往可以运行，但第一次打开时缺少入口：README 不清楚，环境文件不见了，测试不知道怎么跑，样例和结果没有放在一起，引用方式也没有说明。

ReproBadge Lite 解决的是“请别人看之前”的问题。它不做正式复现认证，也不判断论文结论是否正确，只检查一个仓库是否具备基本可审查材料。

## 检查项

第一版检查十类材料：

| 检查 | 目的 |
|---|---|
| README | 是否有入口说明 |
| License | 是否说明复用边界 |
| Environment | 是否有依赖或容器文件 |
| Tests | 是否有最基本的行为检查 |
| CI | 是否有自动检查入口 |
| Citation | 是否有 `CITATION.cff` 或类似元数据 |
| Reproduction instructions | README 是否说明安装、运行、测试或复现 |
| Data policy | 是否说明数据来源、合成数据或可用性 |
| Results/artifacts | 是否有报告、图、结果或站点输出 |
| No secret-like patterns | 是否命中常见 token 形状 |

高分只说明“材料比较齐”，不说明结果正确、测试充分或软件可生产使用。

## 本地接口形状

代码整理公开后，最小使用方式会保持为：

```bash
python3 reprobadge.py ../example-project \
  --repo-label example-project \
  --output reports/example_reprobadge.md \
  --html-output site/index.html

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

`--repo-label` 很重要：公开报告应显示人类可读标签，而避免暴露本机绝对路径。

## 它和正式复现的区别

ReproBadge Lite 不运行完整实验，不重建论文结果，也不替代 artifact evaluation。它更像一个门口检查：在进入真正复现之前，先确认读者至少能找到说明、环境、测试、数据边界和结果位置。

这个定位让它适合小仓库、教学原型、论文辅助代码和个人工具。对于重型系统，仍然需要容器、数据版本、固定随机种子、硬件说明和完整实验脚本。

## 为什么这个小工具有用

公开项目时，缺 README、缺测试、缺许可证这类问题并不深奥，但很影响第一印象。把这些检查自动化以后，项目维护者不用每次都凭记忆补材料，也能在发给别人之前先修一轮基础问题。

更进一步，它可以和 release gate 组合：ReproBadge Lite 检查“材料是否齐”，Release Gate 检查“公开声明是否有证据和 caveat”。两者关注点不同，但都服务于同一件事：减少不可审查的公开材料。

## 参考

- GitHub documentation on `CITATION.cff`: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files>
- Citation File Format project: <https://citation-file-format.github.io/>

## 设计目标与约束

ReproBadge Lite 的目标是给仓库做发布前材料体检：先回答“别人是否找得到入口、环境、测试、数据边界和引用信息”。它不复现论文结果，也不评估算法贡献。这个边界能避免工具误导读者，把材料齐备误写成结论可信。

## 实现细节

检查器可以把仓库扫描结果归一化成结构化条目：

```json
{
  "readme": true,
  "license": true,
  "tests": true,
  "ci": false,
  "citation": true,
  "data_policy": false
}
```

每个字段只回答一个可审查问题。比如 `tests=true` 表示存在可运行测试入口，不表示测试覆盖充分；`data_policy=false` 表示 README 没讲清数据来源或可用性。

## 可复现示例

```bash
python3 reprobadge.py example-project --repo-label example-project --output reports/reprobadge.md
```

预期输出形状：

```text
repo=example-project
checks_passed=4
checks_total=6
missing=data_policy,ci
status=needs-release-fixes
```

## 输出怎么读

这个结果给维护者一个修复顺序：先补数据边界和 CI，再考虑公开传播。它不评价项目本身是否有研究价值，只降低“别人打开后无法审查”的概率。

## 常见误判

第一种误判是把高分当成复现成功。ReproBadge Lite 只检查材料入口；它不会重跑完整实验，也不会证明结果能在另一台机器上复现。

第二种误判是把 `tests=true` 当成测试充分。这里的 `tests=true` 只表示存在可运行测试入口；测试是否覆盖关键路径，要靠后续审查。

第三种误判是忽略数据边界。README 里有安装命令，但没有说明数据来源、可用性、合成方式或许可证，读者仍然无法判断能不能复查结果。

## 可以怎样练习

找一个小仓库，先不要读源码，只看 README、license、环境文件、测试入口、数据说明和引用文件。写出两列清单：读者能直接复查的材料，读者还必须追问作者的材料。这个练习能暴露“代码可运行”和“材料可审查”之间的差距。

## 边界

适合轻量仓库、教学实验和论文辅助代码。对大型 artifact evaluation，还需要固定数据版本、容器镜像、硬件说明、完整实验脚本和原始结果校验。
