---
layout: post
title: "Spring Boot REST API：把 Java service 发布成本地 HTTP 接口"
date: 2026-05-08 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 controller、validation、exception handler 和 curl smoke，把 task tracker service 暴露为本地 REST API。"
tags: [java, spring-boot, rest-api, validation, curl]
---
{% raw %}


> 主题：Java 从0到后端 API / Spring Boot / REST / validation / local smoke  
> 本文 lab 在 `127.0.0.1:18180` 启动本地服务，执行 POST、GET、PATCH 和 CSV 导出 smoke。

当 service 层已经稳定后，REST API 的任务是把 HTTP 请求转换为 service 调用，并把结果转换为 JSON 或 CSV。API 层不应重新实现业务规则，它负责路由、请求绑定、校验、状态码和响应格式。

## 学习目标

1. 用 `@RestController` 定义 REST endpoint。
2. 用 `@Valid` 和 Bean Validation 校验请求体。
3. 用 service 层复用业务规则。
4. 用 exception handler 统一错误响应。
5. 用本地 curl smoke 验证真实 HTTP 边界。

## 先修知识

需要理解 HTTP 方法、JSON 请求体和状态码。本文沿用前几讲的 task tracker service。

## 为什么需要 REST API 适配层

service 层能被 Java 代码调用，但其他程序不能直接调用 Java 对象。REST API 把这个能力变成 HTTP 协议：前端、脚本、curl 或其他服务可以用 JSON 请求创建任务、查询摘要、更新状态。

API 层的职责是适配，而不是重新写业务规则。它要处理路由、请求体绑定、参数校验、异常到状态码的转换、JSON/CSV 响应格式。真正的任务创建、状态更新和 summary 统计仍然交给 `TaskService`。这样 CLI 和 API 会共享同一套行为。

本地教学服务默认绑定 `127.0.0.1`，是因为 REST API 一旦监听网络地址，就会形成外部访问面。入门阶段先证明请求路径、错误边界和 smoke 流程；部署到网络前再补认证、授权、跨域、限流和审计日志。


## 核心模型

请求进入 Spring MVC 后，按 controller、validation、service、响应转换的路径流动：

![Spring Boot REST 请求路径](/assets/diagrams/java-spring-boot-rest-api.svg)

controller 是适配层，service 是业务层，storage 是持久化边界。

## Controller

核心 controller：

```java
@Validated
@RestController
@RequestMapping("/api/tasks")
public class TaskController {
    private final TaskService service;

    @GetMapping
    public List<TaskItem> list() {
        return service.list();
    }

    @PostMapping
    public TaskItem create(@Valid @RequestBody CreateTaskRequest request) {
        return service.create(request.title(), request.priority(), request.tags());
    }

    @PatchMapping("/{id}/status")
    public TaskItem updateStatus(@PathVariable long id, @Valid @RequestBody UpdateStatusRequest request) {
        return service.updateStatus(id, request.status());
    }
}
```

controller 方法很薄：接收请求，调用 service，返回结果。薄 controller 更容易测试，也能保证 CLI 和 API 共享同一套业务规则。

## 错误响应

领域异常转换成 HTTP 状态码：

```java
@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(TaskNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    ApiError notFound(TaskNotFoundException exception) {
        return new ApiError("not_found", exception.getMessage());
    }

    @ExceptionHandler({IllegalArgumentException.class, MethodArgumentNotValidException.class})
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    ApiError badRequest(Exception exception) {
        return new ApiError("bad_request", exception.getMessage());
    }
}
```

这样调用者收到稳定 JSON 错误结构，避免依赖堆栈文本。

## 本地 API smoke

lab 启动本机服务：

```bash
java -jar target/task-tracker-0.1.0.jar \
  --server.address=127.0.0.1 \
  --server.port=18180 \
  --task-tracker.data-file=reports/tasks-api.json
```

创建任务：

```bash
curl -s --fail -H 'Content-Type: application/json' \
  -d '{"title":"write README","priority":"HIGH","tags":["docs","java"]}' \
  http://127.0.0.1:18180/api/tasks
```

响应摘录：

```json
{
  "id": 1,
  "title": "write README",
  "status": "OPEN",
  "priority": "HIGH",
  "tags": ["docs", "java"]
}
```

更新状态后导出 CSV：

```text
id,title,status,priority,tags,createdAt
1,write README,DONE,HIGH,docs;java,2026-07-03T15:17:41.980565873Z
```

## 安全边界

本文服务只绑定 `127.0.0.1`。这个选择让实验流量停留在本机。真正部署到网络前，还需要认证、授权、审计日志、限流、跨域策略和数据库事务设计。

## 输出怎么读

API smoke 的第一段是创建任务响应：

```json
{
  "id": 1,
  "title": "write README",
  "status": "OPEN",
  "priority": "HIGH",
  "tags": ["docs", "java"]
}
```

`id=1` 说明当前 API 数据文件是干净的；`status=OPEN` 说明创建接口没有让调用者直接指定完成状态；`tags` 说明 JSON 数组已被绑定到 Java 集合。

summary 响应是聚合视图：

```json
{ "total": 1, "open": 1, "inProgress": 0, "done": 0 }
```

这里 `total` 应等于当前任务数量，`open + inProgress + done` 也应等于 `total`。如果不相等，错误通常在 summary 统计或状态枚举扩展后没有同步更新。

PATCH 后导出的 CSV：

```text
id,title,status,priority,tags,createdAt
1,write README,DONE,HIGH,docs;java,...
```

这证明更新状态、持久化和 CSV 导出共享同一份数据。读 smoke 输出时要看完整链路：POST 创建、GET summary、PATCH 更新、GET CSV 导出，四步都成功才说明 REST 适配层可展示。


## 常见错误

1. **controller 里写业务逻辑。** 这样 CLI 和 API 行为会分叉。
2. **不校验请求体。** 空标题等问题应在入口处被拒绝。
3. **错误响应无结构。** 客户端需要可解析的错误码和消息。
4. **教学阶段直接暴露到外网。** 本地实验优先绑定 loopback。

## 练习

1. 增加 `GET /api/tasks/{id}`，并补充 404 测试。
2. 为创建请求增加 tag 数量上限。
3. 增加 `GET /api/tasks/export.csv` 的 Content-Type 断言。

## 参考资料

- Spring Boot 文档：[Developing Web Applications](https://docs.spring.io/spring-boot/reference/web/servlet.html)
- Spring Framework 文档：[Annotated Controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods.html)
- Spring Framework 文档：[Validation](https://docs.spring.io/spring-framework/reference/core/validation/beanvalidation.html)


{% endraw %}
