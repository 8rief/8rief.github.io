#!/usr/bin/env python3
from __future__ import annotations
import json, math, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; REPORTS=ROOT/'reports'; REPORTS.mkdir(exist_ok=True)
DOCS={
'cuda-memory':'CUDA为什么不一定快：CUDA性能问题常常来自访存模式、同步和数据传输，而不只是算术数量。',
'lora':'LoRA为什么省显存：LoRA冻结基座模型，只训练低秩适配矩阵，适合改变稳定行为和格式。',
'qlora':'QLoRA把基座模型量化到4 bit，再训练adapter，用更低显存做参数高效微调。',
'rag':'什么时候用RAG而不是微调：RAG把可变知识放在检索系统里，适合文档问答和事实更新。',
'agent':'本地agent由检索、工具、模型、状态、校验和失败回放组成。',
'eval':'agent评估要看什么：模型或agent效果必须和baseline比较，并记录错误类型。',
}
QUERIES={
'什么时候用RAG而不是微调':'rag',
'LoRA为什么省显存':'lora',
'CUDA为什么不一定快':'cuda-memory',
'agent评估要看什么':'eval',
}

def tok(s):
    words = re.findall(r'[a-z0-9_]+', s.lower())
    chars = [ch for ch in s if '\u4e00' <= ch <= '\u9fff']
    bigrams = [''.join(chars[i:i+2]) for i in range(max(0, len(chars)-1))]
    return words + chars + bigrams
def score(q,d):
    qc=Counter(tok(q)); dc=Counter(tok(d))
    return sum(qc[t]*dc[t] for t in qc)
def retrieve(q):
    ranked=sorted(((score(q,d),k,d) for k,d in DOCS.items()), reverse=True)
    return ranked[0]
rag_correct=0; rows=[]
for q,expected in QUERIES.items():
    sc,k,d=retrieve(q); ok=k==expected; rag_correct+=ok
    rows.append({"query":q,"expected":expected,"retrieved":k,"score":sc,"ok":ok})
# parameter budget formulas, not measured training
models=[('0.6B',0.6e9),('1.7B',1.7e9),('4B',4e9),('7B',7e9)]
budgets=[]
for name,params in models:
    fp16_gb=params*2/1024**3
    int4_gb=params*0.5/1024**3
    budgets.append({"model":name,"fp16_params_gb":round(fp16_gb,2),"int4_params_gb":round(int4_gb,2),"local_12gb_note":"comfortable" if fp16_gb<5 else ("qlora_candidate" if int4_gb<5 else "stretch")})
# toy tool schema validation
calls=[{"tool":"search_notes","arguments":{"query":"LoRA"}},{"tool":"run_eval","arguments":{"case_id":"rag-vs-lora"}},{"tool":"delete_file","arguments":{"path":"/tmp/x"}}]
allowed={"search_notes":{"query"},"run_eval":{"case_id"}}
validated=[]
for c in calls:
    ok=c.get('tool') in allowed and set(c.get('arguments',{}))==allowed.get(c.get('tool'),set())
    validated.append({**c,"schema_ok":ok})
report={"retrieval_rows":rows,"rag_accuracy":rag_correct/len(QUERIES),"model_memory_budget":budgets,"tool_calls":validated,"baseline_rule":"base-model-only, RAG, and LoRA/RAG-agent must be compared before claiming improvement"}
(REPORTS/'local_model_agent_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
md=["# Local model and agent lab report","","## Retrieval baseline","","| query | expected | retrieved | ok |","| --- | --- | --- | --- |"]
for r in rows: md.append(f"| {r['query']} | {r['expected']} | {r['retrieved']} | {r['ok']} |")
md += ["", f"RAG retrieval accuracy on the toy set: `{report['rag_accuracy']:.2f}`.", "", "## Model memory budget", "", "| model | fp16 params GB | int4 params GB | 12GB note |", "| --- | --- | --- | --- |"]
for b in budgets: md.append(f"| {b['model']} | {b['fp16_params_gb']} | {b['int4_params_gb']} | {b['local_12gb_note']} |")
md += ["", "## Tool schema", "", "| tool | schema ok |", "| --- | --- |"]
for c in validated: md.append(f"| {c['tool']} | {c['schema_ok']} |")
(REPORTS/'local_model_agent_report.md').write_text('\n'.join(md))
print('local_model_agent_ok', report['rag_accuracy'], len(budgets), sum(c['schema_ok'] for c in validated))
