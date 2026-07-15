# project-http-api-contract-boundary

配套文章：**项目 HTTP/API 契约第一课：method、status、JSON 和幂等边界怎么定**。

这个 lab 用 Python 标准库实现一个本地 task API，用可检查证据呈现 HTTP API 最容易混乱的边界：method、path、status code、JSON 请求/响应、错误结构、`Location`、`X-Request-Id`、`Idempotency-Key` 和重复请求行为。

## 运行

```bash
cd ~/8rief.github.io/assets/labs/project-http-api-contract-boundary
bash run_lab.sh
```

## 你会看到什么

成功时会打印：

```text
HEALTH_STATUS=200
VALIDATION_STATUS=400
CREATE_STATUS=201
CREATED_LOCATION=/tasks/tsk-001
REPLAY_SAME_ID=yes
CONFLICT_STATUS=409
PUT_REPEAT_CHANGED=no
NOT_FOUND_STATUS=404
REQUEST_IDS_PRESENT=yes
RUN_STATUS=ok
http_api_contract_lab_status=ok
```

## 生成文件

- `reports/api_events.jsonl`：每个 HTTP 请求/响应的观察记录。
- `reports/api_contract_probe.json`：机器可读的契约摘要。
- `reports/api_contract_report.md`：学习者可读的报告。

这些报告是本地运行结果，不提交到公开仓库。
