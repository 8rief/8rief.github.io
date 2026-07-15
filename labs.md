---
layout: page
title: 实验代码
permalink: /labs/
---

这里集中放博客文章配套的最小可运行实验代码。文章负责解释问题、机制和边界；实验目录负责给出可以在 WSL/Linux 里实际运行的源码、脚本和测试。

## 使用方式

首次使用时，在 WSL 终端执行：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/<实验目录>
bash run_lab.sh
```

已有本地仓库时：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/<实验目录>
bash run_lab.sh
```

`git pull --ff-only` 只在本地没有分叉提交时更新代码，用于保持公开实验和本地改动边界清晰。

## 按路线选择实验

目录清单按学习目标选择实验组；每组对应一条可运行路线。

| 目标 | 优先实验 |
| --- | --- |
| 建立 Linux 和项目基础 | `linux-local-docs-workflow`、`linux-path-package-resolution`、`linux-env-profile-project-isolation`、`linux-script-args-exit-errors`、`git-foundations-collaboration` |
| 做一个可运行语言项目 | `python-local-evidence-kit`、`java-task-tracker-api`、`go-health-monitor-service`、`rust-log-insight-cli`、`cpp-file-indexer-service` |
| 理解服务和后端边界 | `project-http-api-contract-boundary`、`project-session-auth-cookie-boundary`、`project-database-migration-schema-evolution`、`project-background-jobs-queue-observability-boundary` |
| 学算法和数学 | `algorithm-practical-foundations`、`algorithms-number-theory-toolkit`、`algorithms-heavy-light-decomposition`、`deep-learning-ai-engineering`、`deep-learning-foundations-pytorch` |
| 学深度学习和 PyTorch | `deep-learning-cnn-foundations`、`deep-learning-rnn-hidden-state`、`deep-learning-attention-key-value`、`deep-learning-pytorch-training-engineering`、`deep-learning-pytorch-inference-boundary` |
| 学 CUDA 和本地模型 | `hardware-bottleneck-foundations`、`cuda-local-ai-foundations`、`cuda-local-ai-column`、`local-small-model-agent-course` |

## 怎样读实验目录

- 先看对应文章，确认这个实验要证明什么。
- 再读 `run_lab.sh`，它通常会说明依赖、测试和生成的报告。
- 成功运行后，优先查看本地生成的 JSON、Markdown 或 transcript。公开仓库不提交运行产物；这些结果在本地机器重新生成。
- 缺依赖时先读脚本顶部和文章里的环境段，再按明确依赖安装命令处理报错。
- 一个实验跑完后，至少留下三项本地观察：命令是否成功、生成了哪些报告或 transcript、结果能支持文章里的哪条结论。

## 目录清单

| 实验目录 | 对应内容 |
| --- | --- |
| <a id="algorithm-practical-foundations"></a>[`algorithm-practical-foundations`](/assets/labs/algorithm-practical-foundations/README.md) · [run_lab.sh](/assets/labs/algorithm-practical-foundations/run_lab.sh) | 算法实用基础：BFS、DFS、DP、堆、最短路与复杂度边界 |
| <a id="algorithms-amortized-dynamic-array"></a>[`algorithms-amortized-dynamic-array`](/assets/labs/algorithms-amortized-dynamic-array/README.md) · [run_lab.sh](/assets/labs/algorithms-amortized-dynamic-array/run_lab.sh) | 摊还分析与动态数组实验 |
| <a id="algorithms-binary-lifting-lca"></a>[`algorithms-binary-lifting-lca`](/assets/labs/algorithms-binary-lifting-lca/README.md) · [run_lab.sh](/assets/labs/algorithms-binary-lifting-lca/run_lab.sh) | 倍增 LCA 实验 |
| <a id="algorithms-heavy-light-decomposition"></a>[`algorithms-heavy-light-decomposition`](/assets/labs/algorithms-heavy-light-decomposition/README.md) · [run_lab.sh](/assets/labs/algorithms-heavy-light-decomposition/run_lab.sh) | 树链剖分实验 |
| <a id="algorithms-li-chao-tree"></a>[`algorithms-li-chao-tree`](/assets/labs/algorithms-li-chao-tree/README.md) · [run_lab.sh](/assets/labs/algorithms-li-chao-tree/run_lab.sh) | Li Chao 线段树实验 |
| <a id="algorithms-ntt-convolution"></a>[`algorithms-ntt-convolution`](/assets/labs/algorithms-ntt-convolution/README.md) · [run_lab.sh](/assets/labs/algorithms-ntt-convolution/run_lab.sh) | NTT 卷积实验 |
| <a id="algorithms-number-theory-toolkit"></a>[`algorithms-number-theory-toolkit`](/assets/labs/algorithms-number-theory-toolkit/README.md) · [run_lab.sh](/assets/labs/algorithms-number-theory-toolkit/run_lab.sh) | 数论工具箱实验 |
| <a id="algorithms-persistent-segment-tree"></a>[`algorithms-persistent-segment-tree`](/assets/labs/algorithms-persistent-segment-tree/README.md) · [run_lab.sh](/assets/labs/algorithms-persistent-segment-tree/run_lab.sh) | 可持久化线段树实验 |
| <a id="algorithms-randomized-quickselect"></a>[`algorithms-randomized-quickselect`](/assets/labs/algorithms-randomized-quickselect/README.md) · [run_lab.sh](/assets/labs/algorithms-randomized-quickselect/run_lab.sh) | 随机 Quickselect 实验 |
| <a id="algorithms-sprague-grundy-games"></a>[`algorithms-sprague-grundy-games`](/assets/labs/algorithms-sprague-grundy-games/README.md) · [run_lab.sh](/assets/labs/algorithms-sprague-grundy-games/run_lab.sh) | Sprague-Grundy 博弈实验 |
| <a id="algorithms-suffix-array-lcp"></a>[`algorithms-suffix-array-lcp`](/assets/labs/algorithms-suffix-array-lcp/README.md) · [run_lab.sh](/assets/labs/algorithms-suffix-array-lcp/run_lab.sh) | 后缀数组与 LCP 实验 |
| <a id="cpp-file-indexer-service"></a>[`cpp-file-indexer-service`](/assets/labs/cpp-file-indexer-service/README.md) · [run_lab.sh](/assets/labs/cpp-file-indexer-service/run_lab.sh) | C++ 文件索引服务项目 |
| <a id="deep-learning-foundations-pytorch"></a>[`deep-learning-foundations-pytorch`](/assets/labs/deep-learning-foundations-pytorch/README.md) · [run_lab.sh](/assets/labs/deep-learning-foundations-pytorch/run_lab.sh) | PyTorch 深度学习基础实验 |
| <a id="deep-learning-cnn-foundations"></a>[`deep-learning-cnn-foundations`](/assets/labs/deep-learning-cnn-foundations/README.md) · [run_lab.sh](/assets/labs/deep-learning-cnn-foundations/run_lab.sh) | CNN 卷积、padding、stride、ReLU、pooling 与平移泛化实验 |
| <a id="deep-learning-rnn-hidden-state"></a>[`deep-learning-rnn-hidden-state`](/assets/labs/deep-learning-rnn-hidden-state/README.md) · [run_lab.sh](/assets/labs/deep-learning-rnn-hidden-state/run_lab.sh) | RNN hidden state、recurrent carry 与 delayed cue 序列记忆实验 |
| <a id="deep-learning-lstm-gru-gates"></a>[`deep-learning-lstm-gru-gates`](/assets/labs/deep-learning-lstm-gru-gates/README.md) · [run_lab.sh](/assets/labs/deep-learning-lstm-gru-gates/run_lab.sh) | LSTM/GRU gate、cell state、update gate 与 suffix distractor 记忆控制实验 |
| <a id="deep-learning-attention-key-value"></a>[`deep-learning-attention-key-value`](/assets/labs/deep-learning-attention-key-value/README.md) · [run_lab.sh](/assets/labs/deep-learning-attention-key-value/run_lab.sh) | Attention query/key/value、scaled dot-product 与 key-value binding 查找实验 |
| <a id="deep-learning-transformer-position-mask"></a>[`deep-learning-transformer-position-mask`](/assets/labs/deep-learning-transformer-position-mask/README.md) · [run_lab.sh](/assets/labs/deep-learning-transformer-position-mask/run_lab.sh) | Transformer position encoding、causal mask 与 future leakage 边界实验 |
| <a id="deep-learning-transformer-block"></a>[`deep-learning-transformer-block`](/assets/labs/deep-learning-transformer-block/README.md) · [run_lab.sh](/assets/labs/deep-learning-transformer-block/run_lab.sh) | Transformer multi-head attention、residual、LayerNorm 与 FFN block 机制实验 |
| <a id="deep-learning-pytorch-transformer-encoder"></a>[`deep-learning-pytorch-transformer-encoder`](/assets/labs/deep-learning-pytorch-transformer-encoder/README.md) · [run_lab.sh](/assets/labs/deep-learning-pytorch-transformer-encoder/run_lab.sh) | PyTorch Transformer encoder、baseline、padding mask、训练循环和 checkpoint 实验 |
| <a id="deep-learning-pytorch-training-engineering"></a>[`deep-learning-pytorch-training-engineering`](/assets/labs/deep-learning-pytorch-training-engineering/README.md) · [run_lab.sh](/assets/labs/deep-learning-pytorch-training-engineering/run_lab.sh) | PyTorch config、validation、checkpoint/resume、JSONL 日志、model card 与 artifact manifest 训练工程实验 |
| <a id="deep-learning-pytorch-text-classification"></a>[`deep-learning-pytorch-text-classification`](/assets/labs/deep-learning-pytorch-text-classification/README.md) · [run_lab.sh](/assets/labs/deep-learning-pytorch-text-classification/run_lab.sh) | PyTorch tokenize、vocab、Dataset、DataLoader/collate、padding、baseline、confusion matrix 和 checkpoint 文本分类实验 |
| <a id="deep-learning-pytorch-char-lm"></a>[`deep-learning-pytorch-char-lm`](/assets/labs/deep-learning-pytorch-char-lm/README.md) · [run_lab.sh](/assets/labs/deep-learning-pytorch-char-lm/run_lab.sh) | PyTorch character vocab、shifted input/target、GRU hidden state、teacher forcing、bigram baseline、prompt next-character 和 checkpoint 字符级语言模型实验 |
| <a id="deep-learning-pytorch-inference-boundary"></a>[`deep-learning-pytorch-inference-boundary`](/assets/labs/deep-learning-pytorch-inference-boundary/README.md) · [run_lab.sh](/assets/labs/deep-learning-pytorch-inference-boundary/run_lab.sh) | PyTorch eval/inference_mode、Dropout/BatchNorm mode check、batch-vs-single 输出一致性、prediction table、latency smoke 和 checkpoint reload 推理工程实验 |
| <a id="go-health-monitor-service"></a>[`go-health-monitor-service`](/assets/labs/go-health-monitor-service/README.md) · [run_lab.sh](/assets/labs/go-health-monitor-service/run_lab.sh) | Go 健康检查服务项目 |
| <a id="java-task-tracker-api"></a>[`java-task-tracker-api`](/assets/labs/java-task-tracker-api/README.md) · [run_lab.sh](/assets/labs/java-task-tracker-api/run_lab.sh) | Java/Maven 任务跟踪 API 项目 |
| <a id="linux-path-traversal-boundary"></a>[`linux-path-traversal-boundary`](/assets/labs/linux-path-traversal-boundary/README.md) · [run_lab.sh](/assets/labs/linux-path-traversal-boundary/run_lab.sh) | Linux 路径穿越边界实验 |
| <a id="python-local-evidence-kit"></a>[`python-local-evidence-kit`](/assets/labs/python-local-evidence-kit/README.md) · [run_lab.sh](/assets/labs/python-local-evidence-kit/run_lab.sh) | Python 本地证据包项目 |
| <a id="rust-log-insight-cli"></a>[`rust-log-insight-cli`](/assets/labs/rust-log-insight-cli/README.md) · [run_lab.sh](/assets/labs/rust-log-insight-cli/run_lab.sh) | Rust 日志分析 CLI 项目 |
| <a id="linux-network-security-basics"></a>[`linux-network-security-basics`](/assets/labs/linux-network-security-basics/README.md) · [run_lab.sh](/assets/labs/linux-network-security-basics/run_lab.sh) | Linux 网络安全基础实验 |
| <a id="git-foundations-collaboration"></a>[`git-foundations-collaboration`](/assets/labs/git-foundations-collaboration/README.md) · [run_lab.sh](/assets/labs/git-foundations-collaboration/run_lab.sh) | Git 协作与发布实验 |
| <a id="os-linux-process-files"></a>[`os-linux-process-files`](/assets/labs/os-linux-process-files/README.md) · [run_lab.sh](/assets/labs/os-linux-process-files/run_lab.sh) | Linux 进程与文件观察实验 |
| <a id="sql-practical-development"></a>[`sql-practical-development`](/assets/labs/sql-practical-development/README.md) · [run_lab.sh](/assets/labs/sql-practical-development/run_lab.sh) | SQL 报告 CLI 与索引实验 |
| <a id="debug-build-tooling-foundations"></a>[`debug-build-tooling-foundations`](/assets/labs/debug-build-tooling-foundations/README.md) · [run_lab.sh](/assets/labs/debug-build-tooling-foundations/run_lab.sh) | 调试与构建工具链实验 |
| <a id="network-foundations-nonsecurity"></a>[`network-foundations-nonsecurity`](/assets/labs/network-foundations-nonsecurity/README.md) · [run_lab.sh](/assets/labs/network-foundations-nonsecurity/run_lab.sh) | 网络基础观察服务实验 |
| <a id="software-project-structure-foundations"></a>[`software-project-structure-foundations`](/assets/labs/software-project-structure-foundations/README.md) · [run_lab.sh](/assets/labs/software-project-structure-foundations/run_lab.sh) | 软件项目骨架实验 |
| <a id="deep-learning-ai-engineering"></a>[`deep-learning-ai-engineering`](/assets/labs/deep-learning-ai-engineering/README.md) · [run_lab.sh](/assets/labs/deep-learning-ai-engineering/run_lab.sh) | AI 工程：数据、基线与 NumPy MLP 实验 |
| <a id="container-deployment-practice"></a>[`container-deployment-practice`](/assets/labs/container-deployment-practice/README.md) · [run_lab.sh](/assets/labs/container-deployment-practice/run_lab.sh) | 容器镜像与部署证据实验 |
| <a id="data-processing-visualization"></a>[`data-processing-visualization`](/assets/labs/data-processing-visualization/README.md) · [run_lab.sh](/assets/labs/data-processing-visualization/run_lab.sh) | 数据处理与可视化实验 |
| <a id="database-cache-practice"></a>[`database-cache-practice`](/assets/labs/database-cache-practice/README.md) · [run_lab.sh](/assets/labs/database-cache-practice/run_lab.sh) | 数据库与缓存实践实验 |
| <a id="linux-cli-shell-automation"></a>[`linux-cli-shell-automation`](/assets/labs/linux-cli-shell-automation/README.md) · [run_lab.sh](/assets/labs/linux-cli-shell-automation/run_lab.sh) | Linux CLI 与 Shell 自动化实验 |
| <a id="computer-systems-os-foundations"></a>[`computer-systems-os-foundations`](/assets/labs/computer-systems-os-foundations/README.md) · [run_lab.sh](/assets/labs/computer-systems-os-foundations/run_lab.sh) | 计算机系统与操作系统基础实验 |
| <a id="minimal-web-fullstack"></a>[`minimal-web-fullstack`](/assets/labs/minimal-web-fullstack/README.md) · [run_lab.sh](/assets/labs/minimal-web-fullstack/run_lab.sh) | 最小 Web 全栈请求/响应实验 |
| <a id="cuda-local-ai-foundations"></a>[`cuda-local-ai-foundations`](/assets/labs/cuda-local-ai-foundations/README.md) · [run_lab.sh](/assets/labs/cuda-local-ai-foundations/run_lab.sh) | CUDA 与本地 AI 环境需求实验 |
| <a id="cuda-local-ai-column"></a>[`cuda-local-ai-column`](/assets/labs/cuda-local-ai-column/README.md) · [run_lab.sh](/assets/labs/cuda-local-ai-column/run_lab.sh) | CUDA 编程、归约、N-Queens 与本地 AI 栏目实验 |
| <a id="linux-env-profile-project-isolation"></a>[`linux-env-profile-project-isolation`](/assets/labs/linux-env-profile-project-isolation/README.md) · [run_lab.sh](/assets/labs/linux-env-profile-project-isolation/run_lab.sh) | Linux 环境变量与项目隔离实验 |
| <a id="linux-local-docs-workflow"></a>[`linux-local-docs-workflow`](/assets/labs/linux-local-docs-workflow/README.md) · [run_lab.sh](/assets/labs/linux-local-docs-workflow/run_lab.sh) | Linux 本地文档、man/help/version 证据实验 |
| <a id="linux-path-package-resolution"></a>[`linux-path-package-resolution`](/assets/labs/linux-path-package-resolution/README.md) · [run_lab.sh](/assets/labs/linux-path-package-resolution/run_lab.sh) | Linux PATH、包与命令解析实验 |
| <a id="linux-script-args-exit-errors"></a>[`linux-script-args-exit-errors`](/assets/labs/linux-script-args-exit-errors/README.md) · [run_lab.sh](/assets/labs/linux-script-args-exit-errors/run_lab.sh) | Shell 脚本参数、退出码与错误处理实验 |
| <a id="local-small-model-agent-course"></a>[`local-small-model-agent-course`](/assets/labs/local-small-model-agent-course/README.md) · [run_lab.sh](/assets/labs/local-small-model-agent-course/run_lab.sh) | 本地小模型与 Agent 开发完整课程实验 |
| <a id="project-config-logging-boundary"></a>[`project-config-logging-boundary`](/assets/labs/project-config-logging-boundary/README.md) · [run_lab.sh](/assets/labs/project-config-logging-boundary/run_lab.sh) | 项目配置文件与日志边界实验 |
| <a id="project-data-temp-atomic-write-boundary"></a>[`project-data-temp-atomic-write-boundary`](/assets/labs/project-data-temp-atomic-write-boundary/README.md) · [run_lab.sh](/assets/labs/project-data-temp-atomic-write-boundary/run_lab.sh) | 项目数据、临时文件与原子写入实验 |
| <a id="project-lock-concurrent-write-version-conflict"></a>[`project-lock-concurrent-write-version-conflict`](/assets/labs/project-lock-concurrent-write-version-conflict/README.md) · [run_lab.sh](/assets/labs/project-lock-concurrent-write-version-conflict/run_lab.sh) | 项目锁、并发写与版本冲突实验 |
| <a id="project-retry-idempotency-side-effect-boundary"></a>[`project-retry-idempotency-side-effect-boundary`](/assets/labs/project-retry-idempotency-side-effect-boundary/README.md) · [run_lab.sh](/assets/labs/project-retry-idempotency-side-effect-boundary/run_lab.sh) | 重试、幂等性与副作用边界实验 |
| <a id="project-background-jobs-queue-observability-boundary"></a>[`project-background-jobs-queue-observability-boundary`](/assets/labs/project-background-jobs-queue-observability-boundary/README.md) · [run_lab.sh](/assets/labs/project-background-jobs-queue-observability-boundary/run_lab.sh) | 后台任务、队列与可观测性实验 |
| <a id="project-service-startup-health-graceful-shutdown-boundary"></a>[`project-service-startup-health-graceful-shutdown-boundary`](/assets/labs/project-service-startup-health-graceful-shutdown-boundary/README.md) · [run_lab.sh](/assets/labs/project-service-startup-health-graceful-shutdown-boundary/run_lab.sh) | 服务启动、健康检查与优雅关闭实验 |
| <a id="project-runtime-metrics-log-aggregation-alert-boundary"></a>[`project-runtime-metrics-log-aggregation-alert-boundary`](/assets/labs/project-runtime-metrics-log-aggregation-alert-boundary/README.md) · [run_lab.sh](/assets/labs/project-runtime-metrics-log-aggregation-alert-boundary/run_lab.sh) | 运行时指标、日志聚合与告警边界实验 |
| <a id="project-test-pyramid-regression-boundary"></a>[`project-test-pyramid-regression-boundary`](/assets/labs/project-test-pyramid-regression-boundary/README.md) · [run_lab.sh](/assets/labs/project-test-pyramid-regression-boundary/run_lab.sh) | 测试金字塔、CLI smoke 与 golden regression 实验 |
| <a id="project-http-api-contract-boundary"></a>[`project-http-api-contract-boundary`](/assets/labs/project-http-api-contract-boundary/README.md) · [run_lab.sh](/assets/labs/project-http-api-contract-boundary/run_lab.sh) | HTTP API method/status/JSON/error/idempotency 契约实验 |
| <a id="project-session-auth-cookie-boundary"></a>[`project-session-auth-cookie-boundary`](/assets/labs/project-session-auth-cookie-boundary/README.md) · [run_lab.sh](/assets/labs/project-session-auth-cookie-boundary/run_lab.sh) | 登录、Cookie、server-side session、CSRF 和角色边界实验 |
| <a id="project-database-migration-schema-evolution"></a>[`project-database-migration-schema-evolution`](/assets/labs/project-database-migration-schema-evolution/README.md) · [run_lab.sh](/assets/labs/project-database-migration-schema-evolution/run_lab.sh) | SQLite migration、backfill、rollback 与 schema 演化实验 |
| <a id="hardware-bottleneck-foundations"></a>[`hardware-bottleneck-foundations`](/assets/labs/hardware-bottleneck-foundations/README.md) · [run_lab.sh](/assets/labs/hardware-bottleneck-foundations/run_lab.sh) | 硬件瓶颈基础：cache locality、stride、branch 与 CUDA transfer/timing 实验 |

## 运行产物边界

公开仓库只保留源码、测试、少量输入数据和脚本。运行结果、编译产物、本地工具链缓存和模型权重体积大、依赖机器环境，也容易夹带本地路径；这些内容由本地机器重新生成。
