#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REPORTS=ROOT/'reports'; REPORTS.mkdir(exist_ok=True)

def count_nq(n:int, cur=0,left=0,right=0)->int:
    full=(1<<n)-1
    if cur==full: return 1
    valid=full & ~(cur|left|right)
    total=0
    while valid:
        p=valid & -valid
        valid-=p
        total+=count_nq(n, cur|p, (left|p)<<1, (right|p)>>1)
    return total

def subproblems(n:int, rows:int, cur=0,left=0,right=0):
    full=(1<<n)-1
    if rows==0:
        valid=full & ~(cur|left|right)
        return [(cur,left,right, valid.bit_count())]
    out=[]; valid=full & ~(cur|left|right)
    while valid:
        p=valid & -valid; valid-=p
        out.extend(subproblems(n, rows-1, cur|p, (left|p)<<1, (right|p)>>1))
    return out

def workload_estimate(n:int, state):
    cur,left,right,_=state
    full=(1<<n)-1
    valid=full & ~(cur|left|right)
    return valid.bit_count() + (n - cur.bit_count())
counts={n:count_nq(n) for n in range(4,9)}
subs=subproblems(8,3)
work=[workload_estimate(8,s) for s in subs]
# greedy dynamic fetching simulation: next available worker gets next task cost
workers=[0,0,0,0]
for cost in sorted(work, reverse=True):
    i=min(range(len(workers)), key=workers.__getitem__)
    workers[i]+=cost
static=[sum(work[i::4]) for i in range(4)]
report={"counts":counts,"n8_rows3_subproblems":len(subs),"work_min":min(work),"work_max":max(work),"work_sum":sum(work),"static_worker_loads":static,"dynamic_greedy_loads":workers,"imbalance_static":max(static)-min(static),"imbalance_dynamic":max(workers)-min(workers)}
(REPORTS/'nqueens_bridge_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
md=["# N-Queens bridge lab report","","## Known small counts","","| N | solutions |","| --- | --- |"]
for n,c in counts.items(): md.append(f"| {n} | {c} |")
md += ["", "## Subproblem split", "", f"N=8 after preplacing 3 rows -> `{len(subs)}` subproblems.", f"Estimated work min/max/sum: `{min(work)}/{max(work)}/{sum(work)}`.", "", "| schedule | worker loads | imbalance |", "| --- | --- | --- |", f"| static round-robin | `{static}` | `{report['imbalance_static']}` |", f"| dynamic greedy simulation | `{workers}` | `{report['imbalance_dynamic']}` |", "", "The simulation is not a GPU benchmark; it shows why irregular search needs dynamic work fetching."]
(REPORTS/'nqueens_bridge_report.md').write_text('\n'.join(md))
print('nqueens_bridge_ok', counts[8], len(subs), report['imbalance_static'], report['imbalance_dynamic'])
