---
layout: post
title: "项目目录结构：让源码、测试、文档、配置和报告各有位置"
date: 2026-06-09 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 src、tests、docs、scripts、reports、config、data 讲清项目文件为什么要按职责分层，而不是随手堆在根目录。"
tags: [software-engineering, project-layout, python, teaching]
---
{% raw %}
> 主题：软件工程项目结构基础 / directory layout
> 本文 lab 已验证：demo 项目生成了 README、`.gitignore`、`config/example.json`、`data/tasks.json`、`docs/architecture.md` 和 `reports/summary.md`。

目录结构的目标是降低查找和修改成本。源码、测试、文档、脚本、配置、数据和报告承担不同职责。把它们放在固定位置，后续协作、测试、发布和问题定位都会更简单。

## 学习目标

1. 理解常见目录的职责边界。
2. 区分源文件、配置示例、运行数据和生成报告。
3. 知道哪些文件适合进入版本库，哪些应该被 `.gitignore` 排除。
4. 用一个小项目树解释项目结构是否清晰。

## 先修知识

需要了解文件路径和 Git 基础。建议先读 OS/Linux 文件基础与 Git 基础两组文章。

## 核心模型

![项目目录职责边界](/assets/diagrams/software-directory-layout-boundaries.svg)

`src` 放可复用源码；`tests` 放行为验证；`docs` 解释设计；`config` 放可公开的示例配置；`data` 放本地状态；`reports` 放运行产物。目录结构本身就是项目的第一层文档。

## 逐步实现

lab 初始化项目后生成树：

```text
demo_project/
  .gitignore
  README.md
  config/example.json
  data/tasks.json
  docs/architecture.md
  reports/summary.md
```

`config/example.json` 可以提交，因为它不包含真实凭据。`.gitignore` 中排除了 `.env`、`__pycache__/`、`*.pyc` 和临时报告。这个边界让示例可共享，本机私有状态留在本地。

## 常见错误

1. **把生成文件混进源码目录。** 报告和缓存应该有自己的目录，并明确是否提交。
2. **把真实配置当示例配置。** 示例配置只能包含公开安全的默认值。
3. **测试散落在脚本旁边。** 统一 `tests` 目录有利于发现和运行。
4. **README 与实际命令不一致。** README 是项目入口，必须跟可运行命令同步。

## 练习或延伸

1. 给 demo 项目增加 `scripts/` 下的 `run_demo.sh`，解释它和 `src` 的区别。
2. 判断 `reports/summary.md` 应该提交还是只作为本地证据保存。
3. 为一个已有项目画出“源码、测试、配置、报告”的目录职责图。

## 参考资料

- Python Packaging User Guide：[src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- Git 文档：[gitignore](https://git-scm.com/docs/gitignore)
- Python 文档：[pathlib](https://docs.python.org/3/library/pathlib.html)


## 为什么要引入目录边界

目录结构的价值在于把“源码、测试、配置、输入数据、生成报告”放到可预测的位置；视觉整齐只是附带结果。位置稳定后，构建脚本、测试脚本、README 和发布检查才能引用同一套路径。

## 可复现实验

一个小项目可以从下面结构开始：

```text
sample-app/
  src/
  tests/
  configs/
  data/
  reports/
  README.md
```

创建命令可以写成：

```bash
mkdir -p sample-app/{src,tests,configs,data,reports}
touch sample-app/README.md
find sample-app -maxdepth 1 -type d | sort
```

预期观察：

```text
sample-app
sample-app/configs
sample-app/data
sample-app/reports
sample-app/src
sample-app/tests
```

## 输出怎么读

`src` 放可维护源码，`tests` 放自动检查，`configs` 放可切换配置，`data` 放样例输入，`reports` 放生成结果。读者看到目录就能判断项目入口和产物在哪里。

## 状态变化

项目从一个空目录变成有边界的工作区。后续新增文件时，先判断它属于源码、测试、配置、输入还是产物，而不是随手放在根目录。


## 目录演进检查

一个目录结构后续能不能维护，取决于新增文件时是否还有明确归属。可以用下面清单做检查：

```text
new parser code -> src/
parser test cases -> tests/
example input -> data/
default options -> configs/
generated summary -> reports/
```

如果一个文件找不到归属，通常说明项目边界需要重新命名，或者这个文件只是临时实验材料，不应该进入公开仓库。

{% endraw %}
