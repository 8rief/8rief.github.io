# Transformer multi-head and block lab

This lab explains two mechanisms that appear immediately after basic attention:

1. **Multi-head attention**: two independent heads can read two different positions, while one scalar attention output can collide when it tries to compress two independent facts into one number.
2. **Transformer block**: attention brings in context, the residual path keeps the token's local signal, layer normalization keeps the scale controlled, and a position-wise feed-forward/readout step turns the mixed features into a local decision.

The lab uses only the Python standard library. It is a mechanism probe, not a claim about trained model quality or PyTorch runtime speed.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
PAIR_TEST_SAMPLES=8
BLOCK_TEST_SAMPLES=8
SINGLE_FIRST_HEAD_ACC=0.500
SINGLE_SECOND_HEAD_ACC=0.500
SINGLE_BLEND_HEAD_ACC=0.750
MULTI_HEAD_PAIR_ACC=1.000
MULTI_HEAD_GAIN_OVER_BEST_BASELINE=0.250
MULTI_HEAD_MIN_TOP_WEIGHT=0.968
HEADS_FOCUS_DIFFERENT_KEYS=yes
NO_ATTENTION_BLOCK_ACC=0.500
NO_RESIDUAL_BLOCK_ACC=0.500
ATTENTION_RESIDUAL_FFN_ACC=1.000
BLOCK_GAIN_OVER_BEST_BASELINE=0.500
LAYER_NORM_MEAN_OK=yes
LAYER_NORM_RMS_OK=yes
RUN_STATUS=ok
deep_learning_transformer_block_lab_status=ok
```

The generated `reports/` directory is local evidence. Public copies should contain the source, tests and runner only, not generated reports or Python caches.

## What the numbers mean

- `SINGLE_FIRST_HEAD_ACC=0.500`: reading only the first target recovers the color but guesses the shape.
- `SINGLE_SECOND_HEAD_ACC=0.500`: reading only the second target recovers the shape but guesses the color.
- `SINGLE_BLEND_HEAD_ACC=0.750`: one scalar blended head can separate three scalar values, but two labels collide at the same value.
- `MULTI_HEAD_PAIR_ACC=1.000`: two heads keep the two reads separate, so the downstream readout sees the pair.
- `NO_ATTENTION_BLOCK_ACC=0.500`: without attention, the token keeps its local signal but misses the context.
- `NO_RESIDUAL_BLOCK_ACC=0.500`: without the residual path, the context arrives but the local signal is lost.
- `ATTENTION_RESIDUAL_FFN_ACC=1.000`: attention plus residual gives both facts to the position-wise classifier.
