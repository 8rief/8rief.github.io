---
layout: post
title: "项目数据目录、临时文件与原子写入：怎样让失败重跑不破坏结果"
date: 2026-03-18 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用可复现失败实验讲清 source/config/input/cache/temp/output 边界、same-directory temp、fsync、os.replace、幂等重跑和 artifact manifest。"
tags: [filesystem, atomic-write, idempotence, python, software-engineering, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-data-temp-atomic-write-boundary/README.md`](/assets/labs/project-data-temp-atomic-write-boundary/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
很多项目脚本在最后一步直接打开 `output/report.json` 写结果。正常运行时看不出问题；一旦进程在写到一半时异常退出，旧报告已经被截断，新报告又不完整。下一次运行还可能把这个半成品当成合法缓存继续处理，最终很难判断哪一份结果可信。

这篇文章从一个可观察的失败开始：输出目录里先放一份旧结果，程序生成新结果后在发布前被强制终止。正确设计应同时满足三个条件：旧结果保持逐字节不变，候选临时文件被清理，进程返回非0。随后用相同输入成功运行两次，两次输出和manifest都必须字节一致。

## 学习目标

完成本文后，你应该能够：

1. 区分source、config、input、cache、temp和output六类目录的职责。
2. 解释直接覆盖输出为什么会暴露半写文件。
3. 实现“同目录临时文件→flush/fsync→`os.replace`→目录fsync”的发布流程。
4. 用失败注入证明旧结果不会被候选文件覆盖。
5. 用SHA-256和artifact manifest追踪输入、配置与输出的对应关系。
6. 判断原子替换、幂等重跑、多文件事务和并发写入之间的边界。

## 先修知识与实验目录

你需要会运行Linux命令、读取JSON，并知道进程可能以非0状态退出。本文使用Python标准库，不需要第三方依赖。

实验目录可以组织成：

```text
project-data-temp-atomic-write-boundary/
├── config/
│   └── pipeline.json
├── fixtures/
│   └── orders.jsonl
├── src/
│   └── artifact_pipeline.py
├── scripts/
│   └── data_boundary_probe.py
├── tests/
│   └── test_artifact_pipeline.py
├── reports/
└── run_lab.sh
```

运行时工作目录位于Linux临时文件系统下，包含`input/`、`config/`、`cache/`、`temp/`和`output/`。实验只删除自己创建的目录，不修改home目录中的真实项目数据。

## 为什么需要数据目录与发布边界

一个文件的目录位置应该说明它能否重建、是否允许删除、由谁写入以及失败后如何恢复。把所有内容都放在项目根目录，会让清理脚本和重跑逻辑失去判断依据。

本文使用下面的目录模型：

| 目录角色 | 典型内容 | 可否删除 | 谁写入 |
| --- | --- | --- | --- |
| source | 源码、测试、schema | 受版本控制保护 | 开发者或构建系统 |
| config | 可公开配置 | 有来源时可恢复 | 操作者或部署系统 |
| input | 原始输入、fixture | 默认只读 | 上游系统 |
| cache | 可重新计算的加速数据 | 可以 | 程序 |
| temp | 尚未发布的中间状态 | 失败后应清理 | 程序 |
| output | 对外可消费的完成结果 | 由发布规则替换 | 程序 |

两个判断最关键：cache删除后不应改变最终语义；output只有在完整验证通过后才更新。temp中的文件即使内容完整，也不能被下游当成已发布结果。

## 核心模型：prepare、validate、publish

可靠写入可以拆成三段：

```text
prepare
  读取input与config
  计算内存中的结果
  序列化为完整bytes
        ↓
validate
  校验schema、数量、哈希和业务不变量
        ↓
publish
  在目标目录创建临时文件
  写完整bytes并flush/fsync
  原子替换目标路径
  fsync目标目录
```

prepare阶段失败时，output完全不动。validate阶段失败时，候选bytes不会发布。publish阶段的关键切换点是rename/replace：目标名字在切换前指向旧文件，切换后指向完整新文件。

## 第一步：固定输入、配置和确定性输出

实验输入有4条订单：

```json
{"order_id":"A100","status":"paid","amount_cents":1200}
{"order_id":"A101","status":"pending","amount_cents":800}
{"order_id":"A102","status":"paid","amount_cents":2500}
{"order_id":"A103","status":"refunded","amount_cents":500}
```

配置只统计`paid`和`pending`：

```json
{
  "currency": "CNY",
  "include_statuses": ["paid", "pending"]
}
```

程序先验证UTF-8、JSON结构、字段集合、重复`order_id`和非负整数金额，再得到：

```json
{
  "count_by_status": {"paid": 2, "pending": 1},
  "currency": "CNY",
  "included_statuses": ["paid", "pending"],
  "schema_version": 1,
  "selected_order_count": 3,
  "total_amount_cents": 4500
}
```

为了让相同输入产生相同bytes，序列化时固定键顺序、分隔符、UTF-8和末尾换行：

```python
def canonical_json_bytes(value):
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")
```

若输出包含当前时间、随机ID或无序集合，相同输入的哈希就会变化。需要时间信息时，应把它放进单独的运行日志，或明确把时间视为输入的一部分。

## 第二步：看清直接覆盖的失败窗口

下面的写法会先截断旧文件：

```python
with output_path.open("w", encoding="utf-8") as handle:
    handle.write(first_half)
    raise RuntimeError("process stopped")
    handle.write(second_half)
```

异常发生后，`output_path`仍然存在，但只包含前半段。路径存在检查会错误地把它当成结果；JSON解析失败只能说明文件损坏，无法恢复刚刚被截断的旧版本。

“先删旧文件，再写新文件”会把失败窗口扩大为目标路径完全不存在。“先备份，再直接写”可以恢复，但写入过程仍需额外状态管理。最短正确路径是先把完整候选写到另一个文件，最后只切换目录项。

## 第三步：临时文件为什么要放在目标目录

原子替换依赖rename语义。候选文件应创建在目标文件的同一目录：

```python
with tempfile.NamedTemporaryFile(
    mode="wb",
    dir=output_path.parent,
    prefix=f".{output_path.name}.",
    suffix=".tmp",
    delete=False,
) as handle:
    temporary_path = Path(handle.name)
```

这样候选文件与目标文件处于同一文件系统。若候选放在系统`/tmp`、目标放在另一个挂载点，rename可能返回`EXDEV`，程序只能退化成copy+delete；copy过程会重新暴露半写窗口。

项目仍可以保留独立`temp/`目录保存普通中间数据，但“准备替换某个目标文件的最终候选”应和目标放在同一目录。以点开头的临时文件也更容易从正常artifact列表中排除。

## 第四步：完整写入、同步并原子替换

核心实现如下：

```python
def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temporary_path, path)
        temporary_path = None
        fsync_directory(path.parent)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
```

每一步解决不同问题：

1. `write`把完整bytes送入文件对象。
2. `flush`把Python用户态buffer交给操作系统。
3. `os.fsync`请求把候选文件数据同步到存储设备。
4. `os.replace`在同一文件系统中把目标名字切换到候选文件；目标已存在时也会替换。
5. 目录fsync用于提高目录项更新在掉电后的持久性。
6. `finally`清理尚未发布的候选文件。

原子可见性和持久性是两个问题。rename让其他进程看到旧文件或新文件，避免看到半个新文件；fsync用于降低系统崩溃后丢失已确认写入的风险。具体保证仍取决于操作系统、文件系统、挂载参数和存储硬件。

## 第五步：用失败注入证明旧结果被保留

实验先写入：

```json
{"sentinel":"old-output"}
```

旧文件SHA-256是：

```text
3ba0392fd4cc40904b6bfdf37d7743ce6c70a11ceaf26b8210e9b80ba68e5728
```

随后在候选文件完成`write+fsync`后、`os.replace`前强制抛出异常。进程结果：

```text
FAILED_WRITE_RC=70
OUTPUT_PRESERVED_AFTER_FAILURE=yes
TEMP_FILES_AFTER_FAILURE=0
```

这三个观察共同构成证据：非0退出表示发布没有完成；旧文件bytes和哈希保持不变；`finally`删除了候选临时文件。只检查返回码不能证明旧结果未被破坏，只检查旧文件存在也不能证明内容未变化。

## 第六步：成功发布与manifest

成功运行后输出SHA-256为：

```text
9d9c6895f1e2aeb846364f2fbd5dd71bb88c90db28fd8900db701c7ad4d49ff9
```

manifest记录输入、配置和输出的关系：

```json
{
  "config_sha256": "4c74f0e8a4e7dce868dcf730ee4e79950671189c1f5f01e0138411e53ad5499d",
  "input_sha256": "c3c0edb6bf7f083acc8a488884f623b76bd26af6a0d7c70e34b74318ce95270a",
  "output_bytes": 169,
  "output_sha256": "9d9c6895f1e2aeb846364f2fbd5dd71bb88c90db28fd8900db701c7ad4d49ff9",
  "schema_version": 1,
  "selected_order_count": 3
}
```

消费者可以重新计算output hash并和manifest比较。input/config hash则回答“这份报告由哪组bytes生成”。哈希可以检测意外变化，但不能证明发布者身份；需要防伪时还要签名或受信任的artifact store。

本文先发布output，再发布manifest。因此manifest写入失败时，output可能已经更新。这个顺序适合“output自身完整可用，manifest是附加证据”的场景。若两者必须同时出现，就需要把整个版本写入新目录，再原子切换`current`指针，或者使用数据库/事务型存储。

## 第七步：cache删除后结果仍应一致

第一次成功后，probe删除整个`cache/`目录，再用相同input和config运行。结果为：

```text
RERUN_BYTE_IDENTICAL=yes
MANIFEST_OUTPUT_HASH_MATCH=yes
```

这验证了两个契约：cache只影响速度，不影响语义；同一输入重跑产生相同输出和manifest bytes。若删除cache后结果变化，cache实际上保存了未声明输入，目录命名与真实依赖不一致。

幂等重跑不要求每次都保留同一个inode，也不要求运行时间一致。它要求相同显式输入得到相同可观察结果，并且重复发布不会累积重复行、重复扣款或随机文件名。

## 完整复现实验

运行：

```bash
./run_lab.sh
```

本次输出：

```text
DIRECTORY_MODEL=source,config,input,cache,temp,output
FAILED_WRITE_RC=70
OUTPUT_PRESERVED_AFTER_FAILURE=yes
TEMP_FILES_AFTER_FAILURE=0
PUBLISHED_OUTPUT_SHA256=9d9c6895f1e2aeb846364f2fbd5dd71bb88c90db28fd8900db701c7ad4d49ff9
RERUN_BYTE_IDENTICAL=yes
MANIFEST_OUTPUT_HASH_MATCH=yes
RUN_STATUS=ok
```

实验保留：

```text
data_boundary_probe.json
artifact_manifest.json
transcript.md
atomic_write_summary.md
run_lab_output.txt
```

单元测试覆盖确定性summary、失败前旧结果保护、临时文件清理、成功重跑一致、manifest hash和非法输入边界。process-level probe再检查真实CLI返回码、stdout/stderr和文件系统状态。

## 常见错误与定位方式

1. **直接以写模式打开正式output。** 文件会先被截断；改成完整候选文件加原子替换。
2. **候选文件放在另一个文件系统。** rename可能得到`EXDEV`；在目标目录创建候选。
3. **只调用`flush`。** 它只处理语言运行时buffer；需要持久性时还要考虑文件和目录fsync。
4. **成功后才写cleanup。** 失败路径会泄露临时文件；使用`try/finally`或shell `trap`。
5. **temp文件名与正式文件相同。** 下游扫描器可能提前消费；使用隐藏前缀和`.tmp`后缀，并只发布固定目标名。
6. **把cache当唯一数据源。** 删除cache后结果变化说明依赖未显式声明。
7. **输出包含当前时间或随机ID。** 相同输入无法字节复现；将易变运行元数据移到日志或显式输入。
8. **manifest记录路径却不记录hash。** 路径可被覆盖；hash才能绑定具体bytes。
9. **认为一个`os.replace`能更新多个文件。** 单文件替换不提供跨文件事务。
10. **多个writer同时发布同一目标。** 每次替换可保持单文件完整，但最后写入者会覆盖前者；需要锁、版本号或compare-and-swap规则。
11. **把SHA-256当数字签名。** 哈希检测变化，不能证明来源。
12. **在网络文件系统上直接套用本地结论。** NFS、SMB、对象存储和同步盘的rename/持久性语义需要单独验证。

## 练习

1. 在直接写正式output的版本中注入异常，观察JSON是否被截断，再替换为本文实现。
2. 把候选文件放到另一个挂载点，捕获`EXDEV`并解释为什么copy fallback失去原子可见性。
3. 给输入增加重复`order_id`，要求程序返回2且output hash保持不变。
4. 给summary增加`generated_at`，观察重跑hash变化；再把它移动到运行日志。
5. 模拟两个并发writer写同一目标，记录最终版本。设计基于文件锁或版本号的冲突规则。
6. 将output和manifest写入`versions/<hash>/`，再用一个原子更新的`current`文件指向完整版本，解决多文件一致性问题。
7. 写一个清理命令：只删除超过一天的隐藏`.tmp`文件，不能删除正式output、input或config；先实现`--dry-run`。

## 边界

本文验证的是Linux本地文件系统上的单文件发布。它不代替数据库事务、对象存储条件写、分布式锁、备份、权限控制或灾难恢复。`os.replace`保证的原子可见性范围、fsync的持久性和掉电行为仍需结合具体文件系统文档与故障测试。

原子写也不能修复错误计算。程序仍要在publish前校验schema、业务不变量和输出hash。旧文件完整只说明发布机制没有产生半写状态，不说明旧结果本身正确。

## 参考资料

- Python官方文档：[tempfile — Generate temporary files and directories](https://docs.python.org/3/library/tempfile.html)
- Python官方文档：[os.replace](https://docs.python.org/3/library/os.html#os.replace)
- Python官方文档：[os.fsync](https://docs.python.org/3/library/os.html#os.fsync)
- Python官方文档：[hashlib — Secure hashes and message digests](https://docs.python.org/3/library/hashlib.html)
- POSIX Issue 8：[rename](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)
- Linux man-pages：[rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)

{% endraw %}
