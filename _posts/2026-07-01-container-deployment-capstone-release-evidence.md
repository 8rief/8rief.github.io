---
layout: post
title: "结课项目：把一个 HTTP 服务容器化并留下部署证据"
date: 2026-07-01 20:09:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 Dockerfile、端口、环境变量、挂载、健康检查、Compose 和报告合成一个可复现部署小项目。"
tags: [docker, deployment, capstone, teaching]
---
{% raw %}
> 主题：容器化与部署 / capstone / release evidence
> 本文 lab 已验证：一条命令生成 Docker image、运行容器、检查健康、验证持久化、生成 JSON/SVG/Markdown/transcript。

这个结课项目的目标是把一个 HTTP 小服务从源码推进到本地可访问部署，并留下可复查证据。项目故意不引入数据库、反向代理或云平台，先把容器部署最核心的边界讲清楚：构建什么、运行什么、从哪里访问、配置从哪里来、数据放哪里、如何判断健康、如何把部署参数写成文件。

## 学习目标

1. 从空目录运行完整容器化部署 lab。
2. 解释每个产物的来源和作用。
3. 用报告证明服务可访问、状态可持久化、Compose 可解析。
4. 知道下一步如何接数据库、反向代理或云部署。

## 先修知识

建议按顺序读完本包前七篇。需要本机 Docker 和 Docker Compose 可用。

## 核心模型

![结课项目：把一个 HTTP 服务容器化并留下部署证据](/assets/diagrams/container-deployment-capstone-release-evidence.svg)

结课项目的证据链是：Dockerfile 构建 image，image 启动 container，端口发布让宿主机访问服务，环境变量提供配置，bind mount 保存状态，healthcheck/日志/inspect 证明可用，Compose 固化部署参数，reports 保存验收结果。

## 可信资料的关键结论

- Docker 官方文档的核心路径是构建 image、运行 container、发布端口、管理数据和使用 Compose 描述多服务应用。
- 发布证据应覆盖构建、运行、访问、状态、配置和清理，不只是一条成功命令。
- 本地容器化 lab 的边界是学习部署机制；生产环境还需要单独处理网络入口、TLS、资源、密钥、镜像供应链和监控。

## 逐步实现

运行：

```bash
bash run_lab.sh
```

核心输出：

```text
docker_server_version=29.1.3
compose_version=2.40.3+ds1-0ubuntu1~24.04.1
container_health=healthy
health_status=ok
visits_after_smoke=2
visits_after_smoke=4
compose_config_ok=True
container_deployment_status=ok
```

项目结构：

```text
container-deployment-practice/
  app/server.py
  Dockerfile
  .dockerignore
  compose.yaml
  scripts/smoke.py
  scripts/test_server.py
  scripts/write_report.py
  data/runtime/state.json
  reports/summary.json
  reports/container_deployment_flow.svg
  reports/report.md
  reports/transcript.txt
```

可展示产物：

```text
reports/report.md
reports/container_deployment_flow.svg
reports/summary.json
```

可审计产物：

```text
reports/transcript.txt
data/runtime/state.json
compose.yaml
Dockerfile
```

`reports/summary.json` 中的关键结果：

```json
{
  "health_status": "ok",
  "visits_after_first_smoke": 2,
  "visits_after_restart": 4,
  "state_file_exists": true,
  "compose_config_ok": true
}
```

## 常见错误

1. **只交 Dockerfile，没有证明服务能访问。** 容器化交付必须有运行证据。
2. **只发一条很长的 docker run 命令。** 命令可以教学，发布参数应沉淀到 Compose 或脚本。
3. **把运行数据放进 image。** image 应可替换，数据应外置。
4. **把本地 lab 当成完整生产部署。** 下一步还需要反向代理、TLS、资源限制、镜像仓库、CI/CD 和监控。

## 练习或延伸

1. 给服务增加 `/ready` 接口，区分进程存活和依赖就绪。
2. 把 image 推送到私有 registry 前，写一份标签和版本策略。
3. 增加一个 Redis 或 SQLite 服务，改造 Compose 为双服务部署。
4. 用 GitHub Actions 或本地脚本自动运行 build、smoke 和报告生成。

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
