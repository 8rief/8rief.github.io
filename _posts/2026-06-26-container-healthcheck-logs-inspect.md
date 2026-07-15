---
layout: post
title: "部署后怎么知道它活着：HEALTHCHECK、logs 和 inspect"
date: 2026-06-26 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Docker health check、日志和 inspect 把“服务已启动”变成可检查证据。"
tags: [docker, healthcheck, logs, inspect, teaching]
---
{% raw %}
> 主题：容器化与部署 / healthcheck / observability
> 本文 lab 已验证：容器健康状态达到 `healthy`，日志显示健康检查和访问请求。

部署完成后，最重要的问题是服务是否真的可用。容器进程还在不等于业务接口可用，所以本包把 `/health` 写成明确健康接口，并在 Dockerfile 中加入 `HEALTHCHECK`。再配合 `docker logs` 和 `docker inspect`，可以从外部检查容器状态。

## 学习目标

1. 写出最小健康检查接口。
2. 理解 Dockerfile `HEALTHCHECK` 的作用。
3. 用 `docker logs` 查看请求记录。
4. 用 `docker inspect` 读取健康状态。

## 先修知识

需要知道 HTTP 200 通常表示请求成功。

## 核心模型

![部署后怎么知道它活着：HEALTHCHECK、logs 和 inspect](/assets/diagrams/container-healthcheck-logs-inspect.svg)

健康检查是部署系统和应用之间的可用性合同。应用提供轻量接口，容器运行时周期性调用它，并把结果记录到容器状态中。日志用于解释发生了什么，inspect 用于读取机器可处理的状态。

## 为什么需要健康检查、日志和 inspect

部署后看到容器 ID，只能说明 Docker 启动了一个实例；它不能证明应用已经完成初始化、HTTP 路由能响应、数据目录可写。健康检查解决的是机器可判断的可用性问题：运行时周期性访问应用提供的轻量接口，并把结果写入容器状态。

日志和 inspect 分别服务不同排错场景。日志回答“刚才发生了什么”，例如服务启动、健康请求、业务请求；inspect 回答“当前状态是什么”，例如健康状态、端口、挂载、环境变量和退出码。两者结合，才能把“它好像启动了”变成可审计证据。

本 lab 的健康检查只访问 `/health`，不写状态文件，也不依赖外部服务。保持轻量是为了让健康状态反映应用基本可用性，而不是把复杂业务检查放进每 5 秒一次的命令里。

## 可信资料的关键结论

- Dockerfile `HEALTHCHECK` 指令定义容器内部健康测试命令。
- `docker logs` 用于读取容器标准输出和错误输出，适合查看启动和请求记录。
- `docker inspect` 提供结构化状态，适合脚本化验收。

## 逐步实现

健康接口：

```python
if parsed.path == "/health":
    self.send_json({"status": "ok", "app": app_name(), "version": APP_VERSION})
```

Dockerfile 中的健康检查：

```dockerfile
HEALTHCHECK --interval=5s --timeout=2s --retries=5 CMD python -c "... /health ..."
```

lab 等待状态变成 healthy：

```bash
docker inspect container-deployment-practice-web --format '{{.State.Health.Status}}'
```

输出：

```text
container_health=healthy
```

日志片段：

```text
starting app=container-lab version=1.0.0 port=8080 data_dir=/data
127.0.0.1 - "GET /health HTTP/1.1" 200 -
172.17.0.1 - "GET /visits?label=restart-one HTTP/1.1" 200 -
```

## 输出怎么读

`wait_container_healthy` 会反复读取 Docker 的结构化状态，直到出现：

```text
container_health=healthy
```

这说明 Dockerfile 中的 `HEALTHCHECK` 已经至少成功执行。日志片段解释了为什么健康：

```text
starting app=container-lab version=1.0.0 port=8080 data_dir=/data
127.0.0.1 - "GET /health HTTP/1.1" 200 -
172.17.0.1 - "GET /visits?label=restart-one HTTP/1.1" 200 -
```

第一行是进程启动参数，第二行是容器内部健康检查，第三行来自宿主机经过端口映射访问容器。若 `inspect` 显示 `unhealthy`，先看 `docker logs` 是否有启动异常，再手动访问 `/health`，最后检查 HEALTHCHECK 命令里的 URL、超时和依赖。

## 常见错误

1. **只检查容器是否存在。** 容器存在不代表应用接口正常。
2. **健康检查做太重。** 健康接口应轻量、快速、依赖清晰。
3. **日志里打印秘密值。** 日志是排错材料，也可能被复制分享。
4. **把 inspect 输出当人工阅读材料。** 脚本应读取明确字段，例如 `.State.Health.Status`。

## 练习或延伸

1. 把 `/health` 临时改成返回 500，观察容器健康状态。
2. 增加 `/version` 接口，并在 health 响应里保留版本号。
3. 把 `docker logs` 输出保存到 reports，写一段部署诊断说明。

## 参考资料

- Docker 文档：[Docker overview](https://docs.docker.com/get-started/docker-overview/)
- Docker 文档：[Dockerfile concepts](https://docs.docker.com/build/concepts/dockerfile/)
- Docker 文档：[Build context](https://docs.docker.com/build/concepts/context/)
- Docker 文档：[docker container run](https://docs.docker.com/reference/cli/docker/container/run/)
- Docker 文档：[Publishing and exposing ports](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/)
- Docker 文档：[Bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
- Docker 文档：[Volumes](https://docs.docker.com/engine/storage/volumes/)
- Docker 文档：[HEALTHCHECK](https://docs.docker.com/reference/dockerfile/#healthcheck)
- Docker 文档：[Docker Compose](https://docs.docker.com/compose/)
- Docker 文档：[Compose file reference](https://docs.docker.com/reference/compose-file/)

{% endraw %}
