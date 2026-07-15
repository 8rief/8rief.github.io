---
layout: post
title: "Dockerfile 怎么变成镜像：build context、COPY 和 .dockerignore"
date: 2026-06-24 09:00:00 +0800
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

## 为什么需要 build context 和 .dockerignore

Docker 构建并不是直接读取你电脑上的所有文件。`docker build .` 会把当前目录作为 build context 发送给构建器，Dockerfile 的 `COPY` 只能从这个上下文里取文件。这个边界如果不理解，常见问题有两类：需要的文件没进上下文，或者不该进镜像的报告、缓存、运行数据和秘密文件被送进了上下文。

`.dockerignore` 解决的是上下文边界控制。它让构建只看到源码和必要配置，排除 `reports/`、`data/runtime/`、`.env`、日志和任务记录。这样 image 更小，构建更快，也减少把本地状态带进公开交付物的风险。

Dockerfile 本身则定义 image 的可复现构建步骤。基础镜像决定运行时，`COPY` 决定应用文件，`USER` 决定最小权限，`CMD` 决定启动入口。每条指令都应该服务于运行这个应用，而不是把整个工作目录打包进去。

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

## 输出怎么读

构建日志里有几行值得专门看：

```text
[internal] load build definition from Dockerfile
[internal] load .dockerignore
[internal] load build context
naming to docker.io/library/container-deployment-practice:local done
```

第一行说明 Dockerfile 被找到，第二行说明 `.dockerignore` 参与了构建，第三行说明上下文被发送给构建器。最后一行说明 image tag 已经指向新构建结果。若 `COPY app/server.py /app/server.py` 报错，优先检查文件是否在 build context 内，以及 `.dockerignore` 是否误排除了它。

本 lab 的 Dockerfile 还会创建 UID `10001` 的 `appuser`，并把 `/data` 和 `/app` 权限交给它。这个输出不一定每次都重新执行，因为 Docker 可能使用缓存；你可以通过 `docker image inspect container-deployment-practice:local` 继续查看 image 元数据。

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
