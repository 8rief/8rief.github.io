# CUDA 与本地小模型工程基础包

这个 lab 是博客系列的总纲验证包。它不安装任何依赖，只读取本地硬件、CUDA工具链和Python包状态，并生成需求→原理→实验路线矩阵。

运行：

```bash
./run_lab.sh
```

产物：

- `reports/gpu_env_probe.json`：机器、GPU、nvcc、Python包状态。
- `reports/gpu_env_report.md`：面向文章引用的环境报告。
- `reports/cuda_local_ai_roadmap.json`：路线结构化数据。
- `reports/cuda_local_ai_roadmap.md`：需求到实验的路线矩阵。
- `reports/run_lab_output.txt`：运行 transcript。

解释：缺少 `nvcc` 或 PyTorch CUDA 不会让这个总纲 lab 失败；它们会被记录为后续安装和验证步骤的 readiness gap。
