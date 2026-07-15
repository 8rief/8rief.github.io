---
layout: page
title: 计算机技术教学
permalink: /computer-science-teaching/
---

这里把计算机概念、系统和编程主题整理成可执行的学习目录。每条路线都保留起点、收尾项目和资料入口，便于按表查找和回看。

## 可以学什么

- 编程语言与工程实践：Python、C/C++、Shell、Git、测试、调试、构建系统。
- 计算机系统：操作系统、网络、数据库、编译、分布式系统、性能分析。
- 工程系统边界：HTTP/API、登录会话、迁移、后台任务、重试、幂等、日志和指标。
- 本地 AI 与 GPU 工程：baseline、PyTorch、CUDA、硬件瓶颈、LoRA/RAG 和 Agent 评测。
- 证据判断：源码、实验、复现脚本、图表和结论边界。
- 交叉安全导读：用有限文章建立具身智能安全、抗量子密码和真实系统边界的基本概念。

阅读时按表格顺序查找对应路线即可。表格保留学习入口、收尾项目和资料连接。


## 建议学习路径

下面的路径按学习目标和先修关系组织。底部“已归入本栏目”保留全量索引。

### 基础工具与系统

| 顺序 | 发布包 | 从哪里开始 | 收尾项目 | 适合解决的问题 |
| --- | --- | --- | --- | --- |
| 0 | 本地帮助与文档阅读 | [Linux 本地帮助：从 --help、man 到可复现 transcript](/computer-science-teaching/2026/03/16/linux-local-docs-help-man-version-transcript.html) | 同一篇文章生成 `doc_probe.json` 和 `transcript.md` | 学会用本机版本、帮助、manual page 和模块文档建立可复现证据 |
| 1 | 软件包、PATH 与命令定位 | [Linux 软件包、PATH 和可执行文件定位：命令到底从哪里来](/computer-science-teaching/2026/03/16/linux-path-package-command-resolution.html) | 同一篇文章生成 `package_path_probe.json` 和 `transcript.md` | 解释命令名如何解析到真实可执行文件、权限和软件包版本 |
| 2 | 环境变量与项目环境隔离 | [Linux 环境变量、profile 和项目环境隔离：为什么换个 shell 配置就变了](/computer-science-teaching/2026/03/17/linux-env-profile-project-isolation.html) | 同一篇文章生成 `env_profile_probe.json` 和 `transcript.md` | 解释 export、env -i、.bashrc/profile、BASH_ENV、项目 env.sh 和 subshell 边界 |
| 3 | 脚本参数、退出状态与错误处理 | [Linux 脚本参数、退出状态和错误处理：让 run fail 可以定位](/computer-science-teaching/2026/03/17/linux-script-args-exit-error-handling.html) | 同一篇文章生成 `script_error_probe.json`、`transcript.md` 和 `error_handling_summary.md` | 解释 "$@"、shift、exit status、set -euo pipefail、if command、trap cleanup、usage/exit code |
| 4 | 项目配置与日志边界 | [项目配置文件与日志边界：让开发、测试和发布环境都可解释](/computer-science-teaching/2026/03/18/project-config-files-logging-boundary.html) | 同一篇文章生成 `resolved_config.json`、`events.jsonl`、probe 报告和 transcript | defaults/file/env/CLI 优先级、schema 校验、secret 边界、dry-run、JSONL 日志和 run_id |
| 5 | 项目数据与原子发布 | [项目数据目录、临时文件与原子写入：怎样让失败重跑不破坏结果](/computer-science-teaching/2026/03/18/project-data-temp-atomic-write-boundary.html) | 同一篇文章生成 `data_boundary_probe.json`、artifact manifest 和失败/重跑 transcript | source/config/input/cache/temp/output 边界、same-directory temp、fsync、os.replace、幂等重跑和哈希证据 |
| 6 | 项目锁与版本冲突 | [项目锁、并发写入与版本冲突：原子替换为什么仍会丢更新](/computer-science-teaching/2026/03/19/project-lock-concurrent-write-version-conflict.html) | 同一篇文章生成真实子进程竞争报告、冲突摘要和 transcript | lost update、稳定锁文件、flock、完整临界区、expected_version、冲突重试和有界超时 |
| 7 | 项目重试与幂等副作用 | [项目重试、幂等键与副作用边界：为什么失败后不能只再跑一次](/computer-science-teaching/2026/03/19/project-retry-idempotency-side-effect-boundary.html) | 同一篇文章生成重试/幂等/outbox/副作用去重报告和 transcript | retry、idempotency key、request fingerprint、transactional outbox、stable event_id、receiver dedupe、transient/permanent error |
| 8 | 项目后台任务与队列可观测性 | [项目后台任务、队列与可观测性边界：worker 崩溃后任务怎么恢复](/computer-science-teaching/2026/03/20/project-background-jobs-queue-observability-boundary.html) | 同一篇文章生成 queue probe、JSONL 事件和 status report | atomic lease、visibility timeout、heartbeat、available_at、retry、dead-letter、JSONL observability |
| 9 | 项目服务生命周期与优雅关闭 | [项目服务启动、健康检查与优雅关闭边界：进程收到 SIGTERM 后怎么不丢请求](/computer-science-teaching/2026/03/20/project-service-startup-health-graceful-shutdown-boundary.html) | 同一篇文章生成 service lifecycle probe、JSONL 生命周期事件和 status report | liveness、readiness、status、SIGTERM、graceful drain、grace timeout、PID/port state file、structured lifecycle logs |
| 10 | 项目运行时指标与最小报警 | [项目运行时指标、日志聚合与最小报警边界：什么时候该叫醒人](/computer-science-teaching/2026/03/21/project-runtime-metrics-log-aggregation-alert-boundary.html) | 同一篇文章生成 runtime events、metrics、alerts 和 report | JSONL logs、request counters、status family、latency buckets、p50/p90、error rate、slow rate、sample-size suppression、alert rules |
| 10a | 项目测试金字塔与回归边界 | [项目测试金字塔与回归用例边界：失败应该由哪一层测试抓住](/computer-science-teaching/2026/03/21/project-test-pyramid-regression-boundary.html) | 同一篇文章生成 unit/integration/smoke/golden regression 证据 | unit、integration、smoke、golden fixture、错误退出码、失败不写半成品和最小回归用例选择 |
| 10b | 项目 HTTP/API 契约边界 | [项目 HTTP/API 契约第一课：method、status、JSON 和幂等边界怎么定](/computer-science-teaching/2026/03/22/project-http-api-contract-boundary.html) | 同一篇文章生成 HTTP contract probe、JSONL 事件和报告 | method、path、status code、JSON body、错误结构、Location、request id、Idempotency-Key 和重复请求行为 |
| 10c | 项目登录、Cookie 与会话边界 | [项目登录、Cookie 与会话边界：用户状态怎么变成可测试证据](/computer-science-teaching/2026/03/22/project-session-auth-cookie-boundary.html) | 同一篇文章生成登录、Cookie、CSRF、角色、logout 和 expiry 证据 | password verifier、Set-Cookie、server-side session、CSRF token、role check、session revocation 和 expiry |
| 10d | 数据库迁移与 schema 演化 | [数据库迁移与 schema 演化：expand、backfill、约束和 rollback 怎么做成证据](/computer-science-teaching/2026/03/23/project-database-migration-schema-evolution.html) | 同一篇文章生成迁移、回滚、重复数据 preflight 和 schema 报告 | schema_migrations、checksum、PRAGMA user_version、expand/backfill/constraint、旧查询兼容、rollback 边界和数据修复脚本 |
| 11 | Git 基础与协作 | [Git 心智模型：working tree、index、commit 和 repository](/computer-science-teaching/2026/03/23/git-working-tree-index-commit.html) | [Git repo lab、release tag 和协作检查表](/computer-science-teaching/2026/03/24/git-release-tag-gitignore-capstone.html) | 版本控制、协作、冲突解决和发布前检查 |
| 12 | OS/Linux 进程与文件 | [Linux 文件系统：路径、目录项、inode 和 stat 怎么连起来](/computer-science-teaching/2026/03/24/linux-filesystem-path-inode-stat.html) | [本地 system observer 报告](/computer-science-teaching/2026/03/25/linux-system-observer-capstone.html) | 文件、进程、权限、信号、文本流水线 |
| 13 | 计算机系统与操作系统基础 | [数据表示第一课：bytes、整数宽度和 endian](/computer-science-teaching/2026/03/25/systems-data-representation-bytes-endian.html) | [用 locality 测量生成系统证据报告](/computer-science-teaching/2026/03/26/systems-cache-locality-capstone-report.html) | bytes、内存布局、进程/系统调用、fd/pipe、虚拟内存、线程同步、signal/IPC、cache locality |
| 13a | 硬件瓶颈地图 | [硬件瓶颈地图：从 CPU cache、内存带宽、PCIe 到 GPU occupancy](/computer-science-teaching/2026/03/26/hardware-bottleneck-map-cpu-memory-gpu.html) | 同一篇文章连接系统基础实验和 CUDA 实验 | compute-bound、memory-bound、latency-bound、communication-bound、capacity-bound、cache locality、host/device transfer、occupancy 和本地 AI 显存预算 |
| 13b | 硬件瓶颈实测 | [硬件瓶颈实测第一课：cache、branch、PCIe 和 CUDA timing 怎么一步步看](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html) | 同一篇文章生成 CPU cache/stride/branch 报告，可选 CUDA transfer/timing 报告 | row-major/column-major、stride、cache line、branch predictability、pageable/pinned copy、CUDA event timing 和本地模型瓶颈拆层 |
| 14 | Linux CLI 与 Shell 自动化 | [工作目录、命令和输出边界](/computer-science-teaching/2026/03/27/linux-cli-workspace-command-contract.html) | [本地日志报告自动化](/computer-science-teaching/2026/03/28/linux-shell-automation-capstone-log-report.html) | 管道、变量引用、脚本参数、find 批处理、awk/sed 报告、测试和 transcript |
| 15 | SQL 实用开发 | [SQLite schema 与表设计](/computer-science-teaching/2026/03/28/sql-sqlite-schema-table-primary-key.html) | [SQLite 报表 CLI、索引证据和发布检查](/computer-science-teaching/2026/03/29/sql-report-cli-index-explain-capstone.html) | 查询、增删改、JOIN、聚合、事务、参数化查询、导入导出 |
| 16 | 数据库与缓存开发实践 | [数据库从表结构开始](/computer-science-teaching/2026/03/29/db-cache-schema-migration-user-version.html) | [库存订单系统、报表缓存和 SVG 展示](/computer-science-teaching/2026/03/30/db-cache-capstone-inventory-report.html) | schema 迁移、参数化 CRUD、索引计划、事务下单、cache-aside、TTL、失效、测试和 transcript |
| 17 | 容器化与本地部署 | [容器第一课](/computer-science-teaching/2026/03/30/container-image-container-model.html) | [HTTP 服务容器化并留下部署证据](/computer-science-teaching/2026/03/31/container-deployment-capstone-release-evidence.html) | image/container、Dockerfile、build context、端口发布、环境变量、挂载、健康检查、Compose 和发布证据 |
| 18 | 调试与构建工具 | [编译告警和构建类型](/computer-science-teaching/2026/03/31/debug-build-warnings-build-types.html) | [调试和构建发布检查表](/computer-science-teaching/2026/04/01/debug-build-capstone-release-checklist.html) | warnings、CMake/Ninja、最小复现、sanitizer、CTest、日志、计时和符号证据 |
| 19 | 网络基础（非安全） | [网络栈基础：interface、route、socket 和 loopback 如何连起来](/computer-science-teaching/2026/04/01/network-stack-interface-route-socket.html) | [本地 network observer 报告](/computer-science-teaching/2026/04/02/network-observer-service-map-capstone.html) | interface、IP/CIDR、route、DNS、TCP、UDP、HTTP、timing 和服务观测 |
| 20 | 软件工程项目结构 | [需求切片：先把“要做一个项目”改写成可验收行为](/computer-science-teaching/2026/04/02/software-requirement-slice-contract.html) | [release-ready 小项目骨架](/computer-science-teaching/2026/04/03/software-project-skeleton-capstone.html) | 需求切片、目录结构、模块边界、配置、依赖、测试、文档和发布检查 |

### 从0到可运行项目

| 顺序 | 语言/方向 | 从哪里开始 | 收尾项目 | 重点 |
| --- | --- | --- | --- | --- |
| 1 | Python | [Python 环境和依赖管理](/computer-science-teaching/2026/04/03/python-environment-venv-packaging.html) | [Python 项目收尾](/computer-science-teaching/2026/04/04/python-project-structure-config-logging-readme.html) | venv、文件/JSON/CSV、Typer、pytest、FastAPI、配置和日志 |
| 2 | Java | [Java 工具链和 Maven 项目结构](/computer-science-teaching/2026/04/04/java-toolchain-maven-project-layout.html) | [Java 项目收尾](/computer-science-teaching/2026/04/05/java-project-packaging-readme-demo.html) | Maven、领域模型、JUnit、Jackson、Spring Boot、CLI/API demo |
| 3 | Go | [Go 工具链和 module](/computer-science-teaching/2026/04/05/go-toolchain-module-project-layout.html) | [Go 项目收尾](/computer-science-teaching/2026/04/06/go-project-tests-readme-demo.html) | module、error、JSON/CSV、net/http、context、goroutine、测试 |
| 4 | Rust | [Rust 工具链和 Cargo 项目结构](/computer-science-teaching/2026/04/06/rust-toolchain-cargo-project-layout.html) | [Rust 项目收尾](/computer-science-teaching/2026/04/07/rust-project-readme-demo-release-checklist.html) | Cargo、ownership、Result/Option、serde、clap、测试、Axum |
| 5 | C++ 基础工程 | [C++ 程序如何从源码变成可执行文件](/computer-science-teaching/2026/04/07/cpp-build-pipeline-source-to-executable.html) | [GoogleTest 和可复现实验](/computer-science-teaching/2026/04/08/cpp-googletest-reproducible-tests.html) | 编译链接、头文件、RAII、所有权、CMake、测试 |
| 6 | C++ 库项目 | [CMake FetchContent 和第三方库边界](/computer-science-teaching/2026/04/08/cpp-cmake-fetchcontent-library-boundary.html) | [C++ 项目收尾](/computer-science-teaching/2026/04/09/cpp-project-readme-demo-release-checklist.html) | CLI11、nlohmann/json、CSV、Catch2、spdlog、cpp-httplib |
| 7 | 最小 Web 全栈 | [浏览器、HTTP、服务器和 JSON 文件怎么连起来](/computer-science-teaching/2026/04/09/web-fullstack-request-response-boundary.html) | [从空目录跑起一个最小任务面板](/computer-science-teaching/2026/04/10/web-fullstack-capstone-task-board.html) | HTML 表单、DOM、fetch、Node HTTP、JSON 持久化、输入校验、Node test 和 smoke transcript |
| 8 | 数据处理与可视化 | [从 CSV 到报告的最小流水线](/computer-science-teaching/2026/04/10/data-pipeline-csv-to-report-model.html) | [销售数据报表和 SVG 图表](/computer-science-teaching/2026/04/11/data-processing-visualization-capstone.html) | CSV、字段校验、拒收行、JSON 摘要、SQLite 汇总、SVG 图表、测试和 transcript |
| 9 | 数据库与缓存开发实践 | [数据库从表结构开始](/computer-science-teaching/2026/03/29/db-cache-schema-migration-user-version.html) | [库存订单系统、报表缓存和 SVG 展示](/computer-science-teaching/2026/03/30/db-cache-capstone-inventory-report.html) | SQLite schema、CRUD、索引计划、事务、报表聚合、cache-aside、TTL、失效、测试和 transcript |
| 10 | 容器化与本地部署 | [容器第一课](/computer-science-teaching/2026/03/30/container-image-container-model.html) | [HTTP 服务容器化并留下部署证据](/computer-science-teaching/2026/03/31/container-deployment-capstone-release-evidence.html) | Dockerfile、image/container、端口发布、环境变量、bind mount、healthcheck、Compose、发布证据 |
| 11 | 深度学习/AI 工程入门 | [AI 工程从问题和 baseline 开始](/computer-science-teaching/2026/04/11/ai-engineering-problem-data-baseline-split.html) | [从 baseline 到 NumPy MLP 的可复现 AI 工程包](/computer-science-teaching/2026/04/12/ai-engineering-capstone-numpy-mlp-release.html) | 数据切分、baseline、NumPy 张量、softmax、反向传播、gradient check、训练循环、评估、checkpoint、model card |
| 12 | 深度学习 CNN 机制 | [CNN 第一课：卷积、padding、stride 和 pooling 为什么能识别平移后的形状](/computer-science-teaching/2026/04/12/deep-learning-cnn-convolution-pooling-from-scratch.html) | 同一篇文章生成纯 Python CNN 机制报告 | 卷积窗口、padding/stride、ReLU、max pooling、global max、raw template baseline 和平移泛化边界 |
| 13 | 深度学习 RNN 机制 | [RNN 第一课：hidden state 为什么能把开头信息带到最后](/computer-science-teaching/2026/04/13/deep-learning-rnn-hidden-state-sequence-memory.html) | 同一篇文章生成纯 Python hidden-state trace 报告 | 序列 delayed cue、hidden state、recurrent carry、last-token/suffix/no-recurrence baseline 和记忆边界 |
| 14 | 深度学习 LSTM/GRU gate 机制 | [LSTM/GRU 第一课：gate 为什么能控制写入和保留](/computer-science-teaching/2026/04/13/deep-learning-lstm-gru-gates-memory-control.html) | 同一篇文章生成纯 Python gate memory 报告 | delayed cue、suffix distractor、LSTM cell state、GRU update gate、vanilla RNN baseline 和门控记忆边界 |
| 15 | 深度学习 attention 机制 | [Attention 第一课：query、key、value 为什么能按需读取历史位置](/computer-science-teaching/2026/04/14/deep-learning-attention-key-value-lookup.html) | 同一篇文章生成纯 Python key-value attention 报告 | query/key/value、scaled dot-product、softmax weights、fixed-summary baseline 和按需读取边界 |
| 16 | Transformer position/mask 机制 | [Transformer 第一课：position 和 mask 怎样决定能看哪里](/computer-science-teaching/2026/04/14/deep-learning-transformer-position-mask.html) | 同一篇文章生成纯 Python position/mask 报告 | position key、order-sensitive baseline、causal mask、future leakage 和 mask 方向边界 |
| 17 | Transformer multi-head/block 机制 | [Transformer 第二课：multi-head 和 block 怎样把多种关系合在一起](/computer-science-teaching/2026/04/15/deep-learning-transformer-multi-head-block.html) | 同一篇文章生成纯 Python multi-head/block 报告 | 多头并行读取、单标量碰撞、residual、LayerNorm、FFN 和 block 信息流边界 |
| 18 | PyTorch Transformer encoder 项目 | [PyTorch Transformer encoder 项目：从 baseline 到训练、mask 和 checkpoint](/computer-science-teaching/2026/04/15/deep-learning-pytorch-transformer-encoder-project.html) | 同一篇文章生成 PyTorch 训练、评估、checkpoint 报告 | `nn.TransformerEncoderLayer`、padding mask、baseline、训练循环、eval/no_grad、checkpoint reload 和项目边界 |
| 19 | PyTorch 训练工程 | [PyTorch 训练工程第一课：config、验证集、checkpoint 和 resume 怎样留下证据](/computer-science-teaching/2026/04/16/deep-learning-pytorch-training-engineering.html) | 同一篇文章生成 config hash、JSONL 日志、checkpoint/resume、model card 和 artifact manifest | config、split、baseline、train/eval、no_grad、optimizer/scheduler state_dict、resume 对照和 reproducibility 边界 |
| 20 | PyTorch 文本分类项目 | [PyTorch 文本分类项目第一课：tokenize、vocab、collate 和 baseline 怎么串起来](/computer-science-teaching/2026/04/16/deep-learning-pytorch-text-classification.html) | 同一篇文章生成 vocab、padded batch、baseline、confusion matrix、checkpoint reload 证据 | tokenize、`<pad>/<unk>`、Dataset、DataLoader/collate_fn、mask-aware mean embedding、CrossEntropyLoss、baseline 和错误分析 |
| 21 | PyTorch 字符级语言模型项目 | [PyTorch 字符级语言模型第一课：next-character、GRU hidden state 和采样边界怎么连起来](/computer-science-teaching/2026/04/17/deep-learning-pytorch-char-lm.html) | 同一篇文章生成 shifted input/target、baseline、prompt next-character、checkpoint reload 证据 | character vocab、BOS/EOS/PAD、teacher forcing、GRU hidden state、CrossEntropyLoss(ignore_index)、bigram baseline 和采样边界 |
| 22 | PyTorch 推理工程边界 | [PyTorch 推理工程第一课：eval、inference_mode、batching 和 latency 边界怎么检查](/computer-science-teaching/2026/04/17/deep-learning-pytorch-inference-boundary.html) | 同一篇文章生成 eval/inference_mode、batch-vs-single、prediction table、timing 和 checkpoint reload 证据 | `model.eval()`、`torch.inference_mode()`、Dropout/BatchNorm 行为、batch 推理、latency 边界和 reload 一致性 |

### 本地小模型与 Agent 开发

| 顺序 | 学习主题 | 入口 | 实操结果 | 会建立的能力 |
| --- | --- | --- | --- | --- |
| 1 | 任务、baseline 和方法选择 | [本地小模型微调：先定义任务、baseline，再选择 LoRA 或 QLoRA](/computer-science-teaching/2026/04/18/local-llm-task-baseline-lora-qlora.html) | 一份任务规格、base/RAG/LoRA 对照和显存预算 | 不先被模型名称带着走，能从错误类型选方法 |
| 2 | 第一个可检查 Agent | [Agent 第一课：不用框架，先写可检查的控制循环](/computer-science-teaching/2026/04/18/local-rag-agent-tool-eval-loop.html) | Python 标准库实现的 RAG、工具白名单、有界状态和 trace | 理解 Agent 是控制系统，模型只是其中一层 |
| 3 | WSL 端到端复现 | [WSL 从零跑通本地 Agent：每条命令做了什么](/computer-science-teaching/2026/04/19/cuda-learner-runner-wsl-commands.html) | 8 个 CPU-first 步骤、8 个测试、Qwen 接入和 LoRA adapter | 会在 WSL 分层排查 Linux、driver、PyTorch、模型和评测 |
| 4 | 领域 Qwen LoRA + RAG | [领域小模型微调实战：用 Qwen3-0.6B、LoRA 和 RAG 做本地学习 Agent](/computer-science-teaching/2026/04/19/cuda-domain-qwen-lora-rag-agent-eval.html) | 固定 revision、response-only labels、rank-8 LoRA、base/LoRA/RAG+LoRA 对比 | 能解释 loss、生成、显存和 held-out 证据分别说明什么 |
| 5 | 失败驱动评测与优化 | [Agent 评测与优化：从 held-out 失败分类到检索缓存](/computer-science-teaching/2026/04/20/cuda-agent-quality-iteration-eval-cli.html) | 检索基线 8/10、改进 10/10、cache hit 计数和逐题失败 | 知道什么时候改 retrieval、schema、state、prompt、数据或模型 |

完整公开代码位于 [`assets/labs/local-small-model-agent-course/`](/assets/labs/local-small-model-agent-course/README.md)。RTX 5070 12GB 是本路线的实测平台；00--07 可在 CPU-only 环境学习，GPU 条件主要改变模型规模、长度、batch 和量化选择。

### GPU 与 CUDA 工程

| 顺序 | 发布包 | 从哪里开始 | 收尾项目 | 重点 |
| --- | --- | --- | --- | --- |
| 0 | 硬件瓶颈地图 | [硬件瓶颈地图：从 CPU cache、内存带宽、PCIe 到 GPU occupancy](/computer-science-teaching/2026/03/26/hardware-bottleneck-map-cpu-memory-gpu.html) | 系统基础实验 + CUDA 实验对照 | 先判断 compute/memory/latency/communication/capacity 边界，再决定是否改 kernel、batch、数据布局或模型规格 |
| 0a | 硬件瓶颈实测 | [硬件瓶颈实测第一课：cache、branch、PCIe 和 CUDA timing 怎么一步步看](/computer-science-teaching/2026/03/27/hardware-bottleneck-cache-branch-cuda-transfer-lab.html) | CPU 必跑实验 + 可选 CUDA transfer/timing | 用本机证据区分访问顺序、cache line 利用率、branch 行为、host/device copy 和 kernel 时间 |
| 1 | CUDA 与本地小模型工程总纲 | [CUDA 与本地小模型工程总纲：先从需求、瓶颈和证据开始](/computer-science-teaching/2026/04/20/cuda-local-ai-requirements-roadmap.html) | [CUDA 与本地小模型工程结课检查表](/computer-science-teaching/2026/04/21/cuda-local-ai-capstone-checklist.html) | 从需求、性能瓶颈、环境证据、硬件层级和可迁移边界出发；RTX 5070 是验证平台 |
| 2 | CUDA 基础 | [CUDA 第一个 kernel：vector add 背后的 host/device 边界](/computer-science-teaching/2026/04/21/cuda-host-device-vector-add.html) | [CUDA reduction、atomic 和 profiling：多个线程写同一个答案怎么办](/computer-science-teaching/2026/04/22/cuda-reduction-atomic-profiling.html) | host/device、thread/block/grid、SIMT、访存、reduction、atomic、profiling readiness |
| 3 | N-Queens GPU 搜索桥梁 | [N-Queens 从 bitmask DFS 到 GPU 子问题：为什么搜索要先切任务](/computer-science-teaching/2026/04/22/nqueens-bitmask-dfs-task-splitting.html) | [N-Queens GPU 桥梁：dynamic work fetching 和 shared-memory stack 为什么出现](/computer-science-teaching/2026/04/23/nqueens-dynamic-work-shared-stack.html) | 从状态压缩、预放行、负载不均衡到 dynamic work 和 shared-memory stack |
| 4 | PyTorch/CUDA 训练环境 | [CUDA/PyTorch 实机验收：从 driver、nvcc 到 LoRA 闭环](/computer-science-teaching/2026/04/23/cuda-pytorch-nvcc-lora-runtime-evidence.html) | 同左 | 用户态 toolkit、`sm_120` 编译、PyTorch CUDA、HF/PEFT 和 LoRA 最小训练闭环 |
| 5 | CUDA 与本地 AI 结课验收 | [CUDA 与本地小模型工程结课检查表](/computer-science-teaching/2026/04/21/cuda-local-ai-capstone-checklist.html) | 同左 | 将 kernel 正确性、N-Queens task splitting、PyTorch、LoRA、RAG 和评测分层验收 |


### 机制与实验基础

| 顺序 | 发布包 | 从哪里开始 | 收尾项目 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 深度学习基础 | [先把可复现实验跑起来](/computer-science-teaching/2026/04/24/deep-learning-route-reproducible-lab.html) | [从 XOR baseline 到 MLP 对比](/computer-science-teaching/2026/04/24/deep-learning-capstone-xor-mlp-comparison.html) | 先跑 baseline，再解释 tensor、autograd、loss、训练循环 |
| 2 | 深度学习/AI 工程入门 | [AI 工程从问题和 baseline 开始](/computer-science-teaching/2026/04/11/ai-engineering-problem-data-baseline-split.html) | [从 baseline 到 NumPy MLP 的可复现 AI 工程包](/computer-science-teaching/2026/04/12/ai-engineering-capstone-numpy-mlp-release.html) | CPU-only NumPy lab；baseline 对比、梯度检查、训练曲线、checkpoint、model card 和 transcript |
| 3 | CNN 机制基础 | [CNN 第一课：卷积、padding、stride 和 pooling 为什么能识别平移后的形状](/computer-science-teaching/2026/04/12/deep-learning-cnn-convolution-pooling-from-scratch.html) | 同一篇文章生成 majority/raw-template/conv-feature 对比报告 | 纯 Python 解释卷积窗口、权重共享、ReLU、pooling、global max，以及平移测试上的 baseline 差距 |
| 4 | RNN 机制基础 | [RNN 第一课：hidden state 为什么能把开头信息带到最后](/computer-science-teaching/2026/04/13/deep-learning-rnn-hidden-state-sequence-memory.html) | 同一篇文章生成 majority/last-token/suffix/no-recurrence/RNN 对比报告 | 纯 Python 解释 hidden state、recurrent carry、delayed cue 和序列记忆边界 |
| 5 | LSTM/GRU gate 机制 | [LSTM/GRU 第一课：gate 为什么能控制写入和保留](/computer-science-teaching/2026/04/13/deep-learning-lstm-gru-gates-memory-control.html) | 同一篇文章生成 majority/last-token/vanilla-RNN/LSTM/GRU 对比报告 | 纯 Python 解释 input/forget/output gate、GRU update gate、cell/hidden keep 和后缀干扰边界 |
| 6 | Attention key-value 机制 | [Attention 第一课：query、key、value 为什么能按需读取历史位置](/computer-science-teaching/2026/04/14/deep-learning-attention-key-value-lookup.html) | 同一篇文章生成 majority/last-value/bag/fixed-summary/attention 对比报告 | 纯 Python 解释 query-key score、softmax weight、value weighted sum 和 key-value binding 边界 |
| 7 | Transformer position/mask 机制 | [Transformer 第一课：position 和 mask 怎样决定能看哪里](/computer-science-teaching/2026/04/14/deep-learning-transformer-position-mask.html) | 同一篇文章生成 bag/no-position/position/unmasked/causal-mask 对比报告 | 纯 Python 解释 position encoding、order-sensitive task、future leakage、causal mask 和 PyTorch mask 方向 |
| 8 | Transformer multi-head/block 机制 | [Transformer 第二课：multi-head 和 block 怎样把多种关系合在一起](/computer-science-teaching/2026/04/15/deep-learning-transformer-multi-head-block.html) | 同一篇文章生成 single-head/multi-head/no-attention/no-residual/block 对比报告 | 纯 Python 解释多头读取、单标量信息碰撞、residual 保留本地信号、LayerNorm 尺度控制和 FFN 位置内组合 |
| 9 | PyTorch Transformer encoder 项目 | [PyTorch Transformer encoder 项目：从 baseline 到训练、mask 和 checkpoint](/computer-science-teaching/2026/04/15/deep-learning-pytorch-transformer-encoder-project.html) | 同一篇文章生成 PyTorch 训练、评估、checkpoint 报告 | 用真实 PyTorch 项目串起 embedding、position、encoder、padding mask、CrossEntropyLoss、AdamW、eval/no_grad 和 checkpoint reload |
| 10 | PyTorch 训练工程 | [PyTorch 训练工程第一课：config、验证集、checkpoint 和 resume 怎样留下证据](/computer-science-teaching/2026/04/16/deep-learning-pytorch-training-engineering.html) | 同一篇文章生成 config、validation、checkpoint/resume、model card 和 manifest 证据 | 用小线性任务固定训练工程边界：config hash、baseline、JSONL events、optimizer/scheduler state、best checkpoint reload 和 resume 等价 |
| 11 | PyTorch 文本分类项目 | [PyTorch 文本分类项目第一课：tokenize、vocab、collate 和 baseline 怎么串起来](/computer-science-teaching/2026/04/16/deep-learning-pytorch-text-classification.html) | 同一篇文章生成 tokenize/vocab、padded batch、baseline、confusion matrix 和 checkpoint reload 证据 | 用 support-ticket toy task 解释文本到 tensor 的管线，并诚实比较 majority、first-token、keyword-rule 与神经模型 |
| 12 | PyTorch 字符级语言模型项目 | [PyTorch 字符级语言模型第一课：next-character、GRU hidden state 和采样边界怎么连起来](/computer-science-teaching/2026/04/17/deep-learning-pytorch-char-lm.html) | 同一篇文章生成 shifted input/target、prompt next-character、baseline 和 checkpoint reload 证据 | 用 toy grammar 解释语言模型监督信号、teacher forcing、GRU hidden state、bigram final-label baseline 和采样边界 |
| 13 | PyTorch 推理工程边界 | [PyTorch 推理工程第一课：eval、inference_mode、batching 和 latency 边界怎么检查](/computer-science-teaching/2026/04/17/deep-learning-pytorch-inference-boundary.html) | 同一篇文章生成 eval/inference_mode、batch-vs-single、prediction table、timing 和 checkpoint reload 证据 | 用带 Dropout/BatchNorm 的 toy classifier 解释推理模式、无梯度边界、batching 和本地 timing 的证据范围 |
| 14 | Linux 网络、路径与服务边界补充 | [Linux 网络模型](/computer-science-teaching/2026/04/25/linux-network-model-interface-route-socket.html) | [本地服务地图、路径边界和加固报告](/computer-science-teaching/2026/04/25/linux-network-security-capstone-checklist.html) | 已完成；作为网络、路径处理和本地服务边界的补充材料 |
| 15 | 交叉安全基础导读 | [交叉安全基础导读：具身智能安全、抗量子密码和真实系统为什么会连在一起](/computer-science-teaching/2026/04/26/cross-security-embodied-ai-pqc-foundations.html) | 同一篇文章整理概念地图、资料链接和最小练习 | 建立具身智能传感器闭环、PQC 迁移和真实系统安全的共同问题框架 |

## 从0到可运行项目路线

语言教学采用有限发布包：每门语言围绕一个结课项目，从环境、核心语法、依赖管理、标准库、第三方库、测试、配置、日志、README 和 demo transcript 逐步推进。文章数量服务于可复现项目，不以单纯篇数作为完成标准。

当前路线：

| 方向 | 目标项目形态 | 重点能力 |
| --- | --- | --- |
| 本地小模型与 Agent | 课程学习 Agent + 领域 LoRA | 任务契约、RAG、工具 schema、状态/trace、Qwen3-0.6B、response-only SFT、held-out 评测和失败驱动优化 |
| Python | 本地证据 CLI + API | venv、pyproject、文件/JSON/CSV、Typer、pytest、FastAPI、httpx、配置和日志 |
| Java | 后端 REST API | JDK/JVM、Maven/Gradle、集合/泛型、JUnit、Jackson、Spring Boot、数据访问 |
| Go | 本地服务健康检查器 | module、struct/interface/error、JSON/CSV、net/http、context、goroutine/channel、CLI、测试、优雅关闭 |
| C++ | 本地文件索引 CLI + API | CMake/Ninja、FetchContent、CLI11、nlohmann/json、CSV、Catch2、spdlog、cpp-httplib、README/demo |
| Rust | 日志洞察 CLI + 本地 API | Cargo、ownership/borrowing、Result/Option、thiserror/anyhow、serde、clap、测试、clippy、Tokio/Axum、tracing |
| SQL 实用开发 | 本地 SQLite 报表 CLI | schema、CRUD、JOIN、GROUP BY、事务、迁移、参数化查询、CSV/JSON 导入导出、EXPLAIN QUERY PLAN |
| 数据库与缓存开发实践 | 库存订单系统 + 报表缓存 | SQLite schema 迁移、参数化 CRUD、索引计划、事务扣库存、cache-aside、TTL、显式失效、JSON/SVG/Markdown 报告 |
| 容器化与本地部署 | Python HTTP 服务容器化 | Dockerfile、build context、`.dockerignore`、端口发布、环境变量、bind mount、HEALTHCHECK、logs/inspect、Compose、部署报告 |
| 深度学习/AI 工程入门 | NumPy MLP spiral classifier | 固定 seed、数据切分、majority/linear baseline、softmax/cross entropy、手写反向传播、gradient check、训练历史、checkpoint、model card |
| 深度学习 CNN 机制 | shifted 8x8 bar classifier | 纯 Python conv2d、padding/stride、ReLU、max pooling、global max、majority/raw-template/conv-feature baseline 对比 |
| 深度学习 RNN 机制 | delayed-cue sequence classifier | 纯 Python recurrent step、hidden trace、majority/last-token/suffix/no-recurrence/RNN baseline 对比 |
| 深度学习 LSTM/GRU gate 机制 | delayed-cue sequence classifier with distractors | 纯 Python LSTM cell state、GRU update gate、vanilla RNN overwrite、majority/last-token/gated baseline 对比 |
| 深度学习 attention 机制 | key-value lookup classifier | 纯 Python scaled dot-product attention、query/key/value、majority/last-value/bag/fixed-summary/attention baseline 对比 |
| Transformer position/mask 机制 | order lookup + future-leak probe | 纯 Python positional attention、causal mask、bag/no-position/unmasked/causal baseline 对比 |
| Transformer multi-head/block 机制 | pair lookup + block information-flow probe | 纯 Python multi-head pair read、single scalar collision、attention/residual/FFN baseline 对比 |
| PyTorch Transformer encoder 项目 | order-sensitive sequence classifier | PyTorch `nn.TransformerEncoder`、baseline、padding mask、训练/评估 loop、checkpoint reload 和报告 |
| PyTorch 训练工程 | 2D sign classifier | config hash、balanced split、majority/x-only baseline、train/eval/no_grad、checkpoint、optimizer/scheduler state、resume equivalence、JSONL、model card、artifact manifest |
| PyTorch 文本分类项目 | support-ticket intent classifier | tokenize、vocab、`<pad>/<unk>`、Dataset/DataLoader、collate_fn、padding/mask、mean embedding、baseline、confusion matrix、checkpoint reload |
| PyTorch 字符级语言模型项目 | toy grammar next-character predictor | character vocab、`<bos>/<eos>/<pad>`、shifted input/target、GRU hidden state、teacher forcing、bigram baseline、prompt next-char、checkpoint reload |
| PyTorch 推理工程边界 | toy 2D classifier inference harness | `model.eval()`、`torch.inference_mode()`、Dropout/BatchNorm mode checks、batch-vs-single equality、prediction table、local latency smoke、checkpoint reload |
| 深度学习基础 | XOR toy classifier baseline → MLP | NumPy/tensor、线性代数、autograd、概率统计、优化、baseline、Dataset/DataLoader、checkpoint、可复现实验 |
| Linux 本地帮助与文档阅读 | doc probe + transcript | version、--help、man -k、manual section、pydoc、subcommand help、filtered evidence |
| Linux 软件包、PATH 与命令定位 | package path probe + transcript | command -v、type -a、PATH 顺序、execute bit、dpkg owner、package file list、apt policy |
| Linux 环境变量与项目环境隔离 | env/profile probe + transcript | shell local variable、export、env -i、.bashrc/profile、BASH_ENV、project env.sh、subshell |
| Linux 脚本参数、退出状态与错误处理 | script error probe + transcript | "$@"、shift、exit status、set -euo pipefail、if command、trap cleanup、usage/exit code |
| 项目配置文件与日志边界 | config/log probe + transcript | defaults/file/env/CLI precedence、schema validation、secret boundary、dry-run、JSONL logging、run_id |
| 项目数据目录、临时文件与原子写入 | atomic publication probe + manifest + transcript | source/config/input/cache/temp/output、same-directory temp、fsync、os.replace、failure preservation、idempotent rerun、SHA-256 manifest |
| 项目锁、并发写入与版本冲突 | concurrent writer probe + conflict summary + transcript | atomic visibility、stable lock file、flock、完整临界区、expected version、conflict rc、retry、timeout和distributed boundary |
| 项目重试、幂等键与副作用边界 | retry/idempotency/outbox/side-effect probe + transcript | crash-after-effect、idempotency key、fingerprint conflict、transactional outbox、stable event ID、receiver dedupe、transient/permanent retry policy |
| 项目后台任务、队列与可观测性边界 | queue probe + JSONL events + status report | atomic lease、visibility timeout、heartbeat、retry backoff、max attempts、dead-letter、structured events和status report |
| 项目服务启动、健康检查与优雅关闭边界 | service lifecycle probe + JSONL events + status report | liveness、readiness、status、SIGTERM、refuse new work、graceful drain、grace timeout、PID/port state file和structured lifecycle logs |
| 项目运行时指标、日志聚合与最小报警边界 | runtime events + metrics + alerts + report | JSONL logs、request counters、status family、latency buckets、p50/p90、error rate、slow rate、sample-size suppression和alert rules |
| Linux 网络、路径与服务边界补充 | 本地 HTTP 服务 + service map + hardening report | interface/route/socket/resolver、ss/curl、loopback service map、HTTP headers、path boundary、subprocess boundary |
| CUDA 与本地小模型工程 | CUDA 搜索加速器 + 本地领域 agent | 硬件瓶颈判断、GPU 环境证据、SIMT/访存/profiling、bitmask 搜索、LoRA/QLoRA、RAG、工具调用和评估 |

Linux、网络、路径和服务边界文章作为横向支撑：每篇都给出本地命令、预期观察、实验边界和可复跑小产物。

## 深度学习路线

深度学习内容按有限发布包推进。当前已经覆盖可复现实验、baseline/MLP、NumPy AI 工程包、CNN 机制第一课、RNN hidden-state 机制第一课、LSTM/GRU gate 机制第一课、attention key-value 机制第一课、Transformer position/mask 机制第一课、Transformer multi-head/block 机制第二课、PyTorch 最小 Transformer encoder 项目、PyTorch 训练工程第一课、PyTorch 文本分类项目第一课、PyTorch 字符级语言模型第一课，以及 PyTorch 推理工程边界第一课。现阶段重点是整理这些文章之间的先后关系和实验边界；除非路线出现明显断点，不继续增加长尾模型主题。涉及模型效果的文章必须给出 baseline；只解释机制的文章要明确边界，并用可运行实验说明它解释的是哪一层机制。

## 已归入本栏目

{% assign posts = site.posts | where: "column", "computer-science-teaching" %}
{% if posts.size == 0 %}
当前没有匹配到本栏目文章。请先回到[栏目地图](/columns/)或[全部文章](/posts/)确认导航入口。
{% else %}
{% for post in posts %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%Y-%m-%d" }}
{% endfor %}
{% endif %}
