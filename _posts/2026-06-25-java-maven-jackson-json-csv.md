---
layout: post
title: "Maven 依赖和 Jackson 文件处理：把任务数据落到 JSON 和 CSV"
date: 2026-06-25 17:13:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Maven 管理 Jackson，使用 ObjectMapper、JavaTimeModule、原子写入和 CSV 转义处理任务数据。"
tags: [java, maven, jackson, json, csv, file-io]
---
{% raw %}


> 主题：Java 从0到后端 API / Maven dependency / Jackson / JSON / CSV  
> 本文 lab 已验证 JSON round trip、CLI CSV 导出和 API CSV 导出。

后端项目的数据通常要离开内存：保存到文件、数据库或消息队列。教学项目先用 JSON 文件做持久化，用 CSV 做可读导出。这样可以同时学习 Maven 依赖、Jackson 序列化、Java 时间类型、文件写入和 CSV 转义。

## 学习目标

1. 理解 Maven dependency 如何把 Jackson 引入项目。
2. 用 `ObjectMapper` 读写 `List<TaskItem>`。
3. 用 `JavaTimeModule` 处理 `Instant`。
4. 用临时文件加 move 减少半写入风险。
5. 解释 JSON 和 CSV 的适用边界。

## 先修知识

需要理解 JSON 对象、数组和 CSV 表头。需要知道上一讲的 `TaskItem` 列表来自 service 层。

## 核心模型

数据文件处理链如下：

![JSON/CSV 文件处理链](/assets/diagrams/java-maven-jackson-json-csv.svg)

JSON 保留任务对象的嵌套结构，适合程序重新加载。CSV 是面向人工检查和表格工具的导出格式。

## Maven 依赖

Spring Boot starter 已包含 Jackson 基础模块，项目显式加入 Java Time 模块：

```xml
<dependency>
  <groupId>com.fasterxml.jackson.datatype</groupId>
  <artifactId>jackson-datatype-jsr310</artifactId>
</dependency>
```

`TaskItem` 中有 `Instant createdAt`。注册 `JavaTimeModule` 后，Jackson 可以把它序列化成 ISO-8601 字符串。

## JSON storage

storage 类保存文件路径和 ObjectMapper：

```java
private static final TypeReference<List<TaskItem>> TASK_LIST = new TypeReference<>() {};
private final Path dataFile;
private final ObjectMapper objectMapper;

public JsonTaskStorage(Path dataFile) {
    this.dataFile = dataFile;
    this.objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());
}
```

读取逻辑把不存在的文件视为空任务列表：

```java
public List<TaskItem> load() {
    if (!Files.exists(dataFile)) {
        return List.of();
    }
    return objectMapper.readValue(dataFile.toFile(), TASK_LIST);
}
```

这个选择适合本地小项目：第一次运行没有数据文件时，服务可以正常启动。

## 原子写入

保存时先写临时文件，再移动到目标路径：

```java
Path temp = dataFile.resolveSibling(dataFile.getFileName() + ".tmp");
objectMapper.writerWithDefaultPrettyPrinter().writeValue(temp.toFile(), tasks);
moveAtomicallyWhenPossible(temp, dataFile);
```

如果平台支持原子移动，就用 `ATOMIC_MOVE`；不支持时退回普通替换。这个设计减少写入中断留下半个 JSON 的风险。

## CSV 导出

CSV 只导出扁平字段：

```java
StringBuilder builder = new StringBuilder("id,title,status,priority,tags,createdAt\n");
for (TaskItem task : tasks) {
    builder.append(task.id()).append(',')
            .append(escape(task.title())).append(',')
            .append(task.status()).append(',')
            .append(task.priority()).append(',')
            .append(escape(String.join(";", task.tags()))).append(',')
            .append(task.createdAt()).append('\n');
}
```

标题和 tags 需要 CSV 转义，因为它们可能包含逗号、引号或换行。数字和 enum 可以直接输出。

## 本地执行结果

CLI CSV 摘要：

```text
id,title,status,priority,tags,createdAt
1,write-tests,DONE,HIGH,cli,2026-06-25T09:27:57.412231357Z
2,ship-docs,OPEN,MEDIUM,cli,2026-06-25T09:28:01.093213008Z
```

API CSV 摘要：

```text
id,title,status,priority,tags,createdAt
1,write README,DONE,HIGH,docs;java,2026-06-25T09:28:15.219874423Z
```

## 常见错误

1. **直接拼 JSON 字符串。** 对象字段、数组和时间格式很容易出错。
2. **忘记 Java Time 模块。** `Instant`、`LocalDate` 等类型需要明确支持。
3. **CSV 不转义。** 标题中有逗号时，表格列会错位。
4. **写目标文件时中断。** 临时文件加移动能降低报告损坏风险。

## 练习

1. 增加一个 `import-csv` 命令，把 CSV 重新导入 JSON。
2. 给 JSON 文件写入无效内容，观察 storage 如何报错。
3. 给标题加入逗号，确认 CSV 导出仍能被表格工具正确解析。

## 参考资料

- Jackson Databind：[Project repository](https://github.com/FasterXML/jackson-databind)
- Jackson Java 8 Modules：[Project repository](https://github.com/FasterXML/jackson-modules-java8)
- Oracle Java API：[Files](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/Files.html)
- Maven 文档：[Introduction to Dependency Mechanism](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html)


{% endraw %}
