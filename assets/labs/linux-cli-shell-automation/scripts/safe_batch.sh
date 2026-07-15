#!/usr/bin/env bash
set -euo pipefail

if (($# != 2)); then
  printf 'usage: %s LOG_DIR OUT_TSV\n' "$0" >&2
  exit 2
fi

log_dir=$1
out_tsv=$2
mkdir -p "$(dirname "$out_tsv")"
printf 'file\tlines\terrors\n' > "$out_tsv"

while IFS= read -r -d '' file; do
  lines=$(wc -l < "$file" | tr -d ' ')
  errors=$(grep -c ' level=ERROR ' "$file" || true)
  printf '%s\t%s\t%s\n' "$(basename "$file")" "$lines" "$errors" >> "$out_tsv"
done < <(find "$log_dir" -type f -name '*.log' -print0 | sort -z)

printf 'batch summary written to %s\n' "$out_tsv"
