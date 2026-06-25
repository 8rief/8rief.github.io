---
layout: post
title: "pytest：让 Python 项目能被定位、复跑和审计"
date: 2026-06-25 16:35:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 pytest 覆盖纯函数、文件边界、CLI、API 和 HTTP client，建立从脚本到项目的回归验证方式。"
tags: [python, pytest, testing, reproducibility, cli-test]
---
{% raw %}


> 主题：Python 从0到可运行项目 / pytest / 回归测试 / 可审计实验  
> 本文 lab 执行 `python -m pytest -q`，结果为 7 个用例全部通过。

能跑一次的项目还不够。代码会被改动，依赖会升级，输入会变复杂。测试的作用是把项目契约写成可复跑的检查：哪些行为必须保持，哪些边界必须报错，哪些输出必须稳定。pytest 的优势在于写法轻、fixture 丰富，适合从小项目开始建立验证习惯。

## 学习目标

1. 用 pytest 测纯逻辑和文件边界。
2. 用 `tmp_path` 创建隔离的临时目录。
3. 用 Typer `CliRunner` 测 CLI。
4. 用 FastAPI `TestClient` 测 API。
5. 用 httpx mock transport 测 HTTP client。

## 先修知识

需要理解断言、函数和异常。本文的测试都围绕前几讲的本地证据项目。

## 核心模型

一个小项目的测试不应只测“函数能不能运行”，而应覆盖每个边界：

![pytest 覆盖层次](/assets/diagrams/python-pytest-reproducible-tests.svg)

纯逻辑测试定位最快；文件测试验证输入输出；CLI/API/client 测试验证用户能触达的边界。

## 测纯逻辑和文件边界

扫描器测试使用 `tmp_path` 创建临时文件：

```python
def test_build_manifest_is_deterministic(tmp_path):
    (tmp_path / "b.txt").write_text("beta\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")

    manifest = build_manifest(tmp_path)

    assert [entry.path for entry in manifest.entries] == ["a.txt", "b.txt"]
    assert manifest.summary.file_count == 2
```

`tmp_path` 的好处是每个测试都有自己的目录，测试结束后由 pytest 管理清理。它避免测试依赖用户机器上的固定路径。

边界错误也应该测试：

```python
with pytest.raises(ScanBoundaryError):
    build_manifest(file_path)
```

这里验证的是项目输入契约：普通文件不能当作扫描目录。

## 测 CLI

Typer 提供 `CliRunner`：

```python
runner = CliRunner()
scan_result = runner.invoke(app, ["scan", str(data_dir), "--json", str(manifest_json), "--csv", str(manifest_csv)])
assert scan_result.exit_code == 0, scan_result.output
assert "files=1" in scan_result.output
```

测试 CLI 时要同时检查退出码、关键输出和副作用文件。这样才能确认用户真正执行命令时会得到预期结果。

## 测 API 和 HTTP client

FastAPI 的测试可以在进程内完成：

```python
client = TestClient(create_app(tmp_path))
response = client.get("/manifest", params={"subpath": "data"})
assert response.status_code == 200
assert response.json()["summary"] == {"file_count": 1, "total_bytes": 5}
```

HTTP client 则使用 mock transport：

```python
transport = httpx.MockTransport(lambda request: httpx.Response(500, json={"error": "boom"}))
with httpx.Client(transport=transport, base_url="http://local") as client:
    with pytest.raises(ServiceRequestError):
        fetch_json("http://local/manifest", client=client)
```

这类测试让网络边界可控：不用访问外部站点，也能验证错误处理。

## 执行结果

lab transcript 中的测试结果是：

```text
.......                                                                  [100%]
```

七个点对应七个通过的测试用例。这个输出很短，但它背后覆盖了扫描排序、文件导出、CLI、API、HTTP client 和错误边界。

## 常见错误

1. **只测 happy path。** 输入错误、HTTP 500、路径越界等边界更容易在真实环境出问题。
2. **测试依赖当前工作目录。** 使用 `tmp_path` 能让测试和本机目录解耦。
3. **断言实现细节。** 测试应检查行为契约，例如输出文件存在、摘要正确、错误类型正确。
4. **把 smoke test 当完整测试。** smoke test 证明主路径能跑，回归测试还要覆盖关键分支。

## 练习

1. 添加一个空目录测试，断言 `file_count == 0`。
2. 添加路径越界 API 测试，确认返回 HTTP 400。
3. 给 CLI 的失败路径加测试，例如传入不存在的目录。

## 参考资料

- pytest docs source：[Get Started](https://github.com/pytest-dev/pytest/blob/main/doc/en/getting-started.rst)
- pytest docs source：[Temporary directories and files](https://github.com/pytest-dev/pytest/blob/main/doc/en/how-to/tmp_path.rst)
- Typer 文档：[Testing](https://typer.tiangolo.com/tutorial/testing/)
- FastAPI 文档：[Testing](https://fastapi.tiangolo.com/tutorial/testing/)


{% endraw %}
