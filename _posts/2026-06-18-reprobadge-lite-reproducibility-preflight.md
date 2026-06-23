---
layout: post
title: "ReproBadge Lite：先问仓库有没有被别人检查的基本材料"
date: 2026-06-18 02:30:00 +0800
categories: local-tools
column: project-showcase
column_title: "项目展示"
tags: [reproducibility, research-code, release, citation]
---

> 代码状态：暂未公开。本文记录轻量 reproducibility preflight 的设计。  
> 主题：安全数据系统 / 工程实践 / 研究代码整理

很多研究原型或小工具并不是完全不能运行，而是第一次打开时缺少入口：README 不清楚，环境文件不见了，测试不知道怎么跑，样例和结果没有放在一起，引用方式也没有说明。

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

`--repo-label` 很重要：公开报告应显示人类可读标签，而不是本机绝对路径。

## 它和正式复现的区别

ReproBadge Lite 不运行完整实验，不重建论文结果，也不替代 artifact evaluation。它更像一个门口检查：在进入真正复现之前，先确认读者至少能找到说明、环境、测试、数据边界和结果位置。

这个定位让它适合小仓库、教学原型、论文辅助代码和个人工具。对于重型系统，仍然需要容器、数据版本、固定随机种子、硬件说明和完整实验脚本。

## 为什么这个小工具有用

公开项目时，缺 README、缺测试、缺许可证这类问题并不深奥，但很影响第一印象。把这些检查自动化以后，项目维护者不用每次都凭记忆补材料，也能在发给别人之前先修一轮基础问题。

更进一步，它可以和 release gate 组合：ReproBadge Lite 检查“材料是否齐”，Release Gate 检查“公开声明是否有证据和 caveat”。两者关注点不同，但都服务于同一件事：减少不可审查的公开材料。

## 参考

- GitHub documentation on `CITATION.cff`: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files>
- Citation File Format project: <https://citation-file-format.github.io/>
