---
layout: post
title: "项目测试金字塔与回归用例边界：失败应该由哪一层测试抓住"
date: 2026-03-21 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个 CSV 到 JSON 报告的小项目，把 unit、integration、smoke 和 golden regression 测试放到同一条证据链里。"
tags: [testing, unittest, regression, golden-file, smoke-test, integration-test, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-test-pyramid-regression-boundary/README.md`](/assets/labs/project-test-pyramid-regression-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}

前面的项目文章已经讲过配置、日志、原子写入、并发写、重试、队列、服务生命周期和运行时指标。到这里，一个新问题会变得很具体：改了一行代码以后，应该跑哪些测试？

很多初学者会在两个极端之间摇摆。一种做法是只跑整个程序，失败时不知道哪一层坏了；另一种做法是给每个函数都写很多测试，但真正的文件格式、命令行参数、输出 JSON、日志和回归结果没有被验收。测试金字塔用来解决一个核心问题：让每类失败落到合适的证据层，并把测试成本花在最能定位问题的位置。


## 为什么需要测试分层

测试分层的核心问题是：同一次代码修改会影响纯计算规则、文件边界、命令行入口和公开输出契约。把所有检查都放在一个大测试里，失败定位会很慢；把所有检查都拆成局部函数测试，真实用户路径又缺少证据。测试金字塔把这些风险拆开，让快速测试负责局部规则，让边界测试负责真实连接，让少量入口测试负责主路径可用，让回归测试负责已经承诺的输出不被无意改变。

这篇文章用一个很小的订单报表项目说明四层边界：

```text
unit test       纯函数规则是否正确
integration     文件、目录、JSONL 日志和输出契约是否连起来
smoke test      命令行程序能否像用户那样跑通
regression      已经约定的输出是否被无意改变
```

## 学习目标

读完并跑完实验后，你应该能做到：

1. 判断一个失败应该用 unit、integration、smoke 还是 regression test 固定。
2. 解释为什么 unit test 很快，但不能证明整个程序可用。
3. 解释为什么 smoke test 能证明主路径存在，但定位能力弱。
4. 用 golden JSON 固定公开输出契约，并知道它不适合滥用到所有中间变量。
5. 为一次 bug 修复选择最小、稳定、可复跑的回归测试。

## 先修知识

你只需要知道：

- CSV 是按行保存的文本表格。
- JSON 是结构化输出格式。
- 命令行程序有退出码、stdout 和 stderr。
- Python 可以用 `unittest` 组织测试。

如果这些还不熟，先看 Linux 脚本错误处理、Python 项目结构、数据处理流水线和项目配置/日志文章。

## 先运行实验

如果你已经克隆过本站仓库：

```bash
cd ~/8rief.github.io
git pull --ff-only
cd assets/labs/project-test-pyramid-regression-boundary
bash run_lab.sh
```

如果还没有克隆：

```bash
cd ~
git clone https://github.com/8rief/8rief.github.io.git
cd 8rief.github.io/assets/labs/project-test-pyramid-regression-boundary
bash run_lab.sh
```

成功时，你会看到类似输出：

```text
unit/integration/smoke tests
Ran 6 tests in ...s
OK

regression probe
UNIT_LAYER=unittest
INTEGRATION_LAYER=file_pipeline
SMOKE_LAYER=cli_subprocess
GOLDEN_REGRESSION_MATCH=yes
SUMMARY_LINE_COUNT=4
SUMMARY_NET_CENTS=14265
SUMMARY_TOP_CUSTOMER=bob
JSONL_EVENT_COUNT=3
BAD_INPUT_RC=65
BAD_OUTPUT_EXISTS=no
RUN_STATUS=ok
```

这段输出有三个意思：

- 6 个 `unittest` 覆盖了纯函数、文件流水线和 CLI 主路径。
- golden regression 证明当前 `summary.json` 和 `fixtures/golden_summary.json` 完全一致。
- 坏输入返回 `65`，并且没有写出 `bad_summary.json`，说明失败路径没有伪造一个看似成功的结果。

## 项目要解决什么问题

实验项目读取 `data/orders.csv`：

```csv
order_id,customer,item,unit_price_cents,quantity,discount_pct
o-001,alice,notebook,500,3,0
o-001,alice,pen,120,5,10
o-002,bob,keyboard,8500,1,15
o-003,alice,mouse,2500,2,0
```

程序把它转换成汇总 JSON：

```json
{
  "gross_cents": 15600,
  "line_count": 4,
  "net_cents": 14265,
  "order_count": 3,
  "rejected_lines": 0,
  "top_customer": "bob",
  "top_customer_net_cents": 7225,
  "total_discount_cents": 1335
}
```

这个项目故意很小，因为测试层的边界要从简单例子看清楚。真实项目可以有数据库、HTTP、队列和模型，但测试判断仍然围绕同一个问题：哪个边界出错，应该由哪一层测试最快、最准地抓住？

## 第一层：unit test 测纯规则

最底层测试只看纯规则，不碰文件系统、不启动子进程、不依赖网络。实验里的 `OrderLine` 有三个规则：

```python
@dataclass(frozen=True)
class OrderLine:
    order_id: str
    customer: str
    item: str
    unit_price_cents: int
    quantity: int
    discount_pct: int

    @property
    def gross_cents(self) -> int:
        return self.unit_price_cents * self.quantity

    @property
    def discount_cents(self) -> int:
        return (self.gross_cents * self.discount_pct + 50) // 100

    @property
    def net_cents(self) -> int:
        return self.gross_cents - self.discount_cents
```

对应测试：

```python
def test_discount_rounds_to_nearest_cent(self):
    line = OrderLine("o-1", "alice", "pen", 99, 3, 10)
    self.assertEqual(line.gross_cents, 297)
    self.assertEqual(line.discount_cents, 30)
    self.assertEqual(line.net_cents, 267)
```

这个测试只回答一个问题：折扣取整规则有没有错。它很快，失败也容易定位。如果有人把 `(gross * discount_pct + 50) // 100` 改成向下取整，这个测试会直接失败。

unit test 的边界也很清楚：它不能证明 CSV 能读，不能证明命令行参数正确，不能证明输出 JSON 文件存在。它只证明一个局部规则。

## 第二层：integration test 测边界组合

集成测试开始连接文件、目录和输出格式。实验里的集成测试用临时目录运行完整 pipeline：

```python
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "summary.json"
    log = Path(tmp) / "events.jsonl"
    summary = run_pipeline(ROOT / "data" / "orders.csv", out, log)
    self.assertEqual(summary["net_cents"], 14265)
    self.assertEqual(summary["top_customer"], "bob")
    self.assertEqual(json.loads(out.read_text())["line_count"], 4)
```

这里检查的是组合边界：

```text
CSV 文件
  -> parse_order_row
  -> summarize_orders
  -> write summary.json
  -> append events.jsonl
```

如果单个函数都对，但路径拼错、输出目录没有创建、JSON key 改名、日志漏写，unit test 可能看不到，integration test 会看到。

为什么用临时目录？因为测试不应该污染项目目录，也不应该依赖上一次运行留下的文件。临时目录让每次测试都从干净状态开始。

## 第三层：smoke test 测用户入口

smoke test 不追求覆盖所有分支，它只确认用户真正调用的入口能跑通。实验里用子进程运行 CLI：

```python
result = subprocess.run(
    [
        sys.executable,
        str(SCRIPT),
        "--input", str(ROOT / "data" / "orders.csv"),
        "--output", str(out),
        "--log", str(log),
        "--golden", str(ROOT / "fixtures" / "golden_summary.json"),
    ],
    text=True,
    capture_output=True,
    check=False,
)
self.assertEqual(result.returncode, 0, result.stderr)
self.assertIn("PIPELINE_OK", result.stdout)
```

这层会发现另一类问题：

- `argparse` 参数名写错。
- 程序入口没有可执行。
- stdout marker 丢失。
- 用户实际命令和内部函数测试不是同一条路径。

smoke test 的定位能力弱。它失败时只能告诉你“主路径不可用”，不能直接告诉你是解析错、计算错、文件错还是 golden mismatch。所以 smoke test 数量通常少，重点是覆盖关键用户路径。

## 第四层：golden regression 固定输出契约

回归测试关注“过去已经确认正确的行为有没有被改坏”。实验用 `fixtures/golden_summary.json` 固定公开输出：

```json
{
  "gross_cents": 15600,
  "line_count": 4,
  "net_cents": 14265,
  "order_count": 3,
  "rejected_lines": 0,
  "top_customer": "bob",
  "top_customer_net_cents": 7225,
  "total_discount_cents": 1335
}
```

比较逻辑很直接：

```python
def compare_golden(actual_path: Path, expected_path: Path) -> tuple[bool, list[str]]:
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    diffs = []
    for key in sorted(set(actual) | set(expected)):
        if actual.get(key) != expected.get(key):
            diffs.append(f"{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}")
    return not diffs, diffs
```

它适合固定公开契约，比如报告字段、排序、总金额、错误码、CLI 输出 marker。它不适合固定所有中间细节。否则每次合理重构都会改一堆 golden 文件，测试就会变成维护负担。

## 失败路径也要测试

只测成功路径会留下一个危险空洞：输入错了，程序可能写出一个看似成功的错误报告。实验故意构造坏输入：

```csv
order_id,customer,item,unit_price_cents,quantity,discount_pct
bad-1,alice,pen,120,0,0
```

`quantity=0` 违反规则。probe 预期：

```text
BAD_INPUT_RC=65
BAD_OUTPUT_EXISTS=no
```

这说明程序用明确退出码报告输入错误，并且没有写出 `bad_summary.json`。这里的重点是失败路径必须可观察、可区分、不会留下误导性产物；`65` 只是这个实验为输入错误选择的稳定约定。

## 怎么选择测试层

可以用下面的判断表：

| 失败类型 | 最合适的第一层测试 | 原因 |
| --- | --- | --- |
| 折扣公式、边界取整、排序 tie-break | unit | 输入小、状态少、定位快 |
| CSV 字段、输出 JSON、JSONL 事件、临时目录 | integration | 涉及多个模块和文件边界 |
| 用户命令、参数名、退出码、stdout marker | smoke | 需要从真实入口观察 |
| 已发布报告字段或历史 bug | regression / golden | 需要防止行为被无意改回去 |
| 浏览器点击、真实数据库、外部服务 | e2e 或受控集成测试 | 只在关键路径使用，成本高 |

一个常见策略是：发现 bug 后先用最容易复现的方式定位，修复前或修复后再把它下沉到最小稳定测试层。如果 bug 是纯函数公式，就写 unit；如果 bug 是 CLI 参数组合，就写 smoke；如果 bug 是输出契约变化，就写 golden regression。

## 把测试金字塔落到失败定位

测试金字塔不是规定 unit 一定最多、e2e 一定最少的图形口号。它真正要求的是：

1. 快速测试覆盖稳定规则。
2. 少量集成测试覆盖真实边界组合。
3. 关键 smoke 测试证明用户入口没有断。
4. 回归测试锁住已经修过或已经发布的行为。
5. 慢测试数量受控，并且失败时有足够日志定位。

如果一个项目只有很多 unit test，却没有任何 CLI/API smoke test，发布时仍然可能发现命令启动不了。如果一个项目只有端到端测试，失败时又会花很多时间定位到一个简单取整规则。两种都不是好结构。

## 常见错误

1. **只测试实现细节。** 测试私有临时变量，会让重构成本很高。优先测试输入输出、错误码和公开契约。
2. **golden 文件太大。** 大型 golden diff 很难审阅。能拆成稳定摘要时，不要固定整份噪声输出。
3. **用 smoke test 代替定位测试。** smoke test 失败后，还需要 unit 或 integration 帮你缩小范围。
4. **测试依赖上一次运行产物。** 测试必须能从干净目录开始。公开 lab 尤其不能靠已提交的 `reports/` 或 runtime state 才能通过。
5. **失败路径不验收。** 程序出错时是否写了半成品、返回了什么退出码、stderr 是否可读，都是工程质量的一部分。

## 练习

1. 把 `discount_pct` 改成 101，写一个 unit test 验证它被拒绝。
2. 给 CSV 增加一个新客户，使 top customer 发生变化。先运行测试观察 golden mismatch，再决定是否更新 golden。
3. 修改 CLI 参数名，比如把 `--output` 改成 `--summary`，观察 smoke test 如何失败。
4. 增加一条集成测试，检查 `events.jsonl` 每行都是合法 JSON 且事件顺序为 `start -> loaded -> summary_written`。
5. 设计一个真实项目里的历史 bug，说明它应该放到 unit、integration、smoke 还是 regression 层。

## 参考资料

- Python documentation: [`unittest`](https://docs.python.org/3/library/unittest.html)
- Python documentation: [`tempfile`](https://docs.python.org/3/library/tempfile.html)
- Python documentation: [`subprocess`](https://docs.python.org/3/library/subprocess.html)
- Martin Fowler: [TestPyramid](https://martinfowler.com/bliki/TestPyramid.html)

{% endraw %}
