#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
rm -rf .venv reports
mkdir -p reports
exec > >(tee reports/transcript.txt) 2>&1

printf '== environment setup ==\n'
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt >/dev/null
export PYTHONPATH="$ROOT/src"
python -m dl_foundations.cli env --output reports/environment.json

printf '\n== tests ==\n'
python -m pytest -q

printf '\n== data summary ==\n'
python -m dl_foundations.cli data-summary --output reports/data_summary.json

printf '\n== tensor demo ==\n'
python -m dl_foundations.cli demo-tensors --output reports/tensor_demo.json
cat reports/tensor_demo.json

printf '\n== autograd demo ==\n'
python -m dl_foundations.cli demo-autograd --output reports/autograd_demo.json
cat reports/autograd_demo.json

printf '\n== majority baseline ==\n'
python -m dl_foundations.cli majority --output-dir reports/majority
cat reports/majority/metrics.json

printf '\n== train linear baseline ==\n'
python -m dl_foundations.cli train --model linear --output-dir reports/linear --epochs 180 --learning-rate 0.03
cat reports/linear/metrics.json

printf '\n== train MLP ==\n'
python -m dl_foundations.cli train --model mlp --output-dir reports/mlp --epochs 240 --learning-rate 0.03
cat reports/mlp/metrics.json

printf '\n== checkpoint load check ==\n'
python -m dl_foundations.cli checkpoint-check --checkpoint reports/mlp/checkpoint.pt --output reports/checkpoint_check.json
cat reports/checkpoint_check.json

printf '\n== comparison ==\n'
python -m dl_foundations.cli compare --majority reports/majority/metrics.json --linear reports/linear/metrics.json --mlp reports/mlp/metrics.json --output reports/comparison.json
cat reports/comparison.json

printf '\n== generated artifacts ==\n'
find reports -maxdepth 3 -type f | sort
printf '\n== done ==\n'
