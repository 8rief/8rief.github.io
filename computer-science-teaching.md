---
layout: page
title: 计算机技术教学
permalink: /computer-science-teaching/
---

这个栏目专门写计算机技术教学内容。目标是把一个概念、系统或编程主题讲到学习者能复现、能调试、能解释边界。资料罗列只能作为附录，正文必须建立可操作的理解模型。

## 选题范围

- 编程语言与工程实践：Python、C/C++、Shell、Git、测试、调试、构建系统。
- 计算机系统：操作系统、网络、数据库、编译、分布式系统、性能分析。
- 安全与隐私计算基础：威胁模型、密码学工程接口、MPC/PIR/FSS/ORAM 入门。
- 研究工程方法：如何读源码、搭实验、写复现脚本、做图表和报告。

## 写作结构

每篇教学文章默认包含：

1. **学习目标**：读完应该能做什么。
2. **先修知识**：需要知道哪些概念，不默认读者已经会。
3. **核心模型**：用一个小模型解释本质，不先堆 API。
4. **逐步实现**：给出可运行代码或命令，解释关键状态变化。
5. **常见错误**：指出容易误解的地方和调试方法。
6. **练习或延伸**：给出一两个能检验理解的小任务。


## 建议学习路径

下面的路径用于解决默认文章列表按发布时间倒序显示的问题。学习时优先按这里的顺序走；底部“已归入本栏目”保留为全量索引。

### 基础工具与系统

| 顺序 | 发布包 | 从哪里开始 | 收尾项目 | 适合解决的问题 |
| --- | --- | --- | --- | --- |
| 1 | Git 基础与协作 | [Git 心智模型：working tree、index、commit 和 repository](/computer-science-teaching/2026/06/28/git-working-tree-index-commit.html) | [Git repo lab、release tag 和协作检查表](/computer-science-teaching/2026/06/28/git-release-tag-gitignore-capstone.html) | 版本控制、协作、冲突解决和发布前检查 |
| 2 | OS/Linux 进程与文件 | [Linux 文件系统：路径、目录项、inode 和 stat 怎么连起来](/computer-science-teaching/2026/06/28/linux-filesystem-path-inode-stat.html) | [本地 system observer 报告](/computer-science-teaching/2026/06/28/linux-system-observer-capstone.html) | 文件、进程、权限、信号、文本流水线 |
| 3 | SQL 实用开发 | [SQLite schema 与表设计](/computer-science-teaching/2026/06/28/sql-sqlite-schema-table-primary-key.html) | [SQLite 报表 CLI、索引证据和发布检查](/computer-science-teaching/2026/06/28/sql-report-cli-index-explain-capstone.html) | 查询、增删改、JOIN、聚合、事务、参数化查询、导入导出 |

### 从0到可运行项目

| 顺序 | 语言/方向 | 从哪里开始 | 收尾项目 | 重点 |
| --- | --- | --- | --- | --- |
| 1 | Python | [Python 环境和依赖管理](/computer-science-teaching/2026/06/25/python-environment-venv-packaging.html) | [Python 项目收尾](/computer-science-teaching/2026/06/25/python-project-structure-config-logging-readme.html) | venv、文件/JSON/CSV、Typer、pytest、FastAPI、配置和日志 |
| 2 | Java | [Java 工具链和 Maven 项目结构](/computer-science-teaching/2026/06/25/java-toolchain-maven-project-layout.html) | [Java 项目收尾](/computer-science-teaching/2026/06/25/java-project-packaging-readme-demo.html) | Maven、领域模型、JUnit、Jackson、Spring Boot、CLI/API demo |
| 3 | Go | [Go 工具链和 module](/computer-science-teaching/2026/06/25/go-toolchain-module-project-layout.html) | [Go 项目收尾](/computer-science-teaching/2026/06/25/go-project-tests-readme-demo.html) | module、error、JSON/CSV、net/http、context、goroutine、测试 |
| 4 | Rust | [Rust 工具链和 Cargo 项目结构](/computer-science-teaching/2026/06/25/rust-toolchain-cargo-project-layout.html) | [Rust 项目收尾](/computer-science-teaching/2026/06/25/rust-project-readme-demo-release-checklist.html) | Cargo、ownership、Result/Option、serde、clap、测试、Axum |
| 5 | C++ 基础工程 | [C++ 程序如何从源码变成可执行文件](/computer-science-teaching/2026/06/24/cpp-build-pipeline-source-to-executable.html) | [GoogleTest 和可复现实验](/computer-science-teaching/2026/06/24/cpp-googletest-reproducible-tests.html) | 编译链接、头文件、RAII、所有权、CMake、测试 |
| 6 | C++ 库项目 | [CMake FetchContent 和第三方库边界](/computer-science-teaching/2026/06/25/cpp-cmake-fetchcontent-library-boundary.html) | [C++ 项目收尾](/computer-science-teaching/2026/06/25/cpp-project-readme-demo-release-checklist.html) | CLI11、nlohmann/json、CSV、Catch2、spdlog、cpp-httplib |

### 机制与实验基础

| 顺序 | 发布包 | 从哪里开始 | 收尾项目 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 深度学习基础 | [先把可复现实验跑起来](/computer-science-teaching/2026/06/25/deep-learning-route-reproducible-lab.html) | [从 XOR baseline 到 MLP 对比](/computer-science-teaching/2026/06/25/deep-learning-capstone-xor-mlp-comparison.html) | 先跑 baseline，再解释 tensor、autograd、loss、训练循环 |
| 2 | Linux 网络与授权安全基础 | [Linux 网络模型](/computer-science-teaching/2026/06/27/linux-network-model-interface-route-socket.html) | [本地服务地图、路径边界和加固报告](/computer-science-teaching/2026/06/27/linux-network-security-capstone-checklist.html) | 已完成，但后续安全专题暂缓；可作为网络基础补充 |

### 写作和学习原则

语言、SQL 和开发基础都按“需求 → 用法 → 原理 → 实操”组织。原理不是省略，而是从真实需求出发，用来解释为什么更快、更好用、更安全、更容易维护，或者为什么某个库/API 这样设计。

## 从0到可运行项目路线

语言教学采用有限发布包：每门语言围绕一个结课项目，从环境、核心语法、依赖管理、标准库、第三方库、测试、配置、日志、README 和 demo transcript 逐步推进。文章数量服务于可复现项目，不以单纯篇数作为完成标准。

当前路线：

| 方向 | 目标项目形态 | 重点能力 |
| --- | --- | --- |
| Python | 本地证据 CLI + API | venv、pyproject、文件/JSON/CSV、Typer、pytest、FastAPI、httpx、配置和日志 |
| Java | 后端 REST API | JDK/JVM、Maven/Gradle、集合/泛型、JUnit、Jackson、Spring Boot、数据访问 |
| Go | 本地服务健康检查器 | module、struct/interface/error、JSON/CSV、net/http、context、goroutine/channel、CLI、测试、优雅关闭 |
| C++ | 本地文件索引 CLI + API | CMake/Ninja、FetchContent、CLI11、nlohmann/json、CSV、Catch2、spdlog、cpp-httplib、README/demo |
| Rust | 日志洞察 CLI + 本地 API | Cargo、ownership/borrowing、Result/Option、thiserror/anyhow、serde、clap、测试、clippy、Tokio/Axum、tracing |
| SQL 实用开发 | 本地 SQLite 报表 CLI | schema、CRUD、JOIN、GROUP BY、事务、迁移、参数化查询、CSV/JSON 导入导出、EXPLAIN QUERY PLAN |
| 深度学习基础 | XOR toy classifier baseline → MLP | NumPy/tensor、线性代数、autograd、概率统计、优化、baseline、Dataset/DataLoader、checkpoint、可复现实验 |
| Linux 网络与授权安全基础 | 本地 HTTP 服务 + service map + hardening report | interface/route/socket/resolver、ss/curl、loopback service map、HTTP headers、path boundary、subprocess boundary |

Linux、网络和安全基础文章作为横向支撑：每篇都给出本地命令、预期观察、实验边界和可复跑小产物。

## 深度学习路线

深度学习内容会作为后续有限发布包推进。路线先补必要基础：数值 Python 与 tensor、线性代数、微积分与自动微分、概率统计、优化、简单 baseline、PyTorch 数据集与训练循环、评估与 checkpoint。只有在这些基础能本地复现之后，再进入 MLP、CNN、序列模型、attention/Transformer 和小型部署项目。涉及模型效果的文章必须给出 baseline，或者明确说明该文只解释机制、不做效果主张。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "computer-science-teaching" %}
{% if posts.size == 0 %}
暂时没有文章。后续教学内容会从可复现的小主题开始写，不把项目展示或研究探究混进来。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
