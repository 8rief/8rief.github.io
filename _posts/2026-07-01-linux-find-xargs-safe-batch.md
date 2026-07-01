---
layout: post
title: "批量处理文件：用 find -print0 保护文件名边界"
date: 2026-07-01 09:28:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "从带空格文件名出发，学习 find、while read -d 和安全批处理。"
tags: [linux, find, xargs, batch, teaching]
---
{% raw %}
> 主题：Linux CLI 与 Shell 自动化 / find / print0 / safe batch
> 本文 lab 已验证：`reports/batch-summary.tsv` 正确处理 `app 2026-07-02.log`。

只处理一个文件时，引用变量已经够用。批量处理文件时，风险转移到了“文件列表怎么传递”。如果用空格或换行分隔路径，带空格的文件名会出错。更稳妥的做法是让 `find` 用 NUL 字节分隔文件名，再用支持 NUL 的读取方式逐个处理。

## 学习目标

1. 会用 `find` 按目录、类型、文件名模式找文件。
2. 理解 `-print0` 解决的是路径分隔问题。
3. 能写一个安全处理多个日志文件的循环。

## 先修知识

已经知道变量展开要用双引号保护一个路径参数。

## 核心模型

![find -print0 安全批处理路径](/assets/diagrams/linux-find-print0-safe-batch.svg)

安全批处理要保护两层边界：文件名列表之间的边界，以及单个文件名作为命令参数的边界。`find -print0` 负责第一层，`"$file"` 负责第二层。

## 可信资料的关键结论

- GNU find 从指定起点递归遍历目录树，并按表达式筛选文件。
- `-print0` 用 NUL 字节结尾，适合和 `xargs -0` 或 Bash 的 `read -d ''` 搭配。
- man7 的 find 手册也强调 GNU find 的表达式求值和操作符优先级；复杂条件需要加括号或拆开验证。

## 逐步实现

先列出日志文件：

```bash
find .lab_tmp/logs -type f -name '*.log' -print
```

这个命令适合人看。给脚本处理时，用 NUL 分隔：

```bash
find .lab_tmp/logs -type f -name '*.log' -print0
```

NUL 字节不适合直接显示，因此脚本里这样读取：

```bash
while IFS= read -r -d '' file; do
  lines=$(wc -l < "$file" | tr -d ' ')
  errors=$(grep -c ' level=ERROR ' "$file" || true)
  printf '%s\t%s\t%s\n' "$(basename "$file")" "$lines" "$errors"
done < <(find "$log_dir" -type f -name '*.log' -print0 | sort -z)
```

运行：

```bash
bash scripts/safe_batch.sh .lab_tmp/logs reports/batch-summary.tsv
cat reports/batch-summary.tsv
```

预期输出：

```text
file	lines	errors
app 2026-07-02.log	8	3
app-2026-07-01.log	8	2
```

## 常见错误

1. **用 `for file in $(find ...)`。** 这会按空白拆分路径。
2. **只修复 find，不引用变量。** `-print0` 只保护列表边界，命令参数仍要 `"$file"`。
3. **复杂 find 条件不加验证。** 先只输出文件名，确认范围正确，再添加删除、移动或转换操作。
4. **批处理直接改原文件。** 初学阶段先输出报告，确认范围后再做写操作。

## 练习或延伸

1. 给 `.lab_tmp/logs` 新增一个带括号或空格的日志文件，重新运行 `safe_batch.sh`。
2. 把 `-name '*.log'` 改成 `-mtime -1`，观察当前 lab 中是否仍能找到文件。
3. 用 `xargs -0` 改写一个只统计行数的版本。

## 参考资料

- GNU findutils：[Finding Files](https://www.gnu.org/software/findutils/manual/html_mono/find.html)
- man7：[find(1)](https://man7.org/linux/man-pages/man1/find.1.html)
- GNU findutils：[xargs options](https://www.gnu.org/software/findutils/manual/html_node/find_html/xargs-options.html)

{% endraw %}
