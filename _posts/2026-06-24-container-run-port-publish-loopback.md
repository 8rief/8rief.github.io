---
layout: post
title: "容器服务如何被宿主机访问：端口发布和 loopback 边界"
date: 2026-06-24 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 `-p 127.0.0.1:18080:8080` 理解容器端口、宿主机端口和本地访问边界。"
tags: [docker, ports, networking, teaching]
---
{% raw %}
> 主题：容器化与部署 / port publishing / loopback
> 本文 lab 已验证：宿主机访问 `http://127.0.0.1:18080/health` 返回 `status=ok`。

容器里的服务监听 8080，并不会自动变成宿主机的 8080。端口发布把宿主机某个地址和端口转发到容器端口。本包使用 `127.0.0.1:18080:8080`，让学习者只能从本机访问这个教学服务，避免把练习服务暴露到局域网。

## 学习目标

1. 区分容器端口和宿主机端口。
2. 解释 `127.0.0.1:18080:8080` 的三个部分。
3. 用 curl 或 Python smoke 脚本验证服务可访问。
4. 知道为什么本地 lab 默认绑定 loopback。

## 先修知识

需要知道 URL 里的 `127.0.0.1` 指本机，`18080` 是端口号。

## 核心模型

![容器服务如何被宿主机访问：端口发布和 loopback 边界](/assets/diagrams/container-run-port-publish-loopback.svg)

容器网络边界内的服务监听容器端口；`docker run -p HOST_IP:HOST_PORT:CONTAINER_PORT` 在宿主机上建立访问入口。绑定 `127.0.0.1` 表示只接受本机访问。

## 为什么需要端口发布边界

容器内的 HTTP 服务监听 `0.0.0.0:8080`，这个地址属于容器自己的网络视图。宿主机浏览器直接访问 `127.0.0.1:8080`，并不会自动进入容器。端口发布解决的核心问题是把宿主机上的一个入口转发到容器内部服务。

`127.0.0.1:18080:8080` 同时表达了访问范围和端口映射。左边的 `127.0.0.1` 限制只有本机能连；中间的 `18080` 是宿主机入口；右边的 `8080` 是容器内服务端口。这个写法适合教学和本地开发，因为它能看到结果，同时避免把练习服务暴露到局域网。

理解这个边界也能减少排错时间。访问超时可能是容器没启动、应用没监听 `0.0.0.0`、宿主机端口冲突或映射写错。把“容器端口”和“宿主机端口”分开，才能快速定位问题。

## 可信资料的关键结论

- Docker `run -p` 用于发布容器端口，使宿主机或外部客户端可以访问容器服务。
- 端口发布可以指定宿主机 IP；本地教学默认绑定 loopback 能缩小暴露范围。
- 端口可访问性是部署验收的核心证据。

## 逐步实现

lab 使用的运行命令：

```bash
docker run -d --rm \
  --name container-deployment-practice-web \
  -p 127.0.0.1:18080:8080 \
  -e APP_NAME=container-lab \
  -e DATA_DIR=/data \
  -v "$PWD/data/runtime:/data" \
  container-deployment-practice:local
```

端口映射拆开看：

```text
127.0.0.1  宿主机监听地址，只允许本机访问
18080      宿主机端口，浏览器或 curl 连接它
8080       容器内服务端口，Python HTTP 服务监听它
```

验证：

```bash
python3 scripts/smoke.py --base-url http://127.0.0.1:18080 --label first --out reports/smoke-first.json
```

输出：

```text
health_status=ok
app_name=container-lab
visits_after_smoke=2
```

## 输出怎么读

smoke 脚本访问的是宿主机地址：

```text
health_status=ok
app_name=container-lab
visits_after_smoke=2
event_count=2
```

`health_status=ok` 说明 `http://127.0.0.1:18080/health` 能到达容器内应用。`app_name=container-lab` 说明环境变量已经被容器进程读取。`visits_after_smoke=2` 和 `event_count=2` 说明脚本连续访问了两次 `/visits`，服务不仅能响应健康检查，也能写入状态。

如果 `docker ps` 显示容器运行，但 smoke 脚本失败，下一步应检查 `docker port container-deployment-practice-web`、运行命令里的 `-p` 参数，以及应用是否在容器内监听 `0.0.0.0:8080`。不要直接把容器内部端口当成宿主机端口。

## 常见错误

1. **把容器端口直接写进浏览器。** 宿主机要访问已发布的宿主机端口。
2. **把教学服务绑定到所有网卡。** 初学练习默认使用 `127.0.0.1` 更安全。
3. **忘记检查应用实际监听地址。** 容器内服务应监听 `0.0.0.0`，否则端口转发可能无法访问。
4. **用同一个宿主机端口运行多个容器。** 端口会冲突。

## 练习或延伸

1. 把宿主机端口改成 `18081`，重新运行 smoke 脚本。
2. 访问 `/state`，观察访问次数。
3. 故意访问 `http://127.0.0.1:8080/health`，理解宿主机端口和容器端口的区别。

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
