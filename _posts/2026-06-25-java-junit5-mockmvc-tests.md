---
layout: post
title: "JUnit 5 和 MockMvc：让 Java 后端项目可回归验证"
date: 2026-06-25 17:14:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 JUnit 5、TempDir、AssertJ 和 MockMvc 覆盖 service、storage、CLI、REST API 四个边界。"
tags: [java, junit5, mockmvc, testing, spring-boot-test]
---
{% raw %}


> 主题：Java 从0到后端 API / JUnit 5 / MockMvc / 回归测试  
> 本文 lab 生成 4 个 Surefire XML 报告，共 6 个测试用例，errors=0、failures=0。

后端项目的测试不能只检查“服务能启动”。真正容易出错的边界包括 service 规则、JSON 文件往返、CLI 参数路径、HTTP 请求绑定、校验失败和 CSV 导出。JUnit 5 加 Spring Boot Test 可以用同一套 Maven 命令覆盖这些边界。

## 学习目标

1. 用 JUnit 5 写普通单元测试。
2. 用 `@TempDir` 隔离文件测试。
3. 用 AssertJ 写行为断言。
4. 用 MockMvc 测 Spring MVC controller。
5. 读取 Surefire 报告确认测试数量和失败数。

## 先修知识

需要理解 Maven 的 `test` 阶段和 Java 方法调用。了解 HTTP JSON 会帮助理解 MockMvc 测试。

## 核心模型

测试覆盖从纯逻辑到 HTTP 边界逐层展开：

![Java 测试覆盖层](/assets/diagrams/java-junit5-mockmvc-tests.svg)

service 测业务不变量，storage 测文件往返，CLI 测命令入口，MockMvc 测 HTTP API。Surefire 把结果保存成可审计报告。

## service 测试

service 测试不启动 Spring：

```java
@Test
void createsListsAndUpdatesTasks() {
    TaskService service = service(tempDir.resolve("tasks.json"));

    var created = service.create("  Write tests  ", TaskPriority.HIGH, List.of("Java", "api", "java"));
    var done = service.updateStatus(created.id(), TaskStatus.DONE);

    assertThat(done.status()).isEqualTo(TaskStatus.DONE);
    assertThat(service.summary().total()).isEqualTo(2);
    assertThat(service.list().getFirst().tags()).containsExactly("api", "java");
}
```

这里验证的是行为契约：标题 trim、tag 归一化、状态更新、summary 统计。测试使用固定 `Clock`，避免创建时间影响断言。

## storage 和 CLI 测试

JSON storage 使用 `@TempDir`：

```java
@TempDir
Path tempDir;

@Test
void roundTripsTasksAsJson() {
    Path dataFile = tempDir.resolve("nested/tasks.json");
    JsonTaskStorage storage = new JsonTaskStorage(dataFile);
    storage.save(List.of(task));
    assertThat(storage.load()).containsExactly(task);
}
```

CLI 测试直接调用 `TaskCli.run(...)`，并捕获 stdout/stderr。这个方式能快速验证命令行为和 CSV 输出。

## MockMvc API 测试

API 测试启动 Spring 应用上下文，但不绑定真实端口：

```java
@SpringBootTest(properties = "task-tracker.data-file=target/test-data/controller-tasks.json")
@AutoConfigureMockMvc
class TaskControllerTest {
    @Autowired
    MockMvc mockMvc;
}
```

创建任务的断言：

```java
mockMvc.perform(post("/api/tasks")
        .contentType(MediaType.APPLICATION_JSON)
        .content("{\"title\":\"write api test\",\"priority\":\"HIGH\",\"tags\":[\"api\",\"java\"]}"))
    .andExpect(status().isOk())
    .andExpect(jsonPath("$.id").value(1))
    .andExpect(jsonPath("$.status").value("OPEN"));
```

校验失败也要测试：

```java
mockMvc.perform(post("/api/tasks")
        .contentType(MediaType.APPLICATION_JSON)
        .content("{\"title\":\"\"}"))
    .andExpect(status().isBadRequest())
    .andExpect(jsonPath("$.error").value("bad_request"));
```

## 测试报告

Surefire XML 证明本次 lab 的测试结果：

```text
JsonTaskStorageTest: tests=1 errors=0 failures=0
TaskCliTest: tests=1 errors=0 failures=0
TaskControllerTest: tests=2 errors=0 failures=0
TaskServiceTest: tests=2 errors=0 failures=0
```

总计 6 个测试覆盖四类边界。

## 常见错误

1. **只测 controller。** service 和 storage 错误会被 HTTP 层掩盖。
2. **文件测试写固定目录。** `@TempDir` 能让测试互不污染。
3. **只测成功路径。** 空标题、未知 ID、非法状态都应有失败测试。
4. **忽略测试报告。** 命令通过只是开始，报告能证明测试数量和失败数。

## 练习

1. 给未知 ID 的 PATCH 请求添加 404 测试。
2. 添加 CSV 转义测试，覆盖标题中含逗号的情况。
3. 把 `TaskCli.run` 的未知命令路径加入测试，确认退出码为 2。

## 参考资料

- JUnit 5：[User Guide](https://junit.org/junit5/docs/current/user-guide/)
- Spring Framework：[MockMvc](https://docs.spring.io/spring-framework/reference/testing/mockmvc.html)
- Maven Surefire：[Using JUnit Platform](https://maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html)


{% endraw %}
