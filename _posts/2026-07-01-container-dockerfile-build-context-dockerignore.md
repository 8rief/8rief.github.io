---
layout: post
title: "Dockerfile 怎么变成镜像：build context、COPY 和 .dockerignore"
date: 2026-07-01 20:03:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个最小 Dockerfile 理解构建上下文、COPY、基础镜像、非 root 用户和 .dockerignore。"
tags: [docker, dockerfile, build, teaching]
---
{% raw %}
> 主题：容器化与部署 / Dockerfile / build context
> 本文 lab 已验证：`docker build -t container-deployment-practice:local .` 成功，并生成可运行镜像。

Dockerfile 是把源码目录变成 image 的说明书。初学者最容易忽略 build context：`docker build .` 里的点会把当前目录作为构建上下文发送给 Docker，Dockerfile 只能从这个上下文里 `COPY` 文件。`.dockerignore` 的作用是把不该进入上下文的文件排除掉。

## 学习目标

1. 理解 Dockerfile 每条指令对 image 的影响。
2. 知道 build context 和 `.dockerignore` 的边界。
3. 使用非 root 用户运行应用。
4. 解释为什么 reports、运行数据和任务记录不进入 image。

## 先修知识

需要知道项目目录里有源码、报告、数据和临时文件。还需要知道 `COPY A B` 表示把文件复制到镜像内路径。

## 核心模型

![Dockerfile 怎么变成镜像：build context、COPY 和 .dockerignore](/assets/diagrams/container-dockerfile-build-context-dockerignore.svg)

构建过程从基础镜像开始，逐条执行 Dockerfile 指令，每一步形成新的文件系统层。构建上下文决定 Docker 能看到哪些本地文件，`.dockerignore` 决定哪些文件不送进上下文。

## 可信资料的关键结论

- Docker 官方文档说明 `docker build` 使用 Dockerfile 和构建上下文创建 image。
- 构建上下文会发送给 Docker daemon，`.dockerignore` 用来排除不需要或敏感的文件。
- 最小权限运行和明确启动命令让 image 更容易审计。

## 逐步实现

本包 Dockerfile：

```dockerfile
FROM python:3.14-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    DATA_DIR=/data \
    APP_NAME=container-lab

COPY app/server.py /app/server.py

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app

USER appuser
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=2s --retries=5 CMD python -c "..."
CMD ["python", "/app/server.py"]
```

`.dockerignore`：

```text
.git
__pycache__/
*.pyc
reports/
data/runtime/
internal-task-notes/
*.log
.env
```

运行构建：

```bash
docker build -t container-deployment-practice:local .
```

lab transcript 中可以看到构建阶段：加载 Dockerfile、加载 `.dockerignore`、复制 `app/server.py`、创建用户、导出 image。

## 常见错误

1. **把整个项目目录无差别送入构建上下文。** 报告、运行数据、`.env` 和任务记录都应排除。
2. **在镜像里默认用 root 跑服务。** 教学 lab 也应养成最小权限习惯。
3. **把 `EXPOSE` 当成端口发布。** `EXPOSE` 是镜像元数据，宿主机访问还需要 `-p`。
4. **在 Dockerfile 里写入本机绝对路径。** 构建应只依赖上下文中的相对文件。

## 练习或延伸

1. 把 `.dockerignore` 中的 `reports/` 删除，重新构建并观察 build context 大小变化。
2. 把 `APP_NAME` 默认值改成 `dockerfile-lab`，重新构建并访问 `/health`。
3. 尝试删除 `USER appuser`，对比容器内 `id` 输出。

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
