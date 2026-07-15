---
layout: post
title: "容器配置从环境变量开始：APP_NAME、PORT 和秘密边界"
date: 2026-06-25 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用环境变量配置容器行为，同时说明公开配置和秘密值的边界。"
tags: [docker, configuration, environment, teaching]
---
{% raw %}
> 主题：容器化与部署 / environment config / secrets boundary
> 本文 lab 已验证：`APP_NAME=container-lab` 进入 `/health` 和 `/config` 的公开输出。

部署时经常需要在不改代码的情况下调整端口、数据目录、环境名称和日志级别。环境变量是最简单的配置入口。本包只放公开配置，例如 `APP_NAME`、`PORT`、`DATA_DIR`；秘密值不写入 Dockerfile、不写入博客、不写入 transcript。

## 学习目标

1. 用 `-e` 向容器传入环境变量。
2. 理解代码如何读取环境变量。
3. 区分公开配置和秘密配置。
4. 检查 `/config` 输出是否只包含安全信息。

## 先修知识

需要知道环境变量是进程启动时可读取的键值对。

## 核心模型

![容器配置从环境变量开始：APP_NAME、PORT 和秘密边界](/assets/diagrams/container-env-config-secrets-boundary.svg)

镜像提供默认配置，运行命令提供部署时配置。应用启动后读取环境变量，并把它们转成端口、目录和显示名称等运行参数。公开配置可以出现在日志中，秘密值需要专门的 secret 管理。

## 为什么需要配置和秘密边界

同一个 image 可能要在开发、测试和生产环境中运行。镜像里的代码相同，但端口、应用名称、数据目录、日志级别等运行参数会变化。把这些值写死在源码或 Dockerfile 里，会导致每换一个环境就重新构建 image。环境变量解决的核心问题是让运行时参数独立于应用代码。

公开配置和秘密值必须分开。`APP_NAME`、`PORT`、`DATA_DIR` 这类信息可以出现在命令、日志和教学报告里；数据库密码、API token、私钥和会话凭据不应该写进 Dockerfile、Compose、博客正文或 transcript。容器让配置更方便，也会让错误配置更容易被复制传播。

本 lab 的 `/config` 只返回公开配置，并用一句说明提醒 secrets 不会被打印。这个接口的教学用途是让学习者验证环境变量确实影响了容器进程，同时保持内部状态和秘密值边界清楚。

## 可信资料的关键结论

- Docker 运行容器时可以设置环境变量，适合传入部署配置。
- 官方 Compose 示例也大量使用 `environment` 描述服务配置。
- 秘密值需要独立管理；教学文章和公开仓库只保留公开安全配置。

## 逐步实现

服务端读取配置：

```python
def data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", "/data"))

def app_name() -> str:
    return os.environ.get("APP_NAME", "container-lab")
```

运行容器时传入：

```bash
-e APP_NAME=container-lab \
-e DATA_DIR=/data
```

公开配置接口只返回安全信息：

```json
{
  "app_name": "container-lab",
  "version": "1.0.0",
  "data_dir": "/data",
  "container_note": "configuration is provided through environment variables; secrets are not printed"
}
```

这里故意没有密码、token 或会话凭据。部署教学可以展示公开配置，但不能把秘密值写入文章、脚本或报告。

## 输出怎么读

运行命令传入：

```bash
-e APP_NAME=container-lab -e DATA_DIR=/data
```

随后 `/health` 和 `/config` 会反映这些公开配置：

```json
{
  "app_name": "container-lab",
  "data_dir": "/data",
  "container_note": "configuration is provided through environment variables; secrets are not printed"
}
```

`app_name` 说明进程读取到了 `APP_NAME`。`data_dir=/data` 说明容器内状态目录由环境变量决定，并且和挂载目标一致。`container_note` 是边界提示：可以展示公开配置，不能把秘密值打印出来。若你修改 `APP_NAME` 后输出没有变化，先确认容器已经重建或重启，而不是访问了旧容器。

## 常见错误

1. **把密码写进 Dockerfile。** 镜像层和仓库历史可能长期保存它。
2. **把 `.env` 放入构建上下文。** 本包 `.dockerignore` 明确排除 `.env`。
3. **把所有环境变量都打印到日志。** 日志也可能被上传或分享。
4. **把配置变化和代码变化混在一起。** 运行时配置应由部署命令或 Compose 管理。

## 练习或延伸

1. 把 `APP_NAME` 改成 `local-deploy-demo`，访问 `/health`。
2. 新增一个公开变量 `LOG_LEVEL`，只允许输出 `debug/info/warn`。
3. 设计一个秘密值的占位方案，但不要在文件中写真实秘密。

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
