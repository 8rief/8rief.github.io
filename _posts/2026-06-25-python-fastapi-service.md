---
layout: post
title: "FastAPI：把 Python 逻辑发布成一个本地 HTTP API"
date: 2026-06-25 16:36:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "复用文件扫描核心逻辑，创建 FastAPI /health 和 /manifest 接口，并用路径边界控制本地服务风险。"
tags: [python, fastapi, http-api, service, path-boundary]
---
{% raw %}


> 主题：Python 从0到可运行项目 / FastAPI / 本地服务 / 路径边界  
> 本文 lab 使用进程内 TestClient 验证 `/health` 和 `/manifest`，没有开放公网服务。

当核心逻辑已经能被 CLI 调用后，下一步可以把它发布成 HTTP API。API 的价值在于让其他程序通过网络协议调用同一份能力。风险也随之出现：路径参数从用户请求进入服务，如果边界没管住，本地目录结构可能被暴露。本文只做本地 API，并把路径限制在配置根目录内。

## 学习目标

1. 用 `FastAPI()` 创建应用。
2. 定义 `/health` 和 `/manifest` 两个接口。
3. 复用 `build_manifest()`，避免 API 里重写业务逻辑。
4. 用 `relative_to()` 检查路径没有逃出配置根目录。
5. 用 TestClient 做本地验证。

## 先修知识

需要理解 HTTP GET、查询参数和 JSON 响应。本文沿用前几讲的文件扫描项目。

## 核心模型

API 层把 HTTP 请求转换成核心函数调用，再把领域对象转换成 JSON 响应。

![FastAPI 服务边界](/assets/diagrams/python-fastapi-service.svg)

路径边界是这张图的关键节点。`subpath` 只能指向配置根目录内部，不能让请求者读取任意本机路径。

## 创建应用

示例项目使用工厂函数创建应用，测试时可以传入临时目录：

```python
def create_app(base_dir: Path | str | None = None) -> FastAPI:
    config = AppConfig.from_env()
    base = Path(base_dir).expanduser().resolve() if base_dir is not None else config.evidence_root
    app = FastAPI(title="Local Evidence Kit", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

工厂函数比全局应用更适合测试：测试可以创建指向临时目录的 app，真实运行可以从环境变量读取配置。

## 控制路径边界

`/manifest` 接口接受 `subpath`：

```python
def _resolve_inside(base: Path, subpath: str) -> Path:
    candidate = (base / subpath).expanduser().resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="path escapes configured evidence root") from exc
    return candidate
```

`resolve()` 会规整 `..` 等路径片段，`relative_to(base)` 检查 candidate 是否仍在 base 内。失败时返回 HTTP 400。

接口主体保持很薄：

```python
@app.get("/manifest")
def manifest(subpath: str = Query(".", description="Directory under the configured evidence root")) -> dict:
    target = _resolve_inside(base, subpath)
    try:
        return build_manifest(target).to_dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ScanBoundaryError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

## 本地验证

lab smoke test 输出：

```text
api /health -> {'status': 'ok'}
api /manifest sample_data -> {'file_count': 3, 'total_bytes': 119}
```

对应测试还检查了路径逃逸：

```python
escape = client.get("/manifest", params={"subpath": "../"})
assert escape.status_code == 400
```

这条测试很重要。它证明 API 不只是能返回正确结果，也能拒绝危险输入。

## 常见错误

1. **在路由函数里重写扫描逻辑。** API 应复用核心模块，避免 CLI 和 API 行为分叉。
2. **直接拼接用户路径。** HTTP 参数进入文件系统前必须经过边界检查。
3. **只测 `/health`。** 健康检查只能证明服务活着，不能证明业务接口正确。
4. **默认开放到外部网络。** 教学阶段优先绑定本机地址；真正部署前再设计认证、限流、日志和反向代理。

## 练习

1. 添加 `/summary` 接口，只返回 `file_count` 和 `total_bytes`。
2. 给不存在目录添加测试，确认返回 HTTP 404。
3. 在本机执行 `uvicorn local_evidence.api:app --host 127.0.0.1 --port 18080`，再用 curl 访问 `/health`。

## 参考资料

- FastAPI 文档：[First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/)
- FastAPI 文档：[Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- FastAPI 文档：[Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- Python 文档：[pathlib.PurePath.relative_to](https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.relative_to)


{% endraw %}
