---
layout: post
title: "退出码、信号和作业控制：脚本为什么知道命令失败了"
date: 2026-05-27 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 $?、wait、SIGTERM 和后台进程解释 Linux 命令结束状态。"
tags: [linux, signal, exit-status, shell, teaching]
---
{% raw %}

> 主题：操作系统与 Linux 基础 / 退出状态和信号
> 本文是 OS/Linux 进程与文件基础包的第六篇。实验只启动和结束 lab 自己创建的短生命周期进程。

脚本能判断命令是否成功，靠的是进程结束状态。进程可以主动 `exit(0)` 或 `exit(1)`，也可能被信号结束。shell 把这些结果折叠成退出码，供 `$?`、`if`、`set -e` 和 `wait` 使用。理解这条链路，才能写出可靠的自动化脚本。

## 学习目标

1. 解释退出码 `0` 和非零值的约定。
2. 用 `$?` 和 `if command; then ...` 判断命令结果。
3. 说明信号如何让进程提前结束。
4. 理解后台进程、`$!` 和 `wait` 的基本用法。

## 先修知识

需要知道 shell 脚本按命令顺序执行，知道进程可以在前台或后台运行。

## 为什么需要退出状态和信号

自动化脚本不能靠“终端上看起来没报错”判断成功。一条命令可以安静失败，也可以在成功时输出大量文本。退出状态是父子进程之间用来传递简短结果的稳定接口，shell 再把它映射到条件分支和脚本自身的退出码。

信号解决的是另一类状态变化：进程可能还没运行到主动 `exit`，就收到终止、中断或其他异步通知。启动者仍需要回收子进程并分辨它是正常结束还是被信号终止，所以 `kill` 后的 `wait` 是证据链的一部分。

## 核心模型

![退出码、信号和 wait 模型](/assets/diagrams/linux-exit-status-signals-jobs.svg)

父进程启动子进程后，可以等待它结束。子进程正常退出时会给出退出状态；被信号终止时，shell 通常把结果表示成 `128 + signal_number`。例如 `SIGTERM` 的编号常见为 15，`wait` 得到 143。

## 逐步实现

先看普通退出码：

```bash
true
echo "$?"
false
echo "$?"
```

`true` 返回 `0`，`false` 返回非零值。脚本中更推荐直接写：

```bash
if grep -q 'ERROR' workspace/logs/events.log; then
  echo 'found error line'
else
  echo 'no error line'
fi
```

这样把命令的成功与失败放进控制流，不需要手动保存 `$?`。

再看信号终止：

```bash
sleep 30 &
pid=$!
kill -TERM "$pid"
wait "$pid"
echo "$?"
```

本地 lab 把这一段压缩成脚本，得到：

```text
wait_status=143
```

这表示后台 `sleep` 收到 `SIGTERM` 后结束，父 shell 通过 `wait` 读到了结束状态。

### 143 怎么解释

在 Bash 的常见表示中，被编号 15 的 `SIGTERM` 终止会得到 `128 + 15 = 143`。这是 shell 展示给脚本的约定值。在 C 或 Python 中直接使用 `waitpid` 类 API 时，应用会获得编码后的等待状态，需要用对应 API 判断是正常退出还是信号终止。

因此不应把任意大于 128 的数都盲目解读为信号。应同时记录执行环境、shell 约定和原始操作。本 lab 知道自己明确发送了 `SIGTERM`，所以 143 有完整上下文。

## 写脚本时怎么用

可靠脚本通常遵循三条规则：

1. 对关键命令检查退出码，不用输出文本猜测成功。
2. 对需要清理的临时文件使用 `trap`，让 `INT`、`TERM`、`EXIT` 都能触发清理逻辑。
3. 对后台进程保存 `$!`，结束时用 `wait` 收尾，避免留下孤立进程。

示例：

```bash
cleanup() {
  rm -f workspace/generated/tmp.out
}
trap cleanup EXIT INT TERM

python3 src/system_observer.py --workspace workspace --outdir reports
```

这里的 `trap` 不保证所有异常都能处理，但它能覆盖大量普通脚本中常见的退出路径。

管道还需要明确成功标准。可用下面的对照实验查看 `pipefail` 的作用：

```bash
set +o pipefail
false | true
printf 'without_pipefail=%s\n' "$?"

set -o pipefail
false | true
printf 'with_pipefail=%s\n' "$?"
```

Bash 中的预期输出是：

```text
without_pipefail=0
with_pipefail=1
```

默认情况下，管道状态由最后一条命令决定；启用 `pipefail` 后，前面的 `false` 不再被末尾 `true` 的成功掩盖。对数据处理脚本，这能阻止上游失败后仍然生成看似正常的空报告。

## 常见错误

1. **只看终端是否打印错误。** 有些命令失败时没有明显输出，退出码才是接口。
2. **在管道中忽略前半段失败。** 复杂脚本需要考虑 `pipefail` 或显式检查。
3. **杀后台进程后不 `wait`。** 父进程不读取状态，脚本很难知道真实结束原因。
4. **把所有非零值都当同一种失败。** 有些命令用不同退出码表达不同错误类型。

## 练习或延伸

1. 写一个脚本，分别运行 `grep` 找得到和找不到的模式，观察退出码。
2. 对后台 `sleep` 发送 `INT` 和 `TERM`，比较 `wait` 得到的状态。
3. 尝试 `set -euo pipefail`，记录它如何改变脚本失败行为。

## 参考资料

- Linux man-pages：[signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html)
- Linux man-pages：[wait(2)](https://man7.org/linux/man-pages/man2/wait.2.html)
- GNU Bash Manual：[Job Control Basics](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Basics.html)

{% endraw %}
