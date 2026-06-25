---
layout: post
title: "Java 项目收尾：README、jar、CLI/API demo 和验收清单"
date: 2026-06-25 17:17:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 Java task tracker 收成可展示项目：README、jar 打包、CLI demo、HTTP API smoke、测试报告和边界说明。"
tags: [java, spring-boot, readme, jar, demo, capstone]
---
{% raw %}


> 主题：Java 从0到后端 API / README / jar / CLI demo / API smoke / capstone  
> 本文是 Java 包的结课文章。配套 lab 已完成 domain、service、storage、CLI、Spring Boot API、JUnit/MockMvc、jar 打包和本地 transcript。

项目收尾的目标是让读者能复现，也能判断项目做到了什么。Java 后端项目的可展示形态至少包含：一条从干净环境开始的运行命令、一份测试报告、一个可执行 jar、一个 CLI demo、一个本地 HTTP API smoke，以及清楚的边界说明。

## 学习目标

1. 整理一个 Java 后端项目的交付面。
2. 解释 README 应覆盖哪些运行问题。
3. 用 `mvn test` 和 Surefire 报告证明测试通过。
4. 用 CLI 和 curl smoke 展示真实入口。
5. 写出项目边界和后续扩展方向。

## 先修知识

需要完成前七讲，或至少理解 Maven、record、service、Jackson、JUnit 和 Spring Boot API 的作用。

## 核心模型

结课项目的收尾链条如下：

![Java 项目收尾链](/assets/diagrams/java-project-packaging-readme-demo.svg)

README 告诉读者如何进入项目；测试证明行为契约；jar 证明可执行交付；CLI 和 API smoke 展示真实入口。

## README 应回答什么

一个能展示的 README 至少回答：

1. 项目解决什么问题。
2. 需要什么工具链。
3. 如何运行测试和打包。
4. CLI 如何调用。
5. HTTP API 如何启动和验证。
6. 数据文件、日志和安全边界在哪里。

本 lab 的入口命令是：

```bash
./run_lab.sh
```

脚本会准备工具链、运行测试、打包 jar、执行 CLI、启动本地 API，并保存 transcript。

## jar 和 CLI demo

打包命令：

```bash
mvn -q -DskipTests package
```

CLI demo：

```bash
mvn -q -DskipTests exec:java \
  -Dexec.mainClass=com.example.tasktracker.cli.TaskCli \
  -Dexec.args="add write-tests HIGH"
```

transcript 关键输出：

```text
created id=1 status=OPEN priority=HIGH title=write-tests
1	OPEN	HIGH	write-tests
updated id=1 status=DONE
```

这说明 CLI 可以创建、列出和更新任务，并复用同一个 service 层。

## API smoke

API 使用 jar 启动：

```bash
java -jar target/task-tracker-0.1.0.jar \
  --server.address=127.0.0.1 \
  --server.port=18180 \
  --task-tracker.data-file=reports/tasks-api.json
```

curl smoke 覆盖创建、汇总、更新和 CSV 导出：

```text
POST /api/tasks -> id=1 status=OPEN priority=HIGH
GET /api/tasks/summary -> total=1 open=1 done=0
PATCH /api/tasks/1/status -> status=DONE
GET /api/tasks/export.csv -> one CSV row
```

这个 smoke 属于端到端连通性检查，证明 jar、HTTP 端口、JSON 绑定和 service 调用在真实进程中连通。

## 验收清单

- 工具链：JDK 21、Maven 3.9.10 已记录。
- 项目结构：Maven 标准目录和 Spring Boot jar 可打包。
- 领域模型：record、enum、领域异常表达清楚。
- service：ID、状态、tag、summary 不变量集中。
- 文件处理：Jackson JSON 持久化，CSV 导出可读。
- CLI：`add`、`list`、`done`、`export-csv` 可执行。
- API：POST、GET summary、PATCH、CSV endpoint 本地 smoke 通过。
- 测试：6 个 JUnit/MockMvc 用例，errors=0，failures=0。
- 配置：端口、绑定地址、数据文件可覆盖，默认绑定本机地址。
- 文档：README 提供单入口脚本和边界说明。

## 后续扩展

1. 把 JSON 文件替换成 SQLite 或 PostgreSQL，并讨论事务边界。
2. 增加 OpenAPI 文档和请求示例。
3. 增加认证和操作审计。
4. 用容器运行本地服务，但保持默认只绑定本机端口。

## 常见错误

1. **只交源码，不交运行证据。** transcript 和测试报告能证明项目真的跑过。
2. **README 缺少预期输出。** 读者需要知道成功状态长什么样。
3. **demo 和测试覆盖不同代码路径。** CLI/API smoke 应复用同一套 service。
4. **边界说明缺失。** 教学项目要明确本地运行、内存加文件持久化和无认证的限制。

## 练习

1. 给 README 增加一张 API endpoint 表。
2. 用 `curl -i` 查看响应头，补充 Content-Type 说明。
3. 增加一条失败 smoke：创建空标题任务，观察 400 JSON 错误。

## 参考资料

- Spring Boot 文档：[Running your application](https://docs.spring.io/spring-boot/reference/using/running-your-application.html)
- Maven 文档：[Introduction to the Build Lifecycle](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html)
- Spring Framework 文档：[REST Controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods.html)


{% endraw %}
