---
layout: post
title: "Linux 脚本参数、退出状态和错误处理：让 run fail 可以定位"
date: 2026-03-17 18:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [linux, shell, bash, scripting]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/linux-script-args-exit-errors/README.md`](/assets/labs/linux-script-args-exit-errors/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

前面已经讲了本地帮助、命令定位和环境变量。下一步自然会写脚本：把几条命令放进 `run_lab.sh`、`build.sh`、`deploy.sh` 或 CI job。脚本一多，最常见的问题就来了：命令失败了，但日志里只剩一大片输出；参数带空格后被拆开；`grep` 没找到文本却被当成致命错误；临时文件没有清理；脚本明明失败，最后退出码却是 0。

这篇文章建立一个可复现的脚本错误处理 workflow。读完后你应该能把一次 `run fail` 拆成可定位的信息：脚本收到什么参数，哪条命令返回什么退出状态，哪些失败是预期分支，哪些失败应该立刻停止，退出前如何清理现场，调用者应该从哪个 exit code 判断问题类型。

## 学习目标

读完并跑完实验后，你应该能做到：

1. 用 `$0`、`$#`、`$1`、`"$@"` 和 `shift` 解释脚本参数如何进入 Bash。
2. 解释退出状态的含义，并知道为什么 `$?` 必须立刻保存。
3. 区分“命令失败”和“业务上可接受的未命中”，例如 `grep` 返回 1。
4. 使用 `set -euo pipefail` 暴露未处理错误，同时知道它不替代显式分支。
5. 用 `trap ... EXIT` 做清理，让失败路径也能收尾。
6. 写出 `usage`、参数检查和稳定的 exit code，让调用者知道脚本为什么失败。

## 先修知识

需要知道 shell 会启动子进程，知道 `PATH` 如何定位命令，能读懂基本重定向和管道。本文使用 Bash，因为很多项目脚本和 GitHub Actions step 默认会遇到 Bash 或类 POSIX shell。不同 shell 的细节不完全相同，本文的可复现实验只声明 Bash 行为。

实验目录可以叫 `linux-script-args-exit-errors/`：

```text
linux-script-args-exit-errors/
├── run_lab.sh
├── scripts/
│   └── script_error_probe.py
└── reports/
    ├── error_handling_summary.md
    ├── run_lab_output.txt
    ├── script_error_probe.json
    └── transcript.md
```

`run_lab.sh` 会在 `/tmp/script-error-lab` 下生成几个小脚本：参数脚本、退出状态脚本、strict mode 脚本、cleanup 脚本和 usage 脚本。它不会修改你的 home 目录，也不会安装软件包。

## 为什么需要脚本错误处理 workflow

脚本错误处理 workflow 用来解决一个具体问题：当自动化命令失败时，你需要知道失败发生在哪一层。是参数传错、命令返回非 0、管道中间失败、未定义变量、临时文件残留，还是脚本把错误吞掉以后返回了 0。没有这层结构，日志会变成“看起来很多，真正能定位的信息很少”。

一个实用模型如下：

```text
caller
  │
  ├─ argv                 脚本参数：$0, $#, $1, "$@", shift
  │
script
  ├─ command status       每条命令产生 exit status，0 表示成功
  ├─ expected branch      if command; then ... else rc=$? ...
  ├─ strict guard         set -euo pipefail 暴露未处理错误
  ├─ cleanup              trap cleanup EXIT
  └─ public interface     usage + stderr + exit code
```

这张图的核心是信息不要丢：参数要按原样保留，退出状态要在被覆盖前保存，预期失败要进入显式分支，未预期失败要尽早停止，清理逻辑要覆盖失败路径。

## 第一步：参数不是字符串拼接，`"$@"` 才保留边界

实验脚本 `args_demo.sh` 接收三个参数，其中第二个参数包含空格：

```bash
/tmp/script-error-lab/bin/args_demo.sh alpha 'two words' --flag
```

输出摘录：

```text
SCRIPT_NAME=/tmp/script-error-lab/bin/args_demo.sh
ARG_COUNT=3
FIRST_ARG=alpha
ALL_ARGS=[alpha][two words][--flag]
SHIFT_ARG=alpha REMAINING_BEFORE=3
SHIFT_ARG=two words REMAINING_BEFORE=2
SHIFT_ARG=--flag REMAINING_BEFORE=1
ARG_COUNT_AFTER_SHIFT=0
```

这里有几个状态变化：

- `$0` 是脚本名或调用路径。
- `$#` 是参数个数，这里是 `3`。
- `$1` 是第一个参数，这里是 `alpha`。
- `"$@"` 会把每个参数作为独立单元展开，所以 `two words` 保持为一个参数。
- `shift` 会丢弃当前 `$1`，把后面的参数左移；循环结束后 `$#` 变成 `0`。

初学脚本时最容易写错的是 `$*` 或未加引号的 `$@`。只要参数里有空格、通配符或空字符串，边界就可能被破坏。默认写 `for arg in "$@"; do ...; done`，只有在你明确需要重新分词时才改变它。

## 第二步：退出状态要立刻保存

Linux 命令完成后会返回一个退出状态。Bash 用 `$?` 暴露上一条命令的状态；问题是 `$?` 很容易被下一条命令覆盖。实验脚本 `exit_status_demo.sh` 输出：

```text
true rc=0
grep needle rc=0 action=found
grep missing rc=1 action=not-found-expected
false rc captured=1
```

解释如下：

- `true` 返回 0，表示成功。
- `grep -q needle data.txt` 找到文本，所以条件分支进入成功路径。
- `grep -q missing data.txt` 没找到文本，返回 1；这里“没找到”是预期分支，所以脚本保存 `rc=$?` 并解释它。
- `false || rc=$?` 演示了如何在不停止脚本的情况下捕获失败状态。

关键习惯是：需要解释某条命令的状态时，下一行就保存 `rc=$?`。不要先 `echo`、`printf`、调用函数或执行别的命令后再读 `$?`，那时你读到的已经是新命令的状态。

## 第三步：预期失败放进 `if command`，不要靠日志猜

`grep` 的返回 1 是典型例子。没有找到匹配文本不一定是程序错误，它可能只是业务分支。推荐写法是：

```bash
if grep -q 'needle' work/data.txt; then
  printf 'found needle\n'
else
  rc=$?
  printf 'needle not found, rc=%s\n' "$rc"
fi
```

这种写法有两个好处：第一，读者知道你预期 `grep` 可能返回非 0；第二，日志会说明这个非 0 的语义。相比之下，把所有命令串起来再看最后一行失败，往往需要回头猜哪一步出错。

## 第四步：`set -euo pipefail` 用来暴露未处理错误

实验脚本 `strict_demo.sh` 开头是：

```bash
set -euo pipefail
```

三项含义分别是：

- `-e`：未被条件分支处理的命令返回非 0 时，脚本退出。
- `-u`：引用未设置变量时报错退出。
- `pipefail`：管道整体状态反映管道里失败的命令，而不只看最后一个命令。

实验结果：

```text
STRICT_PASS=done
STRICT_FAILED rc=1
STRICT_UNSET rc=1
STRICT_PIPE rc=1
```

对应三种失败：

```bash
/tmp/script-error-lab/bin/strict_demo.sh fail-command
/tmp/script-error-lab/bin/strict_demo.sh fail-unset
/tmp/script-error-lab/bin/strict_demo.sh fail-pipe
```

`set -euo pipefail` 的作用是让未处理错误尽早显形。它不负责替你判断哪些非 0 是可接受分支。预期失败仍然应该写成 `if command; then ... else ... fi`、`case` 或显式捕获 `cmd || rc=$?`。如果你写 `cmd || true`，请紧跟注释或日志说明为什么这个失败可以忽略。

## 第五步：失败路径也要清理现场

很多脚本会创建临时文件、启动本地服务、写中间报告。只处理成功路径会留下脏状态。实验脚本 `trap_cleanup_demo.sh` 使用：

```bash
cleanup() {
  local rc=$?
  rm -f "$tmp"
  printf 'cleanup_exists_after=no\n'
  return "$rc"
}
trap cleanup EXIT
```

强制失败时：

```bash
/tmp/script-error-lab/bin/trap_cleanup_demo.sh fail
```

输出摘录：

```text
cleanup_exists_before=yes
trap_mode=fail
cleanup_exists_after=no
```

脚本最终返回 `7`，但临时文件仍被删除。这里有一个细节：cleanup 函数先保存 `local rc=$?`，最后 `return "$rc"`，避免清理命令把原始退出状态覆盖掉。真实项目里可以把 kill 本地服务、删除临时目录、输出诊断摘要都放在 cleanup 里。

## 第六步：usage 是脚本的公开接口

脚本给人或 CI 调用时，参数错误应该稳定、清楚、可机器判断。实验脚本 `usage_demo.sh` 没有参数时输出：

```text
usage: usage_demo.sh <input-file> <output-file>
```

退出状态是：

```text
64
```

本文把 `64` 用作 usage error 的约定值。你也可以在团队里选择别的错误码，但要固定下来并写进 README。比错误码本身更重要的是三件事：错误信息写到 stderr；成功输出写到 stdout；调用者能根据 exit code 区分“参数错误”“输入不存在”“命令内部失败”。

一个小模板如下：

```bash
#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'usage: %s <input-file> <output-file>\n' "$(basename "$0")" >&2
}

if [[ "$#" -ne 2 ]]; then
  usage
  exit 64
fi

input=$1
output=$2

if [[ ! -f "$input" ]]; then
  printf 'error: input not found: %s\n' "$input" >&2
  exit 66
fi

cp "$input" "$output"
printf 'copied input=%s output=%s\n' "$input" "$output"
```

这段模板适合很多本地脚本：先定义接口，再检查参数，再进入真正工作。后续要扩展日志、cleanup、子命令时，也不会破坏基本结构。

## 本地实验的完整摘要

本次实验生成的稳定摘要是：

```text
SCRIPT_ERROR_LAB_STATUS ok
ARG_COUNT=3
grep missing rc=1
STRICT_FAILED rc=1
STRICT_UNSET rc=1
STRICT_PIPE rc=1
cleanup_exists_after=no
usage: usage_demo.sh <input-file> <output-file>
reports=script_error_probe.json transcript.md error_handling_summary.md
```

如果你自己复跑，可以用这些 token 判断实验是否和本文一致。更完整的证据在 `reports/script_error_probe.json` 和 `reports/transcript.md` 中，包括每个命令的 argv、stdout、stderr 和 return code。

## 常见错误和定位方式

1. **把参数拼成一个字符串再执行**：参数里有空格时会被拆开。优先使用数组或 `"$@"` 保留边界。
2. **读 `$?` 太晚**：任何命令都会覆盖 `$?`。需要记录时下一行立刻 `rc=$?`。
3. **以为 `set -e` 会处理所有错误**：`if`、`while`、`&&`、`||` 等上下文有自己的规则。预期失败要写成显式分支。
4. **管道只看最后一个命令**：没有 `pipefail` 时，前面的命令失败可能被最后的 `cat`、`wc`、`tee` 掩盖。
5. **cleanup 覆盖原始退出码**：清理函数里先保存 `rc=$?`，最后返回它。
6. **stderr/stdout 混用**：错误、usage 和诊断写 stderr；机器要消费的正常结果写 stdout。
7. **把私有路径或密钥写进 transcript**：公开日志前只保留可复现、可公开的信息；token、数据库密码、本地个人路径都不要进入文章或仓库。

## 练习

1. 修改 `usage_demo.sh`，增加 `--help`：传入 `--help` 时打印 usage 并返回 0；参数数量错误时仍返回 64。
2. 给 `strict_demo.sh` 增加一个 `if grep -q missing ...` 的安全分支，观察它在 `set -e` 下不会退出。
3. 写一个 `with_temp_dir.sh`：创建临时目录，成功和失败都通过 `trap` 删除目录，并在日志里保留原始 exit code。
4. 把你现有项目里的 `run.sh` 改成本文模板：参数检查、`set -euo pipefail`、显式 `usage`、cleanup、最后输出一个稳定 summary token。

## 边界

本文只讨论 Bash 脚本的基础错误处理，不覆盖复杂命令行解析库、并发任务调度、systemd service、Make/Ninja 的依赖图，也不把所有非 0 都解释成错误。真实项目里还要结合语言自己的测试框架、日志系统和 CI artifact。本文提供的是底层脚本接口：调用者能看懂参数、状态、错误分支和清理行为。

## 参考资料

- Linux man-pages project: [bash(1)](https://man7.org/linux/man-pages/man1/bash.1.html)
- The Open Group Base Specifications Issue 8: [Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- The Open Group Base Specifications Issue 8: [shift](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/shift.html)
- The Open Group Base Specifications Issue 8: [set](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/set.html)
- The Open Group Base Specifications Issue 8: [trap](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/trap.html)
- The Open Group Base Specifications Issue 8: [grep](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/grep.html)
