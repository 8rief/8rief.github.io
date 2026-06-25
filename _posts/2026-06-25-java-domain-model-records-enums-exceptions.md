---
layout: post
title: "Java 领域模型：用 record、enum 和异常写清任务数据"
date: 2026-06-25 17:11:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 record、enum、package 和领域异常表达任务系统的数据形状和失败边界。"
tags: [java, record, enum, exceptions, domain-model]
---
{% raw %}


> 主题：Java 从0到后端 API / record / enum / package / exception  
> 本文代码来自同一个 task tracker lab。测试覆盖创建任务、状态更新、空标题拒绝和 JSON 往返。

后端 API 的基础层是数据模型。字段名、状态集合、错误类型如果没有明确表达，HTTP、CLI、JSON 文件和测试会各自发明一套约定。Java 的 `record`、`enum` 和异常类型适合把这些约定写进类型系统。

## 学习目标

1. 用 `record` 表达不可变数据载体。
2. 用 `enum` 固定状态和优先级的合法取值。
3. 用 package 按职责拆分 domain、service、storage、web。
4. 用领域异常表达可预期失败。
5. 理解请求对象和内部对象的边界。

## 先修知识

需要知道 Java 类、字段、方法和包名的基本概念。还不需要掌握泛型和 Spring 注解。

## 核心模型

task tracker 的领域模型可以拆成请求数据、内部记录、枚举状态、service 校验和异常边界。

![Java 领域模型分层](/assets/diagrams/java-domain-model-records-enums-exceptions.svg)

控制器和 CLI 都可以传入请求数据，但最终进入 service 的是明确的 Java 类型。

## 用 record 表达任务

任务对象是不可变记录：

```java
public record TaskItem(
        long id,
        String title,
        TaskStatus status,
        TaskPriority priority,
        Set<String> tags,
        Instant createdAt
) {
    public TaskItem withStatus(TaskStatus newStatus) {
        return new TaskItem(id, title, newStatus, priority, tags, createdAt);
    }
}
```

`record` 自动生成构造器、访问器、`equals`、`hashCode` 和 `toString`。这里的 `withStatus` 返回新对象，避免在原对象上改状态。任务历史写入 JSON 时，字段结构也更稳定。

## 用 enum 固定合法状态

状态和优先级只有有限取值：

```java
public enum TaskStatus {
    OPEN,
    IN_PROGRESS,
    DONE
}

public enum TaskPriority {
    LOW,
    MEDIUM,
    HIGH
}
```

`enum` 的价值在于把非法字符串挡在边界外。HTTP 请求传入未知状态时，Spring/Jackson 会在绑定阶段发现错误；CLI 传入未知优先级时，`TaskPriority.valueOf(...)` 会失败。

## 请求对象和内部对象

创建任务的请求对象只包含用户能提供的字段：

```java
public record CreateTaskRequest(
        @NotBlank(message = "title must not be blank") String title,
        TaskPriority priority,
        Set<String> tags
) {
}
```

`id`、`status`、`createdAt` 由 service 生成，请求对象只承载用户输入。这样 API 调用者无法伪造任务编号或创建时间。

## 领域异常

任务不存在是业务边界，不应让底层 `NullPointerException` 泄漏出来：

```java
public class TaskNotFoundException extends RuntimeException {
    public TaskNotFoundException(long id) {
        super("task not found: " + id);
    }
}
```

HTTP 层会把这个异常转换成 404，CLI 层会打印错误信息。异常类型让不同入口共享同一套失败语义。

## 本地验证

service 测试中创建任务后检查字段：

```java
var created = service.create("  Write tests  ", TaskPriority.HIGH, List.of("Java", "api", "java"));
var done = service.updateStatus(created.id(), TaskStatus.DONE);

assertThat(done.status()).isEqualTo(TaskStatus.DONE);
assertThat(service.list().getFirst().title()).isEqualTo("Write tests");
assertThat(service.list().getFirst().tags()).containsExactly("api", "java");
```

这证明标题会 trim，tag 会归一化并去重，状态更新会返回新的任务对象。

## 常见错误

1. **让请求对象直接成为数据库对象。** 用户输入和内部状态生成逻辑应分层。
2. **用任意字符串表示状态。** 字符串让非法值进入更深层代码。
3. **把所有失败都写成 `RuntimeException`。** 明确异常类型能让 API 和 CLI 做出一致响应。
4. **包名只按技术栈分。** 小项目也应按 domain、service、storage、web 等职责拆分。

## 练习

1. 给任务增加 `dueDate` 字段，并决定它属于创建请求还是服务端生成字段。
2. 给 `TaskStatus` 增加 `ARCHIVED`，补充 summary 统计和测试。
3. 增加 `TaskNotFoundException` 的 CLI 测试，验证错误输出。

## 参考资料

- Oracle Java 21 语言指南：[Record Classes](https://docs.oracle.com/en/java/javase/21/language/records.html)
- Oracle Java 21 语言指南：[Enum Classes](https://docs.oracle.com/en/java/javase/21/language/enum-classes.html)
- Oracle Java 21 API：[RuntimeException](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/RuntimeException.html)


{% endraw %}
