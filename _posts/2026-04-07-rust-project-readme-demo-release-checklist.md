---
layout: post
title: "Rust 项目收尾：README、demo transcript 和公开发布检查"
date: 2026-04-07 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [rust, readme, release, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/rust-log-insight-cli/README.md`](/assets/labs/rust-log-insight-cli/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

## 学习目标

这一篇做 Rust 包的项目收尾。读完以后，你应该能判断一个 Rust 教学项目是否达到了可展示标准：

1. README 能说明运行方式、输出产物和边界；
2. demo transcript 能证明命令确实跑过；
3. 发布前检查能排除内部路径、临时标记、未来日期和 Jekyll 构建问题。

## 先修知识

需要知道 README 是入口说明，transcript 是执行证据，测试报告是质量证据。三者合起来才能支撑公开教程。

## 核心模型

项目收尾是一条证据链。

![Rust 项目收尾证据链](/assets/diagrams/rust-project-readme-demo-release-checklist.svg)

源码通过测试和 clippy 后，CLI 生成 JSON/CSV，API 通过本地 smoke，README 说明如何复现，博客文章只发布公共安全的片段。

## 为什么需要发布检查清单

一个 Rust 教学项目如果只给源码，读者仍然不知道怎么运行、会看到什么、失败时怎么定位。README、demo transcript、测试输出和公开发布检查共同解决的是可展示性问题：别人能按步骤复现，文章也不泄露本地路径或内部过程。

发布检查清单还把证据分层。`cargo test` 和 `clippy` 证明代码质量，CLI/API smoke 证明用户入口，JSON/CSV 证明可见结果，Jekyll build 和 live token 证明博客页面真的上线。任何一层缺失，公开教程都不完整。

这篇收尾文章的边界是本地教学项目，不声称它已经是生产服务。生产化还需要配置管理、认证、限流、日志采集、发布流水线和运维监控。

## 逐步实现

本项目的复现入口是：

```bash
./run_lab.sh
```

它执行完整门禁：

```text
== format ==
cargo fmt -- --check
== tests ==
cargo test
== clippy ==
cargo clippy --all-targets -- -D warnings
== build ==
cargo build
== CLI summarize ==
summary written total=6 errors=2 warnings=1 slow_events=1
== API smoke ==
/health 200
/api/summary 200
/api/events 200
```

README 至少回答四个问题：

```text
1. 这是什么：一个本地日志洞察 CLI + API。
2. 怎么跑：./run_lab.sh。
3. 会生成什么：summary.json、events.csv、transcript.txt。
4. 边界是什么：样例数据是合成的，API 默认绑定 127.0.0.1。
```

公开博客发布前还要检查：

```bash
grep -RInE '内部任务笔记|本机绝对路径|凭据|生成痕迹' _posts assets
python3 check_frontmatter.py
docker run ... jekyll build
curl -I 'https://<your-domain>/<column>/<yyyy>/<mm>/<dd>/<slug>.html'
```

实际执行时不要依赖“构建命令退出 0”这一条证据。Jekyll 同一天文章如果 front matter 时间晚于当前时间，构建可以成功但页面不会生成；因此还要检查 `_site/...html` 文件确实存在。

## 输出怎么读

完整 transcript 的核心顺序是：

```text
== format ==
== tests ==
== clippy ==
== build ==
== CLI summarize ==
== start local API ==
== API smoke ==
== help ==
== done ==
```

前四步是代码门禁，中间两步是功能演示，`help` 是用户入口检查，`done` 表示脚本顺利结束。报告产物包括 `reports/summary.json`、`reports/events.csv`、`reports/api-server.log` 和 `reports/transcript.txt`。

公开博客只摘取必要输出，不应该包含本机绝对路径、私有 token、任务笔记或临时调试内容。若 Jekyll 构建成功，还要继续检查生成 HTML 和线上 URL token，防止页面没有真正发布。

## 常见错误

1. **只提交源码，不提交复现说明**：读者不知道从哪里开始，也不知道预期输出是什么。
2. **只保留成功摘要，不保留 transcript**：摘要能说明结果，transcript 才能说明路径。
3. **公开文章出现本机路径或内部笔记**：这会破坏公开可读性，也可能泄露工作区结构。

## 练习或延伸

- 给 README 增加一张输出示例表，让读者不运行也能知道工具形态。
- 给项目增加 GitHub Actions workflow，只跑 `cargo fmt --check`、`cargo test` 和 `cargo clippy`。

## 参考资料

- [Cargo package metadata](https://doc.rust-lang.org/cargo/reference/manifest.html)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [GitHub Pages documentation](https://docs.github.com/en/pages)
