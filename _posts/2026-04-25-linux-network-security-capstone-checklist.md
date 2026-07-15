---
layout: post
title: "结课项目：本地服务地图、路径边界和加固报告"
date: 2026-04-25 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "把 Linux 网络与授权安全基础包收束成可复跑 lab：service map、curl transcript、path evidence 和 hardening report。"
tags: [linux, networking, security, capstone, checklist]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/linux-network-security-basics/README.md`](/assets/labs/linux-network-security-basics/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

> 主题：Linux 网络与授权安全基础 / 结课项目
> 本文收束本包的本地 lab 和验收清单。所有命令只面向本机 `127.0.0.1` 和 lab 创建的文件。把这些命令用于未授权目标没有学习价值，也会破坏实验边界。

结课项目的目标是把网络观察、HTTP 调试和防御性边界写成一组可复跑证据。最终交付不只是一段服务代码，还包括 transcript、service map、curl verbose trace、路径边界证据、命令边界证据和 hardening report。

## 为什么需要证据包

单独运行过一个命令，只能说明当时的终端出现过某个结果。证据包把环境、命令、机器可读报告和回归测试放在一起：读者能从结论追回原始观察，修改代码后也能复跑同一验收路径。

这个项目的主线是“先建立本地服务，再从不同观察面验证边界”。它没有追求工具数量；每份文件都回答一个不同问题。

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
Ran 12 tests
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

## 证据文件怎样对应问题

| 文件 | 事实来源 | 能支持的结论 |
|---|---|---|
| `transcript.txt` | `run_lab.sh` stdout/stderr | 环境、步骤顺序、12 个测试通过 |
| `ss_listening.txt` | 内核 socket 表 | 18480 在 loopback 监听 |
| `curl_health_verbose.txt` | curl 客户端 | TCP 建立、请求行、状态与 headers |
| `service_map.json` | 受限连接探测 | 三个本地端口中只有 18480 开放 |
| `path_boundary.json` | 两个本地端点 | unsafe 可越界，safe 拒绝同一输入 |
| `command_boundary.json` | 输入验证与 subprocess | 合法 loopback 被接受，元字符输入未执行 |
| `hardening_report.json` | 静态清单加运行 header 请求 | 声明控制项与当前响应头 |

表中的“事实来源”决定证据强度。比如 hardening 静态项是设计声明，405 和路径拒绝还要回到单元测试与对应报告；总览文件不会自动把声明升级为运行证明。

## 从零复跑与检查

运行前只需要 Python 3、curl、`ss` 和 `getent`。脚本清空并重建 `reports/`，启动服务后用 readiness loop 等待 `/health`，结束时通过 trap 回收服务进程。

可以用标准库检查 JSON 是否完整：

```bash
python3 -m json.tool reports/service_map.json >/dev/null
python3 -m json.tool reports/path_boundary.json >/dev/null
python3 -m json.tool reports/command_boundary.json >/dev/null
python3 -m json.tool reports/hardening_report.json >/dev/null
```

再检查四个稳定断言：

```bash
grep -F '127.0.0.1:18480' reports/ss_listening.txt
grep -F 'HTTP/1.0 200 OK' reports/curl_health_verbose.txt
grep -F '"open_ports": [' reports/service_map.json
grep -F '"safe_endpoint": {' reports/path_boundary.json
```

延迟、Date header 和临时客户端端口会变化，不应作为精确 golden value。稳定验收项是状态、地址范围、开放端口、拒绝原因和产物存在性。

## 验收清单

- 服务只绑定 `127.0.0.1`。
- `ss -ltn` 能看到 `18480` 监听。
- `curl -v` 保存了连接、请求和响应头。
- service map 只接受 loopback host，并限制端口数量。
- safe 文件端点拒绝越界路径。
- command boundary 拒绝非 IP literal 输入。
- hardening report 记录 bind address、method、headers、path boundary、subprocess boundary 和 service-map scope。
- README 给出唯一入口 `./run_lab.sh`。

源码回归测试还应覆盖：

- `::1` 通过真实 IPv6 socket 探测，防止接口声称支持 IPv6、实现却固定 `AF_INET`；
- POST 返回 405，并携带 `Allow: GET, HEAD`；
- 编码后的上级目录输入进入同一安全拒绝路径；
- 非 loopback 目标在任何 connect 发生前被拒绝。

## 当前边界

这个 lab 解释基础机制。它没有覆盖认证、TLS、真实 Web 框架、中间件、容器网络、日志平台和生产级扫描流程。后续如果继续扩展，应保持同样原则：先定义授权范围，再写可复跑证据。

Python `http.server` 官方文档明确不建议生产使用。结课通过表示“本地教学目标和回归断言成立”，不表示服务通过安全审计，也不表示这些 headers 能覆盖应用级授权。

## 常见错误

1. **只有代码没有证据。** 安全学习需要 transcript 和报告文件。
2. **只做漏洞演示。** 必须同时给出修复边界和测试。
3. **把工具跑到外部目标。** 本包只服务本地授权练习。
4. **不更新 README。** demo 入口和预期输出要让读者直接复跑。

## 练习或延伸

1. 给 hardening report 增加一列 `risk_if_missing`。
2. 把 service map 的 JSON 转成 Markdown 表格。
3. 增加一个只读日志端点，并为它写方法边界测试。
4. 故意移除 `Allow` header，确认测试失败，再恢复实现。

## 参考资料

- Linux man-pages：[ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html)
- Everything curl：[Verbose](https://ec.haxx.se/usingcurl/verbose/index.html)
- OWASP：[Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- Python 文档：[subprocess](https://docs.python.org/3/library/subprocess.html)
- Python 文档：[http.server 安全说明](https://docs.python.org/3/library/http.server.html#security-considerations)


{% endraw %}
