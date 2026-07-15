#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
.venv/bin/python -m pip install -r requirements-gpu.txt

.venv/bin/python - <<'PY'
import torch, transformers, peft
print("torch", torch.__version__)
print("transformers", transformers.__version__)
print("peft", peft.__version__)
print("cuda_available", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise SystemExit("CUDA is required for steps 08 and 09; CPU steps 00--07 remain available.")
print("device", torch.cuda.get_device_name(0))
print("AGENT_GPU_SETUP_OK")
PY
