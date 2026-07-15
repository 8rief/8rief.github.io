# Deep learning attention key-value lookup lab

This lab explains the first attention mechanism without depending on NumPy, PyTorch or a GPU. It uses pure Python to show how a query can match keys and read the associated values instead of compressing all history into one fixed summary.

## Run

```bash
./run_lab.sh
```

Expected stable markers:

```text
TRAIN_SAMPLES=32
TEST_SAMPLES=32
MEMORY_SLOTS=4
KEY_DIM=4
VALUE_DIM=4
MAJORITY_BASELINE_ACC=0.250
LAST_VALUE_ACC=0.250
BAG_OF_VALUES_ACC=0.250
FIXED_SUMMARY_ACC=0.250
ATTENTION_LOOKUP_ACC=1.000
ATTENTION_GAIN_OVER_BEST_BASELINE=0.750
ATTENTION_MIN_TOP_WEIGHT=0.711
TOP_KEYS_MATCH_QUERY=yes
RUN_STATUS=ok
deep_learning_attention_lab_status=ok
```

## What the experiment does

Each sample contains four memory slots such as:

```text
red:apple blue:coin green:leaf gold:sky | query=blue | label=coin
```

Every sample has the same four keys and the same four values. Only the key-value pairing changes. A majority rule, the final memory value, a bag of values and an averaged fixed summary cannot recover the binding between the queried key and its value. Scaled dot-product attention compares the query vector with each key vector, turns the scores into weights with softmax, and reads a weighted sum of value vectors.

Generated reports live under `reports/` after you run the lab:

- `attention_probe.json`: machine-readable metrics and per-sample traces.
- `attention_report.md`: method comparison and interpretation.
- `trace_table.csv`: query, slots, predictions and attention weights for each test sample.

`reports/` is generated evidence and is not committed to the public package.

## Boundary

The vectors in this lab are hand-built one-hot vectors. A real Transformer learns embeddings and projection matrices, uses multiple heads, adds position information and trains with a task loss. This lab proves one mechanism: query-key-value attention can retrieve information from a specific earlier position when fixed summaries lose the key-value binding.
