# 实验代码使用说明

这里放的是博客文章配套的最小可运行实验代码。文章解释概念与过程，本目录提供你可以在 WSL/Linux 里实际运行的源码和脚本。

## 如果你还没有克隆本站仓库

在 WSL 终端执行：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/<实验目录>
bash run_lab.sh
```

这些命令分别做四件事：进入你的 WSL home 目录；下载本站公开仓库；进入某个实验目录；用 Bash 执行该实验的主脚本。

## 如果你已经克隆过本站仓库

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/<实验目录>
bash run_lab.sh
```

`git pull --ff-only` 只在本地没有分叉提交时更新代码，能避免把学习实验和你自己的改动混在一起。

## 目录清单

| 实验目录 | 对应内容 |
| --- | --- |
| [`algorithm-practical-foundations`](/assets/labs/algorithm-practical-foundations/README.md) | 算法实用基础：BFS、DFS、DP、堆、最短路与复杂度边界 |
| [`algorithms-amortized-dynamic-array`](/assets/labs/algorithms-amortized-dynamic-array/README.md) | 摊还分析与动态数组实验 |
| [`algorithms-binary-lifting-lca`](/assets/labs/algorithms-binary-lifting-lca/README.md) | 倍增 LCA 实验 |
| [`algorithms-heavy-light-decomposition`](/assets/labs/algorithms-heavy-light-decomposition/README.md) | 树链剖分实验 |
| [`algorithms-li-chao-tree`](/assets/labs/algorithms-li-chao-tree/README.md) | Li Chao 线段树实验 |
| [`algorithms-ntt-convolution`](/assets/labs/algorithms-ntt-convolution/README.md) | NTT 卷积实验 |
| [`algorithms-number-theory-toolkit`](/assets/labs/algorithms-number-theory-toolkit/README.md) | 数论工具箱实验 |
| [`algorithms-persistent-segment-tree`](/assets/labs/algorithms-persistent-segment-tree/README.md) | 可持久化线段树实验 |
| [`algorithms-randomized-quickselect`](/assets/labs/algorithms-randomized-quickselect/README.md) | 随机 Quickselect 实验 |
| [`algorithms-sprague-grundy-games`](/assets/labs/algorithms-sprague-grundy-games/README.md) | Sprague-Grundy 博弈实验 |
| [`algorithms-suffix-array-lcp`](/assets/labs/algorithms-suffix-array-lcp/README.md) | 后缀数组与 LCP 实验 |
| [`cpp-file-indexer-service`](/assets/labs/cpp-file-indexer-service/README.md) | C++ 文件索引服务项目 |
| [`deep-learning-foundations-pytorch`](/assets/labs/deep-learning-foundations-pytorch/README.md) | PyTorch 深度学习基础实验 |
| [`deep-learning-cnn-foundations`](/assets/labs/deep-learning-cnn-foundations/README.md) | CNN 卷积、padding、stride、ReLU、pooling 与平移泛化实验 |
| [`deep-learning-rnn-hidden-state`](/assets/labs/deep-learning-rnn-hidden-state/README.md) | RNN hidden state、recurrent carry 与 delayed cue 序列记忆实验 |
| [`deep-learning-lstm-gru-gates`](/assets/labs/deep-learning-lstm-gru-gates/README.md) | LSTM/GRU gate、cell state、update gate 与 suffix distractor 记忆控制实验 |
| [`deep-learning-attention-key-value`](/assets/labs/deep-learning-attention-key-value/README.md) | Attention query/key/value、scaled dot-product 与 key-value binding 查找实验 |
| [`deep-learning-transformer-position-mask`](/assets/labs/deep-learning-transformer-position-mask/README.md) | Transformer position encoding、causal mask 与 future leakage 边界实验 |
| [`deep-learning-transformer-block`](/assets/labs/deep-learning-transformer-block/README.md) | Transformer multi-head attention、residual、LayerNorm 与 FFN block 机制实验 |
| [`deep-learning-pytorch-transformer-encoder`](/assets/labs/deep-learning-pytorch-transformer-encoder/README.md) | PyTorch Transformer encoder、baseline、padding mask、训练循环和 checkpoint 实验 |
| [`deep-learning-pytorch-training-engineering`](/assets/labs/deep-learning-pytorch-training-engineering/README.md) | PyTorch config、validation、checkpoint/resume、JSONL 日志、model card 与 artifact manifest 训练工程实验 |
| [`deep-learning-pytorch-text-classification`](/assets/labs/deep-learning-pytorch-text-classification/README.md) | PyTorch tokenize、vocab、Dataset、DataLoader/collate、padding、baseline 和 checkpoint 文本分类实验 |
| [`deep-learning-pytorch-char-lm`](/assets/labs/deep-learning-pytorch-char-lm/README.md) | PyTorch character vocab、shifted input/target、GRU hidden state、teacher forcing、bigram baseline 和 checkpoint 字符级语言模型实验 |
| [`deep-learning-pytorch-inference-boundary`](/assets/labs/deep-learning-pytorch-inference-boundary/README.md) | PyTorch eval/inference_mode、batch-vs-single 输出一致性、prediction table、latency smoke 和 checkpoint reload 推理工程实验 |
| [`go-health-monitor-service`](/assets/labs/go-health-monitor-service/README.md) | Go 健康检查服务项目 |
| [`java-task-tracker-api`](/assets/labs/java-task-tracker-api/README.md) | Java/Maven 任务跟踪 API 项目 |
| [`linux-path-traversal-boundary`](/assets/labs/linux-path-traversal-boundary/README.md) | Linux 路径穿越边界实验 |
| [`python-local-evidence-kit`](/assets/labs/python-local-evidence-kit/README.md) | Python 本地证据包项目 |
| [`rust-log-insight-cli`](/assets/labs/rust-log-insight-cli/README.md) | Rust 日志分析 CLI 项目 |
| [`linux-network-security-basics`](/assets/labs/linux-network-security-basics/README.md) | Linux 网络安全基础实验 |
| [`git-foundations-collaboration`](/assets/labs/git-foundations-collaboration/README.md) | Git 协作与发布实验 |
| [`os-linux-process-files`](/assets/labs/os-linux-process-files/README.md) | Linux 进程与文件观察实验 |
| [`sql-practical-development`](/assets/labs/sql-practical-development/README.md) | SQL 报告 CLI 与索引实验 |
| [`debug-build-tooling-foundations`](/assets/labs/debug-build-tooling-foundations/README.md) | 调试与构建工具链实验 |
| [`network-foundations-nonsecurity`](/assets/labs/network-foundations-nonsecurity/README.md) | 网络基础观察服务实验 |
| [`software-project-structure-foundations`](/assets/labs/software-project-structure-foundations/README.md) | 软件项目骨架实验 |
| [`deep-learning-ai-engineering`](/assets/labs/deep-learning-ai-engineering/README.md) | AI 工程：数据、基线与 NumPy MLP 实验 |
| [`container-deployment-practice`](/assets/labs/container-deployment-practice/README.md) | 容器镜像与部署证据实验 |
| [`data-processing-visualization`](/assets/labs/data-processing-visualization/README.md) | 数据处理与可视化实验 |
| [`database-cache-practice`](/assets/labs/database-cache-practice/README.md) | 数据库与缓存实践实验 |
| [`linux-cli-shell-automation`](/assets/labs/linux-cli-shell-automation/README.md) | Linux CLI 与 Shell 自动化实验 |
| [`computer-systems-os-foundations`](/assets/labs/computer-systems-os-foundations/README.md) | 计算机系统与操作系统基础实验 |
| [`minimal-web-fullstack`](/assets/labs/minimal-web-fullstack/README.md) | 最小 Web 全栈请求/响应实验 |
| [`cuda-local-ai-foundations`](/assets/labs/cuda-local-ai-foundations/README.md) | CUDA 与本地 AI 环境需求实验 |
| [`cuda-local-ai-column`](/assets/labs/cuda-local-ai-column/README.md) | CUDA 编程、归约、N-Queens 与本地 AI 栏目实验 |
| [`linux-env-profile-project-isolation`](/assets/labs/linux-env-profile-project-isolation/README.md) | Linux 环境变量与项目隔离实验 |
| [`linux-local-docs-workflow`](/assets/labs/linux-local-docs-workflow/README.md) | Linux 本地文档、man/help/version 证据实验 |
| [`linux-path-package-resolution`](/assets/labs/linux-path-package-resolution/README.md) | Linux PATH、包与命令解析实验 |
| [`linux-script-args-exit-errors`](/assets/labs/linux-script-args-exit-errors/README.md) | Shell 脚本参数、退出码与错误处理实验 |
| [`local-small-model-agent-course`](/assets/labs/local-small-model-agent-course/README.md) | 本地小模型与 Agent 开发完整课程实验 |
| [`project-config-logging-boundary`](/assets/labs/project-config-logging-boundary/README.md) | 项目配置文件与日志边界实验 |
| [`project-data-temp-atomic-write-boundary`](/assets/labs/project-data-temp-atomic-write-boundary/README.md) | 项目数据、临时文件与原子写入实验 |
| [`project-lock-concurrent-write-version-conflict`](/assets/labs/project-lock-concurrent-write-version-conflict/README.md) | 项目锁、并发写与版本冲突实验 |
| [`project-retry-idempotency-side-effect-boundary`](/assets/labs/project-retry-idempotency-side-effect-boundary/README.md) | 重试、幂等性与副作用边界实验 |
| [`project-background-jobs-queue-observability-boundary`](/assets/labs/project-background-jobs-queue-observability-boundary/README.md) | 后台任务、队列与可观测性实验 |
| [`project-service-startup-health-graceful-shutdown-boundary`](/assets/labs/project-service-startup-health-graceful-shutdown-boundary/README.md) | 服务启动、健康检查与优雅关闭实验 |
| [`project-runtime-metrics-log-aggregation-alert-boundary`](/assets/labs/project-runtime-metrics-log-aggregation-alert-boundary/README.md) | 运行时指标、日志聚合与告警边界实验 |
| [`project-test-pyramid-regression-boundary`](/assets/labs/project-test-pyramid-regression-boundary/README.md) | 测试金字塔、CLI smoke 与 golden regression 实验 |
| [`project-http-api-contract-boundary`](/assets/labs/project-http-api-contract-boundary/README.md) | HTTP API method/status/JSON/error/idempotency 契约实验 |
| [`project-session-auth-cookie-boundary`](/assets/labs/project-session-auth-cookie-boundary/README.md) | 登录、Cookie、server-side session、CSRF 和角色边界实验 |
| [`project-database-migration-schema-evolution`](/assets/labs/project-database-migration-schema-evolution/README.md) | SQLite migration、backfill、rollback 与 schema 演化实验 |
| [`hardware-bottleneck-foundations`](/assets/labs/hardware-bottleneck-foundations/README.md) | 硬件瓶颈基础：cache locality、stride、branch 与 CUDA transfer/timing 实验 |

## 依赖说明

多数实验只依赖 Bash、Python 标准库或系统自带工具；涉及 CUDA、PyTorch、Go、Java、Rust、Node 或 Docker 的实验会在自己的 README 或脚本输出里说明缺失依赖。缺依赖时优先阅读脚本开头和文章里的环境段，不要盲目复制报错后的随机安装命令。

## 为什么不提交 reports、target、.tools、模型权重

公开仓库只保留源码、测试、少量输入数据和脚本。运行结果、编译产物、本地工具链缓存和模型权重体积大、依赖机器环境，也容易夹带本地路径；这些内容应该由你在自己的机器上重新生成。
