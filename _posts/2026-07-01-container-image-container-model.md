---
layout: post
title: "容器第一课：image、container 和可复现运行环境"
date: 2026-07-01 20:02:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从一个 Python HTTP 小服务开始，理解镜像、容器、进程和可复现运行环境的关系。"
tags: [docker, container, deployment, teaching]
---
{% raw %}
> 主题：容器化与部署 / image / container model
> 本文 lab 已验证：本地构建镜像 `container-deployment-practice:local`，运行容器并通过 `/health`。

部署的核心需求很朴素：同一份应用在不同机器上尽量以相同方式运行。容器把应用文件、运行时、启动命令和部分系统视图打包到一个可重复启动的环境里。本包用一个 Python 标准库 HTTP 服务做最小例子，让学习者先看到一个容器真的启动、响应请求、记录状态，再解释 Dockerfile、端口、挂载、健康检查和 Compose。

## 学习目标

1. 说清 image 和 container 的区别。
2. 理解容器内部运行的是普通进程。
3. 运行本包 lab 并看到健康检查成功。
4. 知道容器解决的是环境一致性和部署边界问题。

## 先修知识

需要会打开终端，能运行 `python3 --version`。如果本机已经能运行 `docker version` 和 `docker compose version`，就可以开始。

## 核心模型

![容器第一课：image、container 和可复现运行环境](/assets/diagrams/container-image-container-model.svg)

image 是可分发的只读模板，container 是从 image 启动出来的运行实例。一个 image 可以启动多个 container；container 内部的主进程退出后，container 也结束。

## 可信资料的关键结论

- Docker 官方文档把 Docker 描述为开发、交付和运行应用的平台，核心对象包括 image 和 container。
- 容器的价值来自把应用和运行依赖一起交付，并通过命令重复启动。
- 本地教学部署要把“构建成功”和“服务可访问”同时作为验收条件。

## 逐步实现

本包 lab 的应用只有几个 HTTP 路径：

```text
/health  -> 返回服务健康状态
/visits  -> 记录一次访问
/state   -> 返回访问计数
/config  -> 返回公开配置
```

运行完整 lab：

```bash
bash run_lab.sh
```

你会看到类似输出：

```text
docker_server_version=29.1.3
compose_version=2.40.3+ds1-0ubuntu1~24.04.1
image_id=sha256:...
container_health=healthy
health_status=ok
container_deployment_status=ok
```

这条链路说明三件事：Docker 能构建 image，Docker 能从 image 启动 container，宿主机能通过端口访问容器里的 HTTP 进程。

## 常见错误

1. **把 image 当成正在运行的服务。** image 是模板，container 才是运行实例。
2. **把容器理解成完整虚拟机。** 容器更接近带隔离边界的进程集合。
3. **只看构建成功，不访问服务。** 部署学习必须看到可访问结果。
4. **把环境问题全部交给容器。** 容器能固定很多依赖，但端口、数据、配置和权限仍要设计。

## 练习或延伸

1. 运行 `docker images | grep container-deployment-practice`，找到本包 image。
2. 运行 lab 后执行 `docker ps -a --filter name=container-deployment-practice-web`，确认脚本已清理容器。
3. 把 `APP_NAME` 改成自己的值，观察 `/health` 返回如何变化。

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
