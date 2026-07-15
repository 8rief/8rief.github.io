#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CUDA_VERSION="${CUDA_VERSION:-13.2.1}"
CUDA_DRIVER_TAG="${CUDA_DRIVER_TAG:-595.58.03}"
CUDA_RUNFILE="cuda_${CUDA_VERSION}_${CUDA_DRIVER_TAG}_linux.run"
CUDA_URL="${CUDA_URL:-https://developer.download.nvidia.com/compute/cuda/${CUDA_VERSION}/local_installers/${CUDA_RUNFILE}}"
EXPECTED_MD5="${CUDA_RUNFILE_MD5:-e5b4bdf19cc27d63a8254cb486764626}"
INSTALL_DIR="${CUDA_TOOLKIT_PATH:-$HOME/.local/cuda-${CUDA_VERSION}}"
CACHE_DIR="${CUDA_RUNFILE_CACHE:-$HOME/.cache/nvidia-cuda-runfiles}"
TMP_DIR="$CACHE_DIR/tmp"
RUNFILE_PATH="$CACHE_DIR/$CUDA_RUNFILE"
mkdir -p "$CACHE_DIR" "$TMP_DIR" "$INSTALL_DIR" "$ROOT/.tools"

printf 'setup_cuda_runfile_user\n'
printf 'cuda_url=%s\n' "$CUDA_URL"
printf 'install_dir=%s\n' "$INSTALL_DIR"
printf 'cache_dir=%s\n' "$CACHE_DIR"

if [[ -f "$CUDA_URL" ]]; then
  cp "$CUDA_URL" "$RUNFILE_PATH"
else
  if ! command -v wget >/dev/null 2>&1; then
    echo 'wget not found; install wget or set CUDA_URL to an existing local runfile path.' >&2
    exit 2
  fi
  wget -c -O "$RUNFILE_PATH" "$CUDA_URL"
fi
actual_md5="$(md5sum "$RUNFILE_PATH" | awk '{print $1}')"
printf 'runfile_md5=%s\n' "$actual_md5"
if [[ "$actual_md5" != "$EXPECTED_MD5" ]]; then
  echo "MD5 mismatch for $RUNFILE_PATH" >&2
  exit 3
fi
chmod +x "$RUNFILE_PATH"

# Important for WSL: install toolkit only. Do not install a Linux NVIDIA driver.
"$RUNFILE_PATH" --nox11 --silent --toolkit --toolkitpath="$INSTALL_DIR" --no-man-page --override --tmpdir="$TMP_DIR"

cat > "$ROOT/.tools/cuda-env.sh" <<EOF_ENV
export CUDA_HOME="$INSTALL_DIR"
export PATH="\$CUDA_HOME/bin:\$PATH"
export LD_LIBRARY_PATH="\$CUDA_HOME/lib64:/usr/lib/wsl/lib:\${LD_LIBRARY_PATH:-}"
export CUDA_ARCH_FLAGS="\${CUDA_ARCH_FLAGS:--arch=native}"
EOF_ENV

"$INSTALL_DIR/bin/nvcc" --version
printf 'CUDA_ENV_READY=%s\n' "$ROOT/.tools/cuda-env.sh"
printf 'NEXT=source .tools/cuda-env.sh && bash run_lab.sh\n'
