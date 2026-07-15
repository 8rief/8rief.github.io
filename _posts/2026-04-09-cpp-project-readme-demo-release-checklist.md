---
layout: post
title: "C++ 项目收尾：README、demo transcript 和公开发布门禁"
date: 2026-04-09 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, readme, release, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/cpp-file-indexer-service/README.md`](/assets/labs/cpp-file-indexer-service/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

## 学习目标

这一篇做 C++ 项目化包的收尾。读完以后，你应该能判断一个 C++ 教学项目是否可以展示：

1. README 说明项目、运行方式、输出和实验边界；
2. transcript 证明配置、构建、测试、CLI 和 API 全链路跑通；
3. 发布前检查排除内部路径、临时标记、未来日期和 Jekyll 生成页问题。

## 先修知识

需要知道 C++ 项目的可复现性来自构建图、测试、运行脚本和输出证据，不只来自源代码本身。

## 为什么需要发布检查清单

一个项目能在本机运行，不等于已经适合公开展示。读者看不到你的终端历史，也不知道依赖是否下载成功、测试是否真的跑过、API 是否只是写在 README 里。发布检查清单把这些口头承诺转换成可复查证据。

C++ 项目尤其需要这一步，因为失败点分散在编译器、CMake 版本、Ninja、第三方库、链接、运行时路径和网络端口。README 负责告诉读者怎么复现；transcript 负责证明作者已经按这条路线跑过；发布门禁负责排除不该公开的路径、凭据和生成痕迹。

清单不是形式化收尾。它把“能展示”的含义具体化：有入口、有输出、有测试、有边界、有线上页面。


## 核心模型

C++ 项目收尾是一条证据链。

![C++ 项目收尾证据链](/assets/diagrams/cpp-project-readme-demo-release-checklist.svg)

从 `CMakeLists.txt` 到 FetchContent，再到 build、CTest、CLI、API、README 和博客检查，每一环都要留下可复查输出。

## 逐步实现

复现入口：

```bash
./run_lab.sh
```

脚本执行：

```text
== configure ==
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
== build ==
cmake --build build
== tests ==
ctest --test-dir build --output-on-failure
== CLI scan ==
files=3 bytes=304 lines=7 words=45
== API smoke ==
/health 200
/api/summary 200
/api/files 200
```

README 至少回答：

```text
1. 项目是什么：本地文件索引 CLI + HTTP API。
2. 怎么运行：./run_lab.sh。
3. 产物是什么：index.json、index.csv、file-indexer.log、transcript.txt。
4. 边界是什么：默认只扫描 sample_data/docs，只监听 127.0.0.1。
```

公开博客发布前还要检查：

```bash
grep -RInE '内部任务笔记|本机绝对路径|凭据|生成痕迹' _posts assets
python3 check_frontmatter.py
python3 parse_svg.py
docker run ... jekyll build
curl -L -sS -o /dev/null -w '%{http_code}' live_url
```

同一天发布文章时，front matter 时间必须早于实际构建时间；本地 Jekyll build 后还要检查 `_site` 里是否真的生成了 HTML 页面。

## 输出怎么读

`reports/transcript.txt` 应该形成一条连续证据链：

```text
== configure ==
== build ==
== tests ==
100% tests passed, 0 tests failed out of 3
== CLI scan ==
files=3 bytes=304 lines=7 words=45
== API smoke ==
/health 200
/api/summary 200
/api/files 200
```

读 transcript 时不要只看最后一行。`configure` 证明依赖版本和构建图生成；`build` 证明目标完成编译链接；`tests` 证明核心行为被回归验证；`CLI scan` 证明命令行入口写出报告；`API smoke` 证明服务入口能读同一份结果。

发布博客时还要读线上证据：页面返回 HTTP 200，并且包含本批文章的新内容 token。GitHub Pages 的构建状态有时会滞后，所以最终以成功的 Pages run、Pages REST `built` 状态和 live token 三者组合判断。

如果清单中某一步失败，就不要把后面的成功当成整体成功。比如 Jekyll build 成功但 `_site` 没生成对应 HTML，说明 front matter 或日期有问题。


## 常见错误

1. **只说“CMake 构建通过”**：还要证明测试、CLI 和 API 都在同一构建结果上运行。
2. **把下载依赖的细节藏起来**：C++ 第三方库解析常常是失败点，应进入 transcript。
3. **把实验目录当作公开仓库路径写进文章**：公开文章使用相对路径和命令，不暴露本机工作区。

## 练习或延伸

- 给项目补一个 `Release` 构建 transcript，比较 Debug 和 Release 的输出是否一致。
- 增加 GitHub Actions workflow，运行 configure、build、CTest，但把本地 API smoke 放在 job 内部。

## 参考资料

- [CMake build tool mode](https://cmake.org/cmake/help/latest/manual/cmake.1.html#build-tool-mode)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
- [Ninja manual](https://ninja-build.org/manual.html)
