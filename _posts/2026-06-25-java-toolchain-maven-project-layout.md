---
layout: post
title: "Java 工具链和 Maven 项目结构：先把 jar 跑起来"
date: 2026-06-25 17:10:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 JDK、javac、Maven 标准目录和 Spring Boot jar 建立 Java 项目的可复现运行边界。"
tags: [java, jdk, maven, jar, project-layout]
---
{% raw %}


> 主题：Java 从0到后端 API / JDK / Maven / jar / 项目结构  
> 本文配套 lab 已在 Ubuntu 24.04、Temurin JDK 21.0.11、Maven 3.9.10 环境下执行。最终 Maven 测试、jar 打包、CLI smoke 和本地 HTTP API smoke 均通过。

Java 项目容易在第一步就混乱：机器上有 `java`，却没有 `javac`；IDE 能运行，终端不能打包；源码文件能执行，依赖和测试无法复现。工程化的起点是把工具链和项目结构固定下来，让项目离开 IDE 后仍能通过命令行构建、测试和运行。

## 学习目标

1. 区分 JRE、JDK、`java`、`javac` 的职责。
2. 理解 Maven 标准目录如何组织源码、测试和资源。
3. 读懂 `pom.xml` 中 parent、dependency、plugin 的基本作用。
4. 用 `mvn test`、`mvn package` 验证项目边界。
5. 解释为什么教学项目也要保留 transcript。

## 先修知识

需要会使用 Linux 终端，理解目录、文件和命令行参数。暂时不要求掌握 Spring Boot 或 JUnit。

## 核心模型

一个可复现 Java 项目可以先看成五层：

![Java 项目运行边界](/assets/diagrams/java-toolchain-maven-project-layout.svg)

JDK 提供编译器和运行时。Maven 读取 `pom.xml`，下载依赖，按标准目录编译源码和测试。打包结果是一个 jar，后续 CLI 和 HTTP API 都从这个 jar 或同一套源码进入。

## 目录结构

capstone 项目是一个 task tracker：同一套 service 层同时被 CLI 和 Spring Boot API 调用。核心目录如下：

```text
java-task-tracker-api/
├── pom.xml
├── run_lab.sh
├── src/main/java/com/example/tasktracker/
│   ├── cli/
│   ├── config/
│   ├── csv/
│   ├── domain/
│   ├── service/
│   ├── storage/
│   └── web/
├── src/main/resources/application.properties
└── src/test/java/com/example/tasktracker/
```

`src/main/java` 放生产代码，`src/main/resources` 放应用配置，`src/test/java` 放测试。Maven 默认认识这套结构，因此构建命令不需要额外指定每个目录。

## POM 的最小解释

项目使用 Spring Boot parent 管理依赖版本：

```xml
<parent>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-parent</artifactId>
  <version>3.3.2</version>
</parent>

<properties>
  <java.version>21</java.version>
  <maven.compiler.release>21</maven.compiler.release>
</properties>
```

`java.version` 表示项目目标 Java 版本。`maven.compiler.release` 让编译器按 Java 21 API 边界检查源码。依赖部分引入 Web、Validation、Jackson Java Time 和测试：

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-test</artifactId>
  <scope>test</scope>
</dependency>
```

这里固定 Spring Boot 3.3.2 是为了让 lab 可复现，不把“追最新版本”作为教学目标。

## 可复现命令

lab 的主路径包含：

```bash
java -version
javac -version
mvn -version | head -4
mvn -q test
mvn -q -DskipTests package
```

`mvn test` 会编译生产代码和测试代码，并运行 JUnit。`mvn package` 会生成 `target/task-tracker-0.1.0.jar`。transcript 中记录了实际工具链：

```text
openjdk version "21.0.11" 2026-04-21 LTS
javac 21.0.11
Apache Maven 3.9.10
```

## 常见错误

1. **只有 `java` 没有 `javac`。** 这说明机器上可能只有运行时，项目无法编译。
2. **把源码放在随意目录。** Maven 标准目录减少构建脚本和 IDE 配置差异。
3. **依赖版本散落在命令里。** 版本应进入 `pom.xml`，命令只负责执行构建。
4. **只依赖 IDE 的绿色按钮。** 交付项目必须能用终端命令复现。

## 练习

1. 执行 `mvn -q test` 后查看 `target/surefire-reports/`，理解 Maven 如何保存测试报告。
2. 修改 `java.version` 为低于源码需要的版本，观察编译错误。
3. 执行 `jar tf target/task-tracker-0.1.0.jar | head`，观察 jar 内部结构。

## 参考资料

- Oracle Java 21 API：[Java Platform SE 21](https://docs.oracle.com/en/java/javase/21/docs/api/index.html)
- Maven 文档：[Introduction to the POM](https://maven.apache.org/guides/introduction/introduction-to-the-pom.html)
- Maven 文档：[Standard Directory Layout](https://maven.apache.org/guides/introduction/introduction-to-the-standard-directory-layout.html)
- Spring Boot 文档：[Build systems](https://docs.spring.io/spring-boot/reference/using/build-systems.html)


{% endraw %}
