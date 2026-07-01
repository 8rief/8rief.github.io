---
layout: post
title: "从一条 docker run 到 compose.yaml：把部署参数写成文件"
date: 2026-07-01 20:08:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 Compose 固定 image、端口、环境变量、挂载和健康检查，避免手工命令越写越长。"
tags: [docker, compose, deployment, teaching]
---
{% raw %}
> 主题：容器化与部署 / Docker Compose / local deployment
> 本文 lab 已验证：`docker compose config` 成功解析 compose.yaml。

`docker run` 适合第一次理解容器启动，但真实项目的参数会越来越长：端口、环境变量、挂载、健康检查、依赖服务。Compose 把这些参数写进 `compose.yaml`，让本地部署变成可复查文件。

## 学习目标

1. 读懂一个单服务 `compose.yaml`。
2. 把 `docker run` 参数映射到 Compose 字段。
3. 用 `docker compose config` 验证配置。
4. 理解 Compose 为多服务项目做准备。

## 先修知识

建议先读端口、配置、挂载和健康检查几篇。

## 核心模型

![从一条 docker run 到 compose.yaml：把部署参数写成文件](/assets/diagrams/container-compose-local-deployment.svg)

Compose 文件描述一组服务。每个服务可以指定 build、image、ports、environment、volumes 和 healthcheck。`docker compose config` 会解析并规范化配置，适合作为发布前检查。

## 可信资料的关键结论

- Docker Compose 用一个文件定义和运行多容器应用。
- Compose service 支持 `build`、`image`、`ports`、`environment`、`volumes`、`healthcheck` 等常用部署字段。
- `docker compose config` 是检查 Compose 文件能否正确解析的直接命令。

## 逐步实现

本包 `compose.yaml`：

```yaml
services:
  web:
    build:
      context: .
    image: container-deployment-practice:local
    container_name: container-deployment-practice-web
    environment:
      APP_NAME: compose-container-lab
      PORT: "8080"
      DATA_DIR: /data
    ports:
      - "127.0.0.1:18080:8080"
    volumes:
      - ./data/runtime:/data
    healthcheck:
      test: ["CMD", "python", "-c", "..."]
      interval: 5s
      timeout: 2s
      retries: 5
```

验证配置：

```bash
docker compose config
```

lab 把结果记录为：

```json
{
  "compose_config_ok": true
}
```

以后如果增加数据库或缓存服务，可以在同一个 `services` 下继续添加，例如 `db` 或 `redis`。

## 常见错误

1. **把 Compose 当成生产编排的全部答案。** 它非常适合本地和小型部署，但复杂生产集群还需要更完整的平台能力。
2. **手工命令改了，Compose 文件没有同步。** 最终应以文件为准。
3. **把秘密值直接写在 compose.yaml。** 公开教学文件只保留非秘密配置。
4. **忽略 `docker compose config`。** 配置文件也需要可解析检查。

## 练习或延伸

1. 运行 `docker compose config`，找到 ports、environment 和 volumes 规范化后的形式。
2. 用 `docker compose up --build` 手动启动服务，再用 `docker compose down` 清理。
3. 给 Compose 增加一个只读环境变量 `APP_ENV: local`。

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
