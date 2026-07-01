---
layout: post
title: "容器数据怎么留下来：bind mount、volume 和访问计数持久化"
date: 2026-07-01 20:06:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用访问计数文件理解容器可删除、数据要外置的部署原则。"
tags: [docker, storage, bind-mount, volume, teaching]
---
{% raw %}
> 主题：容器化与部署 / bind mount / persistence
> 本文 lab 已验证：重启容器后访问计数从 2 增长到 4，`data/runtime/state.json` 保留下来。

容器可以随时删除重建，业务数据不能跟着消失。这个区别是部署实践的基础。本包把访问计数写到容器内 `/data/state.json`，再用 bind mount 把宿主机目录挂到 `/data`。容器重启后，状态文件仍在宿主机目录中。

## 学习目标

1. 解释容器文件系统和持久化数据的区别。
2. 用 bind mount 保存 `state.json`。
3. 观察容器重启后访问计数仍然存在。
4. 知道 volume 和 bind mount 的适用差异。

## 先修知识

需要知道 JSON 文件可以保存状态。

## 核心模型

![容器数据怎么留下来：bind mount、volume 和访问计数持久化](/assets/diagrams/container-bind-mount-volume-persistence.svg)

容器自己的可写层跟随容器生命周期；持久数据应放到容器外部。bind mount 使用宿主机指定目录，volume 由 Docker 管理存储位置。教学 lab 用 bind mount，因为路径可见、容易检查。

## 可信资料的关键结论

- Docker 官方文档区分 bind mount 和 volume：bind mount 依赖宿主机路径，volume 由 Docker 管理。
- 持久化数据应脱离可替换的容器实例。
- 教学项目选择 bind mount 的原因是可观察性强，学习者能直接打开状态文件。

## 逐步实现

运行命令里的挂载参数：

```bash
-v "$PWD/data/runtime:/data"
```

服务把状态写到：

```python
def state_path(root=None):
    return (root or data_dir()) / "state.json"
```

lab 第一次 smoke 访问两次：

```text
visits_after_smoke=2
```

停止并重新启动容器后，再访问两次：

```text
visits_after_smoke=4
state_ready=data/runtime/state.json
```

`reports/summary.json` 中固定了验收指标：

```json
{
  "visits_after_first_smoke": 2,
  "visits_after_restart": 4,
  "state_file_exists": true
}
```

## 常见错误

1. **把数据库或上传文件只写在容器可写层。** 容器删除后数据会丢失。
2. **在文章里直接推荐复杂存储系统。** 初学阶段先用可见目录理解边界。
3. **把 bind mount 路径写成机器相关绝对路径放进公开文章。** 文章用项目相对路径说明即可。
4. **忘记检查重启后的数据。** 持久化要靠重启实验验证。

## 练习或延伸

1. 删除 `data/runtime/state.json` 后重新运行 lab，观察计数从 0 开始。
2. 把 bind mount 换成 Docker volume，比较宿主机可见性。
3. 把 `state.json` 扩展为最近 20 次访问标签列表。

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
