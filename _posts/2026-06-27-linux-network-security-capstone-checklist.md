---
layout: post
title: "结课项目：本地服务地图、路径边界和加固报告"
date: 2026-06-27 23:07:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 Linux 网络与授权安全基础包收束成可复跑 lab：service map、curl transcript、path evidence 和 hardening report。"
tags: [linux, networking, security, capstone, checklist]
---
{% raw %}

> 主题：Linux 网络与授权安全基础 / 结课项目
> 本文收束本包的本地 lab 和验收清单。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

结课项目的目标是把网络观察、HTTP 调试和防御性边界写成一组可复跑证据。最终交付不只是一段服务代码，还包括 transcript、service map、curl verbose trace、路径边界证据、命令边界证据和 hardening report。

## 学习目标

1. 复跑完整 lab 并理解每个报告文件。
2. 用 service map 和 `ss` 交叉确认监听端口。
3. 用 path boundary evidence 说明 unsafe 和 safe 的差异。
4. 写出本地服务的加固验收清单。

## 先修知识

需要完成前七篇，或至少理解 loopback、socket、HTTP headers、路径边界和 subprocess 输入校验。

## 核心模型

![Linux 网络安全基础结课证据链](/assets/diagrams/linux-network-security-capstone-checklist.svg)

结课证据链从本地服务开始，经过系统观察、客户端请求、边界测试和加固报告，最后形成 README/demo 可复跑入口。

## 逐步实现

完整运行：

```bash
./run_lab.sh
```

本地 transcript 的关键结果：

```text
Ran 11 tests
OK
open_ports = [18480]
unsafe_status = 200
safe_status = 400
```

生成的核心文件：

```text
reports/transcript.txt
reports/service_map.json
reports/curl_health_verbose.txt
reports/path_boundary.json
reports/command_boundary.json
reports/hardening_report.json
```

## 验收清单

- 服务只绑定 `127.0.0.1`。
- `ss -ltn` 能看到 `18480` 监听。
- `curl -v` 保存了连接、请求和响应头。
- service map 只接受 loopback host，并限制端口数量。
- safe 文件端点拒绝越界路径。
- command boundary 拒绝非 IP literal 输入。
- hardening report 记录 bind address、method、headers、path boundary、subprocess boundary 和 service-map scope。
- README 给出唯一入口 `./run_lab.sh`。

## 当前边界

这个 lab 解释基础机制。它没有覆盖认证、TLS、真实 Web 框架、中间件、容器网络、日志平台和生产级扫描流程。后续如果继续扩展，应保持同样原则：先定义授权范围，再写可复跑证据。

## 常见错误

1. **只有代码没有证据。** 安全学习需要 transcript 和报告文件。
2. **只做漏洞演示。** 必须同时给出修复边界和测试。
3. **把工具跑到外部目标。** 本包只服务本地授权练习。
4. **不更新 README。** demo 入口和预期输出要让读者直接复跑。

## 练习或延伸

1. 给 hardening report 增加一列 `risk_if_missing`。
2. 把 service map 的 JSON 转成 Markdown 表格。
3. 增加一个只读日志端点，并为它写方法边界测试。

## 参考资料

- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- Everything curl：[Verbose](https://ec.haxx.se/usingcurl/verbose/index.html)
- OWASP：[Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- Python 文档：[subprocess](https://docs.python.org/3/library/subprocess.html)


{% endraw %}
