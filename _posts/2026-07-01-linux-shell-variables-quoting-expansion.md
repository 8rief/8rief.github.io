---
layout: post
title: "Shell 变量和引用：为什么带空格的文件名会让脚本出错"
date: 2026-07-01 09:14:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用一个带空格的日志文件解释变量展开、双引号、glob 和安全参数传递。"
tags: [linux, shell, bash, quoting, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / variables / quoting / expansion
> 本文 lab 已验证：文件 `app 2026-07-02.log` 能被安全处理，`batch-summary.tsv` 正确记录 8 行、3 条错误。

Shell 脚本最容易坏在空格、通配符和空变量上。常见原因是变量展开后被 shell 重新拆成了多个词，命令收到的参数已经变形。初学阶段要养成一个基本习惯：表示一个路径或一个参数时，变量展开默认加双引号。

## 学习目标

1. 理解变量保存的是字符串，命令收到的是参数列表。
2. 知道双引号如何保留一个参数的边界。
3. 能解释为什么 `"$file"` 比 `$file` 安全。

## 先修知识

知道 `grep`、`wc` 可以接收文件路径作为参数。

## 核心模型

![Shell 展开和引用边界](/assets/diagrams/linux-shell-variables-quoting.svg)

shell 会先展开变量和通配符，再执行命令。没有引用保护时，一个变量可能变成多个参数，也可能触发 glob 展开。双引号把变量结果保留为一个参数。

## 可信资料的关键结论

- Bash 手册把 quoting 单独列为一章，因为引用直接影响词拆分和特殊字符解释。
- POSIX shell 也定义了 field splitting、pathname expansion 和 quote removal；这些阶段解释了很多脚本“看起来对、运行就坏”的现象。
- ShellCheck 的 SC2086 提醒：变量展开通常需要双引号，以避免 word splitting 和 globbing。

## 逐步实现

lab 故意生成了一个带空格的文件名：

```text
.lab_tmp/logs/app 2026-07-02.log
```

安全写法：

```bash
file='.lab_tmp/logs/app 2026-07-02.log'
wc -l "$file"
```

预期输出：

```text
8 .lab_tmp/logs/app 2026-07-02.log
```

危险写法：

```bash
wc -l $file
```

这会把路径拆成多个参数，命令可能会分别寻找 `.lab_tmp/logs/app`、`2026-07-02.log`，导致文件不存在。

在脚本里，路径参数也要加双引号。`scripts/safe_batch.sh` 中的核心写法是：

```bash
lines=$(wc -l < "$file" | tr -d ' ')
errors=$(grep -c ' level=ERROR ' "$file" || true)
printf '%s\t%s\t%s\n' "$(basename "$file")" "$lines" "$errors"
```

这里每个变量展开都代表一个参数，因此都用双引号保护。

## 常见错误

1. **只在有空格时才加引号。** 你通常不知道未来输入会不会有空格、换行或通配符。
2. **把一串命令选项放进普通字符串变量。** 如果确实需要多个参数，Bash 里优先用数组。
3. **用 `for file in $(find ...)`。** 这种写法会按空白拆分文件名，后面会用 `find -print0` 修正。
4. **把单引号和双引号混用。** 单引号禁止变量展开，双引号允许变量展开但保护参数边界。

## 练习或延伸

1. 新建文件 `.lab_tmp/logs/app [test].log`，比较 `wc -l $file` 和 `wc -l "$file"` 的行为。
2. 在 `safe_batch.sh` 里临时去掉 `"$file"` 的引号，重新运行测试，观察失败原因。

## 参考资料

- GNU Bash：[Quoting](https://www.gnu.org/software/bash/manual/html_node/Quoting.html)
- GNU Bash：[Shell Expansions](https://www.gnu.org/software/bash/manual/html_node/Shell-Expansions.html)
- POSIX：[Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- ShellCheck：[SC2086](https://www.shellcheck.net/wiki/SC2086)

{% endraw %}
