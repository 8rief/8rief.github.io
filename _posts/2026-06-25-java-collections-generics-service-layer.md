---
layout: post
title: "Java Collections 和 service 层：把业务不变量放在一个地方"
date: 2026-06-25 17:12:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Map、List、Set、Optional 和 synchronized service 组织任务列表、唯一 ID、状态更新和汇总统计。"
tags: [java, collections, generics, service-layer, invariants]
---
{% raw %}


> 主题：Java 从0到后端 API / Collections / 泛型 / service layer  
> 本文 lab 的 service 测试覆盖创建、列表排序、状态更新、summary 统计、标题校验和 tag 归一化。

CLI 和 HTTP API 都会修改任务数据。如果两个入口各自实现创建和更新逻辑，ID 生成、标题校验、状态统计很快会分叉。service 层的目标是把业务不变量集中起来：任务 ID 唯一、列表按 ID 稳定排序、空标题被拒绝、tag 归一化、每次修改都持久化。

## 学习目标

1. 用 `Map<Long, TaskItem>` 保存按 ID 索引的任务。
2. 用 `List`、`Set`、`TreeSet` 表达顺序、集合和去重。
3. 用 `Optional` 处理默认优先级。
4. 理解 service 层如何同时服务 CLI 和 API。
5. 解释小项目里的同步边界。

## 先修知识

需要理解 Java 泛型的基本形式，例如 `List<String>`、`Map<Long, TaskItem>`。

## 核心模型

service 层把输入命令变成稳定的状态变化：

![service 层不变量](/assets/diagrams/java-collections-generics-service-layer.svg)

CLI 和 controller 不直接改 Map，它们调用 service。service 负责校验、创建对象、更新 Map、调用 storage 保存，并提供 summary 和 CSV 输出。

## 任务集合

核心字段如下：

```java
private final Map<Long, TaskItem> tasksById = new LinkedHashMap<>();
private long nextId = 1;
```

`LinkedHashMap` 保留插入顺序，但对外返回时仍按 ID 排序：

```java
public synchronized List<TaskItem> list() {
    return tasksById.values().stream()
            .sorted(Comparator.comparingLong(TaskItem::id))
            .toList();
}
```

这让输出稳定，便于测试和日志对比。

## 创建任务

创建逻辑集中在 service：

```java
public synchronized TaskItem create(String title, TaskPriority priority, Collection<String> tags) {
    String normalizedTitle = normalizeTitle(title);
    TaskPriority normalizedPriority = Optional.ofNullable(priority).orElse(TaskPriority.MEDIUM);
    Set<String> normalizedTags = normalizeTags(tags);
    TaskItem task = new TaskItem(nextId++, normalizedTitle, TaskStatus.OPEN,
            normalizedPriority, normalizedTags, Instant.now(clock));
    tasksById.put(task.id(), task);
    persist();
    return task;
}
```

`Optional.ofNullable(priority).orElse(...)` 表达默认值。`normalizeTags` 使用 `TreeSet` 去重并排序，让 tag 输出可预测。

## 更新和统计

更新状态先检查任务存在，再替换 Map 中的对象：

```java
public synchronized TaskItem updateStatus(long id, TaskStatus status) {
    if (status == null) {
        throw new IllegalArgumentException("status is required");
    }
    TaskItem updated = get(id).withStatus(status);
    tasksById.put(id, updated);
    persist();
    return updated;
}
```

summary 只从当前集合计算：

```java
public synchronized TaskSummary summary() {
    long open = count(TaskStatus.OPEN);
    long inProgress = count(TaskStatus.IN_PROGRESS);
    long done = count(TaskStatus.DONE);
    return new TaskSummary(tasksById.size(), open, inProgress, done);
}
```

这样 summary 不会和任务列表脱节。

## 为什么这里用了 synchronized

示例项目用内存 Map 和 JSON 文件保存数据。`synchronized` 让单进程内的修改串行执行，避免两个请求同时写文件导致丢失更新。它适合教学项目；真实服务在多实例部署、数据库事务和锁策略上还要进一步设计。

## 常见错误

1. **在 controller 中直接操作 Map。** 这样 CLI 和 API 很难共享逻辑。
2. **让 summary 自己保存计数。** 计数可能和任务集合不一致。
3. **tag 不归一化。** `Java`、`java`、` java ` 会变成三个值。
4. **忽略并发写入。** 即使是本地教学项目，也要知道共享 Map 和文件写入存在竞态。

## 练习

1. 增加 `IN_PROGRESS` 命令，并让 summary 测试覆盖它。
2. 给 tag 增加最大数量限制，例如最多 5 个。
3. 把 `LinkedHashMap` 换成 `ConcurrentHashMap`，思考它能否替代当前整个 service 的同步策略。

## 参考资料

- Oracle Java API：[java.util package](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/package-summary.html)
- Dev.java：[Collections Framework](https://dev.java/learn/api/collections-framework/)
- Oracle Java API：[Optional](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Optional.html)


{% endraw %}
