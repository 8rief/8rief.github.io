---
layout: post
title: "Java 配置和日志：让路径、端口和诊断信息有明确边界"
date: 2026-05-08 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 application.properties、ConfigurationProperties、命令行参数和 logging 配置 Java API 的运行边界。"
tags: [java, spring-boot, configuration, logging, operations]
---
{% raw %}


> 主题：Java 从0到后端 API / configuration / logging / diagnostics  
> 本文 lab 通过命令行参数覆盖端口、绑定地址和任务数据文件，服务日志写入本地报告文件。

项目能运行后，下一类问题是运行边界：端口写在哪里？数据文件路径从哪里来？日志应该打印什么？配置散落在代码里会让测试、CLI、API smoke 和真实运行互相干扰。Spring Boot 的配置体系可以把这些可变项集中管理。

## 学习目标

1. 用 `application.properties` 保存默认运行参数。
2. 用命令行参数覆盖本次运行的端口和文件路径。
3. 用 `@ConfigurationProperties` 绑定结构化配置。
4. 区分用户输出和诊断日志。
5. 建立本地服务的安全默认值。

## 先修知识

需要知道属性文件的 `key=value` 形式，并理解前一讲的 Spring Boot 应用如何启动。

## 为什么需要配置和日志边界

一个后端服务通常会在不同环境里运行：测试要写临时文件，demo 要绑定固定本机端口，真实部署可能由容器或启动脚本传入路径。把这些值写死在 Java 代码里，会让每次运行都共享同一个状态文件，也会让端口冲突难以排查。

配置边界的目标是把“会变的运行参数”从“不会变的业务规则”里拿出来。`TaskService` 只关心任务怎样创建、更新和统计；数据文件路径、监听地址和日志级别由 Spring Boot 配置体系交给入口层处理。这样同一份 jar 可以在测试、CLI smoke 和本地 API smoke 中使用不同数据文件。

日志边界解决另一个问题：用户输出和诊断信息应该分开。CLI 的 `created id=1` 是给用户看的结果；服务启动、端口、请求错误和持久化路径是给排查问题看的诊断信息。公开文章只摘取安全片段，避免把本机绝对路径或敏感参数带出去。


## 核心模型

配置从 properties 或命令行进入 Spring，绑定成 Java 对象，再用于创建 storage 和 service。日志从应用运行过程输出到终端或文件。

![配置和日志边界](/assets/diagrams/java-configuration-logging-boundary.svg)

配置控制运行差异，源码控制业务逻辑。两者分开后，同一份 jar 可以用于测试、demo 和本地服务。

## 默认配置

项目默认配置：

```properties
server.address=127.0.0.1
server.port=18180
task-tracker.data-file=reports/tasks-api.json
logging.level.com.example.tasktracker=INFO
```

`server.address=127.0.0.1` 是教学项目的安全默认值：只接受本机连接。`task-tracker.data-file` 指向本地 JSON 文件，让数据位置可配置。

## 绑定配置对象

配置对象使用 record：

```java
@ConfigurationProperties(prefix = "task-tracker")
public record TaskTrackerProperties(Path dataFile) {
    public TaskTrackerProperties {
        if (dataFile == null) {
            dataFile = Path.of("reports/tasks-api.json");
        }
    }
}
```

应用入口把它注册成 bean，并创建 storage 和 service：

```java
@SpringBootApplication
@EnableConfigurationProperties(TaskTrackerProperties.class)
public class TaskTrackerApplication {
    @Bean
    JsonTaskStorage jsonTaskStorage(TaskTrackerProperties properties) {
        return new JsonTaskStorage(properties.dataFile());
    }

    @Bean
    TaskService taskService(JsonTaskStorage storage) {
        return new TaskService(storage);
    }
}
```

这样 service 不需要知道配置来源，它只接收已经构造好的 storage。

## 命令行覆盖

lab 中启动 API 时覆盖三项配置：

```bash
java -jar target/task-tracker-0.1.0.jar \
  --server.address=127.0.0.1 \
  --server.port=18180 \
  --task-tracker.data-file=reports/tasks-api.json
```

这种覆盖方式适合 demo 和测试。真实部署还可以使用环境变量、配置中心或容器参数，但敏感值不应写入源码、README、日志或公开报告。

## 日志边界

CLI 的结果可以直接打印给用户：

```text
created id=1 status=OPEN priority=HIGH title=write-tests
```

服务诊断日志则写入 `reports/api-server.log`，用于排查启动失败、端口冲突、请求错误等问题。文章中只摘取安全的输出片段，不发布本机绝对路径和完整日志。

## 输出怎么读

本次 Java lab 的工具链输出先确认运行环境：

```text
openjdk version "21.0.11"
javac 21.0.11
Apache Maven 3.9.10
```

这三行分别说明运行时、编译器和构建工具都存在。只有 `java` 而没有 `javac` 时，Spring Boot 应用也许能运行旧 jar，但不能重新编译测试；只有 `javac` 而没有 Maven 时，依赖、测试和打包流程仍然无法复现。

CLI 阶段的输出说明数据文件覆盖生效：

```text
created id=1 status=OPEN priority=HIGH title=write-tests
updated id=1 status=DONE
exported csv=reports/tasks-cli.csv
```

这几行应写入 CLI 专用数据文件。API 阶段再用 `--task-tracker.data-file=reports/tasks-api.json` 启动服务，返回的 summary 是另一份状态：

```json
{ "total": 1, "open": 1, "inProgress": 0, "done": 0 }
```

如果 CLI 中已经有两个任务，而 API summary 仍是一个任务，说明配置隔离成功。若两边数据互相污染，优先检查 `task-tracker.data-file` 是否在两个入口中指向同一个文件。


## 常见错误

1. **把端口和文件路径写死在代码里。** 测试、demo 和本地运行会互相影响。
2. **日志打印敏感值。** 日志应帮助诊断，但不能泄露凭据或本机私密路径。
3. **让 service 直接读环境。** 业务层应接收已经准备好的依赖。
4. **默认绑定所有网卡。** 本地教学服务优先绑定 loopback。

## 练习

1. 增加 `task-tracker.max-title-length` 配置，并在 service 中使用它。
2. 启动两个不同端口的服务，分别指定不同数据文件，观察它们是否互不干扰。
3. 把日志级别改为 `DEBUG`，观察启动日志和请求日志的变化。

## 参考资料

- Spring Boot 文档：[Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)
- Spring Boot 文档：[Logging](https://docs.spring.io/spring-boot/reference/features/logging.html)
- Spring Boot 文档：[Configuration Properties](https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties)


{% endraw %}
