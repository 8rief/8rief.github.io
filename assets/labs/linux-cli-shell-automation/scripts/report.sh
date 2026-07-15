#!/usr/bin/env bash
set -euo pipefail

if (($# != 2)); then
  printf 'usage: %s LOG_DIR REPORT_DIR\n' "$0" >&2
  exit 2
fi

log_dir=$1
report_dir=$2
mkdir -p "$report_dir"

mapfile -d '' logs < <(find "$log_dir" -type f -name '*.log' -print0 | sort -z)
if ((${#logs[@]} == 0)); then
  printf 'no .log files found under %s\n' "$log_dir" >&2
  exit 1
fi

all_log="$report_dir/all.log"
cat "${logs[@]}" > "$all_log"

total_requests=$(wc -l < "$all_log" | tr -d ' ')
error_requests=$(grep -c ' level=ERROR ' "$all_log" || true)
slow_requests=$(awk '{ for (i=1; i<=NF; i++) { split($i, kv, "="); if (kv[1] == "latency_ms" && kv[2] + 0 >= 400) count++ } } END { print count + 0 }' "$all_log")

awk '
{
  delete f
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    f[kv[1]] = kv[2]
  }
  status[f["status"]]++
}
END {
  for (s in status) print s "\t" status[s]
}
' "$all_log" | sort -k2,2nr -k1,1 > "$report_dir/status_counts.tsv"

awk '
{
  delete f
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    f[kv[1]] = kv[2]
  }
  path = f["path"]
  latency[path] += f["latency_ms"] + 0
  count[path]++
}
END {
  for (p in count) printf "%s\t%.1f\t%d\n", p, latency[p] / count[p], count[p]
}
' "$all_log" | sort -k2,2nr -k1,1 > "$report_dir/path_latency.tsv"

awk '
{
  delete f
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    f[kv[1]] = kv[2]
  }
  counts[f["service"] "\t" f["level"]]++
}
END {
  for (key in counts) print key "\t" counts[key]
}
' "$all_log" | sort -k1,1 -k2,2 > "$report_dir/service_level_counts.tsv"

awk '
{
  delete f
  for (i = 1; i <= NF; i++) {
    split($i, kv, "=")
    f[kv[1]] = kv[2]
  }
  if (f["latency_ms"] + 0 >= 400) print
}
' "$all_log" > "$report_dir/slow_requests.log"

top_status=$(head -n 1 "$report_dir/status_counts.tsv")
{
  printf 'total_requests=%s\n' "$total_requests"
  printf 'error_requests=%s\n' "$error_requests"
  printf 'slow_requests_ge_400ms=%s\n' "$slow_requests"
  printf 'top_status=%s\n' "$top_status"
  printf 'source_files=%s\n' "${#logs[@]}"
} > "$report_dir/summary.txt"

printf 'summary written to %s\n' "$report_dir/summary.txt"
