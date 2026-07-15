---
layout: post
title: "Shell 变量和引用：为什么带空格的文件名会让脚本出错"
date: 2026-06-12 18:00:00 +0800
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

## 为什么需要理解展开顺序

Shell 脚本不是把一行文本直接交给程序执行。它会先做变量展开、命令替换、词拆分、通配符展开，最后才构造程序真正收到的参数列表。很多脚本看起来“变量里明明是一个路径”，运行时却失败，是因为路径在词拆分阶段已经变成了多个参数。

引用直接决定参数边界，是脚本正确性的一部分。`"$file"` 表示“把变量结果作为一个参数传递”；`$file` 表示“展开后再让 shell 拆分和匹配”。在处理路径、用户输入、报告文件名时，默认选择前者。

把这件事想清楚，后面的 `find -print0`、脚本参数、`grep "$pattern" "$file"` 都会更自然：我们一直在保护参数边界。

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

## 输出怎么读

`wc -l "$file"` 的输出有两部分：前面的 `8` 是行数，后面的路径是 `wc` 实际打开的文件名。路径仍然完整显示为 `app 2026-07-02.log`，说明 shell 给 `wc` 传入了一个文件参数。

危险写法的失败原因可以按参数列表理解：

```text
file='.lab_tmp/logs/app 2026-07-02.log'
wc -l $file
-> wc 收到多个参数：.lab_tmp/logs/app、2026-07-02.log
```

程序本身并不知道这是一个被拆坏的路径。它只会按收到的参数逐个打开文件，所以错误表面上像“文件不存在”，根因却是 shell 展开阶段没有保护边界。

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

## 什么时候不加双引号

学习阶段可以采用简单规则：变量展开默认加双引号。少数例外需要明确理由，例如：

1. 你确实想让 shell 展开通配符：`ls *.log`。
2. 你在 Bash 数组里传多个参数：`cmd "${args[@]}"`。
3. 你在 `[[ ... ]]` 条件中使用模式匹配，并且知道右侧是否要按模式解释。

如果说不出理由，就先加双引号。这个规则比记一堆特殊案例更可靠。

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
