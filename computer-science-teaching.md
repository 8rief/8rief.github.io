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
