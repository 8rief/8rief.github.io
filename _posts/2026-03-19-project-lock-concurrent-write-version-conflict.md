---
layout: post
title: "项目锁、并发写入与版本冲突：原子替换为什么仍会丢更新"
date: 2026-03-19 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用真实Linux子进程复现lost update，再实现稳定锁文件、flock临界区、expected_version冲突检测、有界等待和重试。"
tags: [concurrency, file-lock, optimistic-concurrency, lost-update, python, linux, teaching]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/project-lock-concurrent-write-version-conflict/README.md`](/assets/labs/project-lock-concurrent-write-version-conflict/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

{% raw %}
上一篇文章解决了半写文件：先把完整内容写入同目录临时文件，执行`fsync`，最后用`os.replace`原子替换正式路径。这样做保证读者看到旧文件或新文件，不会看到正在写到一半的文件。

然而，文件完整不代表业务更新完整。假设两个进程同时给计数器加一：它们都读到0，各自算出1，再各自原子替换文件。最终JSON始终合法，值却只有1。第二次完整写入覆盖了第一次完整写入，这就是lost update（丢失更新）。

本文用真实Linux子进程构造三组对照实验：无锁写入稳定复现lost update；完整临界区加`flock`后得到2；两个乐观写入者携带相同版本号时，一个成功，另一个收到明确冲突并在重读后完成重试。

## 学习目标

完成本文后，你应该能够：

1. 区分原子可见性、互斥、版本冲突检测和持久化。
2. 画出两个read-modify-write操作产生lost update的时间线。
3. 用独立且稳定的锁文件保护完整临界区。
4. 解释为什么只给`os.replace`加锁，或只先检查一次版本，仍然有竞态。
5. 实现`expected_version`检查、冲突返回码和有界重试。
6. 说明`flock`的协作性、文件系统和分布式边界。

## 先修知识与实验范围

你需要会运行Linux命令，知道进程退出状态，并读得懂少量Python和JSON。实验只用Python标准库，依赖Unix平台提供的`fcntl.flock`；Windows不提供同一个接口。

实验目录如下：

```text
project-lock-concurrent-write-version-conflict/
├── src/
│   └── versioned_counter.py
├── scripts/
│   └── concurrency_probe.py
├── tests/
│   └── test_versioned_counter.py
├── reports/
│   ├── concurrency_probe.json
│   ├── transcript.md
│   └── version_conflict_summary.md
└── run_lab.sh
```

所有竞争都发生在实验创建的临时目录中。本文验证单机Linux上的协作进程，不把结论直接外推到NFS、SMB、多台服务器或对象存储。

## 为什么需要在原子替换之外增加并发控制

先明确目标，才能选择机制。

| 性质 | 要回答的问题 | 本文机制 |
| --- | --- | --- |
| 原子可见性 | 读者会不会看到半个JSON | 同目录临时文件加`os.replace` |
| 互斥 | 是否只有一个进程执行read-modify-publish | 稳定锁文件上的排他`flock` |
| 冲突检测 | 写者依据的旧版本是否仍然有效 | `expected_version == current_version` |
| 持久化 | 系统调用返回后，数据和目录项是否已请求落盘 | 文件`fsync`加目录`fsync` |

它们解决不同故障。`os.replace`使一次发布不可分割，却不会把发布前的读取和计算一起变成事务。`flock`能协调遵守协议的本机进程，却不会自动检查业务版本。`fsync`面向掉电后的持久化，不负责协调并发顺序。

## 状态文件为什么同时保存value和version

实验状态只有三个字段：

```json
{"schema_version":1,"value":0,"version":0}
```

- `schema_version`描述文件格式，便于将来迁移。
- `value`是业务数据。
- `version`每次成功更新都加一，用来判断写者读取后状态是否变化。

在这个计数器中，每次更新恰好让两个字段都加一，所以校验器要求`value == version`。真实项目中的version与业务值通常没有这种相等关系，但version仍应单调变化。

发布函数沿用原子写入流程：

```python
def atomic_write_state(path: Path, state: dict[str, int]) -> None:
    payload = _canonical_bytes(state)
    fd, candidate_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    candidate = Path(candidate_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(candidate, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        candidate.unlink(missing_ok=True)
```

临时文件与正式文件位于同一目录，是为了避免跨文件系统替换。文件`fsync`请求保存内容，替换后的目录`fsync`请求保存路径到新inode的映射。具体掉电语义仍取决于文件系统、挂载方式和存储设备，不能把几行代码解释成对所有介质的绝对保证。

## 无锁实验：两个完整文件仍然丢了一次更新

无锁worker执行四步：

```text
read current state
compute proposed = current + 1
wait until both workers have finished reading
atomically replace state with proposed
```

探针用ready marker强制两个子进程都在任何发布前读到version 0，再让B先发布、A后发布：

```text
时间  worker A                 worker B                 正式文件
t0    read 0                                            0
+t    proposed=1               read 0                   0
+2t                              proposed=1             0
+3t                              replace(value=1)       1
+4t    replace(value=1)                                 1
```

两个`replace`都成功，每个时刻的文件也都是合法JSON。错误发生在业务历史：两次“加一”只留下一个效果。

实验输出为：

```text
UNSAFE_FINAL_VALUE=1
UNSAFE_LOST_UPDATE=yes
STATE_JSON_VALID=yes
```

所以“文件没有损坏”和“更新没有丢失”必须分别验证。

## 悲观方案：锁住完整read-modify-publish临界区

如果冲突频繁、临界区很短，可以先取得排他锁，再读取当前状态、计算并发布：

```text
acquire lock
  read current
  validate
  compute next
  atomic replace
release lock
```

这里的锁路径是`counter.lock`，数据路径是`counter.json`。两者必须分开。

### 为什么不要锁数据文件本身

`flock`作用于打开文件所对应的open file description。原子替换会让路径`counter.json`指向一个新inode：旧进程可能锁着旧inode，新进程打开路径后却拿到新inode。两个进程看似锁了同一路径，实际没有协调同一个锁对象。

稳定的独立锁文件不参与`os.replace`，它的inode在数据文件多次替换后保持不变。单元测试会记录两者inode并验证：锁文件inode不变，数据文件inode变化。

### 有界的FileLock

核心实现使用非阻塞`LOCK_NB`轮询，而不是无限等待：

```python
class FileLock:
    def __enter__(self):
        self._stream = self.path.open("a+b")
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            try:
                fcntl.flock(
                    self._stream.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    self._stream.close()
                    raise LockTimeout("lock acquisition timed out")
                time.sleep(self.poll_seconds)

    def __exit__(self, exc_type, exc, traceback):
        fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
        self._stream.close()
```

使用`time.monotonic()`是因为系统时钟校准不应让超时突然变长或缩短。超时是协议的一部分：调用者能收到确定失败并决定稍后重试、返回503，或把任务放回队列。

### 真实双进程结果

探针同时启动两个locked worker。第一个worker故意在锁内停留100ms，让第二个确实遇到竞争；第二个只能在锁释放后重新读取：

```text
LOCKED_FINAL_VALUE=2
LOCKED_SERIALIZED=yes
```

锁内必须重新读取。若两个worker在加锁前都读取0，即使之后依次进入锁并发布，各自仍会写1，锁只会把两个过期结果排队，并不能修复lost update。

## 乐观方案：让旧版本写入明确失败

悲观锁在整个计算期间阻塞其他写者。若读取和计算很慢、冲突很少，更合适的流程是：

```text
read version N
compute proposed result without holding lock
compare current version with N and publish as one indivisible动作
if conflict: reread, recompute, retry or return conflict
```

实验接口接受`expected_version`：

```python
def compare_and_increment(state_path, lock_path, *, expected_version, timeout_seconds):
    with FileLock(lock_path, timeout_seconds):
        current = read_state(state_path)
        if current["version"] != expected_version:
            raise VersionConflict(
                f"expected {expected_version}, current {current['version']}"
            )
        updated = next_state(current)
        atomic_write_state(state_path, updated)
        return updated
```

短锁保护的是“重新读取当前版本→比较→替换”这段操作。计算可以在锁外进行，临界区因此更短。

### 为什么版本检查本身也要原子化

下面的写法仍然错误：

```python
current = read_state(path)
if current["version"] == expected_version:
    atomic_write_state(path, proposed)
```

两个进程可能同时通过`if`，然后依次替换。版本字段存在，但check与write之间留下了TOCTOU（time-of-check to time-of-use）窗口。

普通文件系统没有直接提供“仅当这个JSON仍是version N时替换”的业务级条件写入。本文用短`flock`构造本地compare-and-swap。数据库事务、对象存储条件请求或HTTP的`If-Match`可以提供各自系统内的原生条件更新；不要先读后写模拟它，再误以为已经原子。

## 把冲突设计为公开结果

两个CAS worker都携带`expected_version=0`。B先进入短临界区并发布version 1，A随后读取到1，不能覆盖，只能以73退出：

```text
CAS_SUCCESS_COUNT=1
CAS_CONFLICT_COUNT=1
CAS_CONFLICT_RC=73
```

返回码73是本实验约定，不是跨系统标准。关键是冲突和锁超时不能都变成含糊的“写文件失败”：

| 结果 | 本实验返回码 | 调用者动作 |
| --- | ---: | --- |
| 更新成功 | 0 | 使用新版本 |
| expected version过期 | 73 | 重读、重算，或把冲突交给用户 |
| 等锁超过上限 | 75 | 退避后重试，或报告服务繁忙 |
| 状态schema损坏 | 非0 | 停止更新，先修复数据 |

探针让冲突worker重新读取version 1，以它为基础重算，再提交一次：

```text
CAS_RETRY_FINAL_VALUE=2
```

重试不能简单重复旧字节。旧proposal基于version 0，再写一次仍可能覆盖新状态；正确重试包含“重读→重新验证→重新计算→条件提交”。

## 重试必须有上限和退避

一个实用循环可以写成：

```python
for attempt in range(max_attempts):
    snapshot = read_state(path)
    proposed = compute(snapshot)
    try:
        return conditional_publish(
            expected_version=snapshot["version"],
            proposed=proposed,
        )
    except VersionConflict:
        time.sleep(backoff(attempt))
raise TooMuchContention
```

还需根据操作语义决定能否自动重试：

- 计数器加一可从新快照重新计算，适合自动重试。
- 用户编辑长文本时，覆盖可能丢掉他人修改，通常应展示冲突并合并。
- 调用支付、发邮件等外部副作用时，重试前还需幂等键；文件版本号本身无法撤销已经发生的外部动作。

本实验只重试一次，是为了清楚展示状态变化，不把“无限重试直到成功”当成正确性保证。

## 锁超时、死锁与锁顺序

探针先启动一个holder持锁400ms，再让另一个进程只等待60ms：

```text
LOCK_TIMEOUT_RC=75
```

有界等待避免进程永久挂起，但不能从根源上消除死锁。项目需要多个锁时，应定义全局顺序，例如始终先锁`account`、再锁`order`；所有路径都遵守同一顺序。不要在拿着文件锁时执行无上限网络请求或等待用户输入。

Linux的`flock`不会替应用检测所有死锁。超时日志至少应包含锁名、等待上限、操作名和run ID，但不应泄露完整敏感路径或业务数据。

## 进程崩溃后会留下什么

`flock`由内核关联到打开的文件描述对象。进程退出、相关描述符全部关闭后，锁会释放，因此不需要靠“删除一个写着PID的文件”解锁。锁文件继续存在是正常现象；存在不等于有人持锁。

这也说明为什么“如果`counter.lock`存在就拒绝运行”不是锁：进程崩溃会留下文件，PID还可能被复用，检查与创建之间也有竞态。

锁释放不等于候选临时文件一定清理。进程若在`finally`执行前被强制终止，临时文件可能残留。正式读取者只读`counter.json`，维护流程可以按严格命名规则清理足够旧的`.counter.json.*.tmp`，但不能把候选文件自动当成已提交结果。

## flock的边界

### 它是协作协议

Linux本地文件系统上的`flock`通常是advisory lock。拥有权限但不调用同一锁协议的进程仍可直接替换数据文件。因此，所有写入口必须集中到同一个库或服务，而不是只修其中一个脚本。

### 网络文件系统语义不能想当然

NFS和SMB上的锁传播、与`fcntl`锁的交互、是否表现为mandatory lock，会随内核、协议和挂载选项变化。本文的通过结果只证明当前本机实验环境。共享存储需要在真实部署组合上故障测试，或改用数据库事务、协调服务或存储系统提供的条件写入。

### 它不是分布式锁

多台机器上的租约、网络分区、暂停进程、时钟和fencing token属于另一套问题。把一个本地`.lock`文件放到共享目录，不会自动得到可靠的分布式互斥。

## 完整复现实验

在实验根目录运行：

```bash
chmod +x run_lab.sh
./run_lab.sh
```

本次实测先通过5项单元测试：canonical JSON往返、坏状态拒绝、锁文件inode稳定、旧版本冲突、锁超时。随后启动真实子进程，得到：

```text
UNSAFE_FINAL_VALUE=1
UNSAFE_LOST_UPDATE=yes
LOCKED_FINAL_VALUE=2
LOCKED_SERIALIZED=yes
CAS_SUCCESS_COUNT=1
CAS_CONFLICT_COUNT=1
CAS_CONFLICT_RC=73
CAS_RETRY_FINAL_VALUE=2
LOCK_TIMEOUT_RC=75
STATE_JSON_VALID=yes
RUN_STATUS=ok
```

报告`concurrency_probe.json`还保存每个worker的可移植命令、return code、stdout和stderr。判断实验成功不能只搜索`RUN_STATUS=ok`，至少应同时断言计数、冲突数和返回码。

## 怎样在悲观锁与乐观版本之间选择

| 场景 | 更自然的起点 | 原因 |
| --- | --- | --- |
| 本机短小的read-modify-write，冲突频繁 | 完整临界区锁 | 实现直接，冲突不会反复重算 |
| 计算耗时，冲突少 | 乐观版本 | 大部分计算在锁外，提交临界区短 |
| SQLite/PostgreSQL中的多行状态 | 数据库事务 | 数据库提供隔离、日志和崩溃恢复 |
| HTTP资源编辑 | ETag加`If-Match` | 服务端原子评估precondition，冲突可返回412 |
| 多机共享状态 | 存储原生条件写或经过验证的协调协议 | 本地`flock`没有网络分区与fencing语义 |

选择前先写下不变量：一次操作修改哪些状态，是否允许重算，冲突该自动重试还是交给用户，最长等待多久，崩溃后由谁恢复。API名称排在这些问题之后。

## 常见错误

### 1. 认为`os.replace`等于事务

它只原子化一次路径替换，不保护替换前的read和compute。用两个进程同时加一即可检验。

### 2. 锁住临时文件

每个writer有自己的临时文件，彼此不会争同一把锁。锁对象必须代表共享业务资源。

### 3. 锁住会被replace的数据inode

路径替换后新打开者可能锁到新inode。使用不参与替换的稳定锁文件。

### 4. 在加锁前读取，锁内直接写旧结果

临界区必须包含决定新状态所依赖的读取，或使用锁内的版本比较拒绝旧proposal。

### 5. 版本不匹配时仍覆盖

version只有在不匹配会中止提交时才有意义。把冲突映射为明确返回码或领域错误。

### 6. 无限等待或无限重试

锁需要timeout，重试需要次数上限、退避和最终失败出口。否则高竞争会变成不可诊断的挂起或活锁。

### 7. 把锁文件存在当作锁被持有

锁状态由内核维护，文件存在只是提供稳定inode。用真实锁调用判断，不解析陈旧PID文件猜测。

## 练习

1. 把两个unsafe worker扩展到10个。用barrier保证它们先读，再观察最终值与成功进程数的差异。
2. 给CAS重试增加最多3次的指数退避，并在报告中记录每次读取版本；验证没有静默覆盖。
3. 在持锁进程中用`SIGKILL`制造崩溃，证明新进程能重新取得`flock`；同时检查是否残留候选临时文件。
4. 把计数器改为库存扣减。加入`value >= 0`不变量，并说明冲突与库存不足为什么是两种不同失败。
5. 用SQLite的`BEGIN IMMEDIATE`重写同一实验，对比应用锁、数据库事务和崩溃恢复的职责。

## 验收清单

- [ ] 能稳定复现两次成功写入只留下value 1。
- [ ] 每个被观察到的状态文件都是完整、合法且满足schema的JSON。
- [ ] 锁文件独立且不会被数据发布流程替换。
- [ ] 完整锁方案的两次加一得到value/version 2。
- [ ] 乐观方案恰好产生一次成功和一次明确冲突。
- [ ] 冲突后会重读和重算，不会重放旧proposal。
- [ ] 锁等待有上限，日志能区分冲突、超时和坏状态。
- [ ] 文档明确声明advisory、本地文件系统和非分布式边界。

## 参考资料

- [Python `fcntl`：文件描述符控制与`flock`](https://docs.python.org/3/library/fcntl.html)
- [Linux `flock(2)`：open file description、释放条件与advisory语义](https://man7.org/linux/man-pages/man2/flock.2.html)
- [Linux `flock(1)`：在Shell中管理锁与超时](https://man7.org/linux/man-pages/man1/flock.1.html)
- [Python `os.replace`与`os.fsync`](https://docs.python.org/3/library/os.html#os.replace)
- [Python `tempfile.mkstemp`](https://docs.python.org/3/library/tempfile.html#tempfile.mkstemp)
- [RFC 9110 If-Match：用条件请求防止lost update](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-match)
- [SQLite事务：语言级事务控制](https://www.sqlite.org/lang_transaction.html)
{% endraw %}
