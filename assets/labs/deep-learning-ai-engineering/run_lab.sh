#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p reports data models
TRANSCRIPT="reports/transcript.txt"
exec > >(tee "$TRANSCRIPT") 2>&1

echo "lab=deep-learning-ai-engineering"
echo "pwd=$ROOT"
echo "python_version=$(python3 --version)"
python3 - <<'PY'
import numpy as np
print(f"numpy_version={np.__version__}")
PY

echo
echo "syntax checks"
python3 -m py_compile scripts/train.py scripts/test_train.py

echo
echo "run training demo"
rm -f reports/metrics.json reports/linear-history.csv reports/mlp-history.csv reports/training_curve.svg reports/report.md models/mlp-weights.npz models/model-card.md
python3 scripts/train.py --root "$ROOT"

echo
echo "metrics summary"
python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('reports/metrics.json').read_text())
print(json.dumps({
  'majority_test_acc': m['majority']['test']['accuracy'],
  'linear_test_acc': m['linear']['test']['accuracy'],
  'mlp_test_acc': m['mlp']['test']['accuracy'],
  'mlp_minus_linear_test_acc': m['comparison']['mlp_minus_linear_test_acc'],
  'gradient_max_relative_error': m['gradient_check']['max_relative_error'],
}, indent=2, sort_keys=True))
PY

echo
echo "run tests"
python3 -m unittest discover -s scripts -p 'test_*.py'

echo
echo "visible result markers"
echo "metrics_ready=reports/metrics.json"
echo "chart_ready=reports/training_curve.svg"
echo "checkpoint_ready=models/mlp-weights.npz"
echo "model_card_ready=models/model-card.md"
echo "deep_learning_ai_status=ok"
