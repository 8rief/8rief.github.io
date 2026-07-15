# Deep learning Transformer position and mask lab

This lab explains two Transformer support mechanisms with pure Python: positional information and causal masks. It does not require NumPy, PyTorch or a GPU.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
ORDER_TEST_SAMPLES=8
FUTURE_TEST_SAMPLES=8
POSITION_BAG_BASELINE_ACC=0.500
NO_POSITION_ATTENTION_ACC=0.500
POSITIONAL_ATTENTION_ACC=1.000
POSITION_GAIN_OVER_BEST_BASELINE=0.500
POSITION_MIN_TOP_WEIGHT=0.944
POSITION_TOP_MATCHES_QUERY=yes
UNMASKED_FUTURE_LOOKUP_ACC=1.000
CAUSAL_MASKED_LOOKUP_ACC=0.500
MASK_BLOCKS_FUTURE=yes
RUN_STATUS=ok
deep_learning_transformer_position_mask_lab_status=ok
```

## What the experiment does

The lab has two probes.

1. Position probe: sequences `AB` and `BA` contain the same token bag, but the label asks for the token at position 0. A bag baseline and an attention variant without position both stay at 50%; positional attention selects slot 0 and reaches 100%.
2. Mask probe: a query at index 1 tries to read the token at index 2. Unmasked future lookup reaches 100% by leaking the answer. A causal mask blocks that future slot, sets its attention weight to zero, and the remaining context stays at 50%.

Generated reports live under `reports/` after you run the lab:

- `position_mask_probe.json`: machine-readable metrics and traces.
- `position_mask_report.md`: method comparison and interpretation.
- `order_trace_table.csv`: position-task predictions and attention weights.
- `future_trace_table.csv`: mask-task predictions and future weights.

`reports/` is generated evidence and is not committed to the public package.

## Boundary

The vectors in this lab are hand-built and the masks are deterministic. A real Transformer learns embeddings and projections, combines multi-head attention with feed-forward networks, residual connections and normalization, and trains on a task loss. This lab proves two support mechanisms: attention needs position information for order-sensitive tasks, and causal masks prevent invalid future reads.
