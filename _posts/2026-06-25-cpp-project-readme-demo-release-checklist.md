---
layout: post
title: "C++ 项目收尾：README、demo transcript 和公开发布门禁"
date: 2026-06-25 21:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [cpp, readme, release, teaching]
---

## 学习目标

这一篇做 C++ 项目化包的收尾。读完以后，你应该能判断一个 C++ 教学项目是否可以展示：

1. README 说明项目、运行方式、输出和实验边界；
2. transcript 证明配置、构建、测试、CLI 和 API 全链路跑通；
3. 发布前检查排除内部路径、临时标记、未来日期和 Jekyll 生成页问题。

## 先修知识

需要知道 C++ 项目的可复现性来自构建图、测试、运行脚本和输出证据，不只来自源代码本身。

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
