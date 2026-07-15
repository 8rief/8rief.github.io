# Deep Learning Foundations PyTorch Lab

This lab is a small PyTorch project that executes the teaching tensors on CPU for teaching deep-learning foundations before model recipes. It generates a deterministic nonlinear 2D classification dataset, runs tensor and autograd demos, trains a majority baseline, a linear baseline, and a small MLP, then writes metrics, history, and checkpoint artifacts.

Run the full lab:

```bash
./run_lab.sh
```

Expected key artifacts:

- `reports/transcript.txt`: environment, tests, demos, training, and comparison output.
- `reports/tensor_demo.json`: shape, dtype, broadcasting, and batch matrix examples.
- `reports/autograd_demo.json`: autograd gradient, analytic gradient, and finite-difference check.
- `reports/majority/metrics.json`: majority-class baseline.
- `reports/linear/metrics.json`: linear classifier baseline.
- `reports/mlp/metrics.json`: nonlinear MLP result.
- `reports/comparison.json`: side-by-side baseline comparison.

The dataset is synthetic and local. The lab reports whether CUDA is available, but all teaching tensors and models run on CPU by design. The result is an educational reproducibility check, not a benchmark of real-world model quality.
