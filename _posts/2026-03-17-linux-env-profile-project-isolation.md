---
layout: post
title: "Linux 环境变量、profile 和项目环境隔离：为什么换个 shell 配置就变了"
date: 2026-03-17 09:00:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
tags: [linux, shell, environment, profile]
---

> **配套实验代码**：完整源码和运行脚本见 [`assets/labs/linux-env-profile-project-isolation/README.md`](/assets/labs/linux-env-profile-project-isolation/README.md)。如果你还没有克隆本站仓库，先看[实验代码使用说明](/assets/labs/README.md)。

前两篇已经解决了两个基础问题：如何读本地帮助，以及一个命令名如何通过 `PATH` 命中真实可执行文件。接下来会遇到更常见的开发问题：同一个项目，在一个终端里能跑，换一个终端、换一个脚本、换成 CI 或 systemd 就失败。很多时候代码没有变，变化发生在环境里：变量有没有 `export`，shell 有没有读 `.bashrc` 或 profile，项目有没有把自己的 `bin` 目录放到 `PATH` 前面，脚本有没有在干净环境里运行。

这篇文章建立一个可复现的环境变量 workflow。它的目标是让你能回答四个问题：变量在哪个 shell 里产生，是否会传给子进程，哪个启动文件改了它，项目环境如何启用和退出。后续学习 Python venv、Java `JAVA_HOME`、Go/Rust/C++ 工具链、Docker 环境变量和深度学习训练配置时，都要用到这套模型。

## 学习目标

读完并跑完实验后，你应该能做到：

1. 解释 shell 变量和进程环境变量的区别。
2. 用 `export` 让变量进入子进程环境，并用 Python 观察结果。
3. 用 `env -i` 构造最小环境，定位某个变量是否来自外部污染。
4. 区分 `.bashrc`、profile、`BASH_ENV` 和项目 `env.sh` 的作用边界。
5. 用 `source` 启用项目环境，并解释为什么 subshell 里的改动不会向父 shell 泄漏。
6. 写出项目环境 transcript，说明哪些变量可公开，哪些本地值不能提交。

## 先修知识

需要知道当前 shell 会启动子进程，知道 `PATH` 会影响命令定位，能读懂 `command -v` 和基本重定向。本文用 Bash 演示；Zsh、Fish、PowerShell 的启动文件不同，但“父进程环境传给子进程”的操作系统模型相同。

实验目录可以叫 `linux-env-profile-project-isolation/`：

```text
linux-env-profile-project-isolation/
├── run_lab.sh
├── scripts/
│   └── env_profile_probe.py
└── reports/
    ├── env_profile_probe.json
    ├── environment_summary.md
    ├── run_lab_output.txt
    └── transcript.md
```

实验会在 `/tmp/env-profile-lab` 下创建临时 home、临时项目目录、临时 `.bashrc`、临时 `.bash_profile` 和项目 `env.sh`。它不会修改你真正的 home 目录，也不会安装软件包。

## 为什么需要环境隔离 workflow

环境隔离 workflow 用来解决一个很实际的调试问题：你看到的命令行为不只由源码决定，还由启动它的进程环境决定。一个项目如果依赖 `PATH`、`PYTHONPATH`、`JAVA_HOME`、`CUDA_VISIBLE_DEVICES`、`APP_ENV`、`DATABASE_URL` 之类的变量，就必须说明这些变量从哪里来、何时生效、传给了哪些子进程。

核心模型如下：

```text
parent shell
  ├─ shell local variable      只在当前 shell 内部可见
  ├─ exported environment      exec 子进程时复制一份
  ├─ startup files             .bashrc / profile / BASH_ENV 可能修改 shell
  └─ source project/env.sh     修改当前 shell 的项目环境
          │
          ├─ child process     继承 exported variables
          └─ subshell (...)    可继承父环境，退出后改动丢弃
```

这里的关键点是方向：子进程继承父进程的一份环境副本，子进程改动不会反向改变父 shell。项目环境脚本如果用 `source` 执行，会修改当前 shell；如果用普通脚本执行，只会修改脚本进程自己。

## 第一步：shell 变量默认不会传给子进程

先看一个最小反例：

```bash
bash --noprofile --norc -c \
  'LOCAL_ONLY=hidden; python3 -c "import os; print(os.getenv(\"LOCAL_ONLY\", \"unset\"))"'
```

实验输出：

```text
unset
```

`LOCAL_ONLY=hidden` 在 shell 内部存在，但没有进入子进程环境。`python3` 是子进程，它通过 `os.environ` 只能看到已经导出的环境变量。这解释了很多“我明明在 shell 里设置了变量，程序却读不到”的问题。

## 第二步：`export` 才会进入子进程环境

把变量导出后再观察：

```bash
bash --noprofile --norc -c \
  'export EXPORTED_VALUE=visible; python3 -c "import os; print(os.getenv(\"EXPORTED_VALUE\", \"unset\"))"'
```

输出：

```text
visible
```

`export` 的含义是把这个名字和值放进当前 shell 启动子进程时会复制的环境里；它不负责把变量永久保存到所有终端。关掉这个 shell，或者在另一个没有设置它的 shell 里运行程序，变量就不会自动存在。

## 第三步：用 `env -i` 构造最小环境

调试环境问题时，最有效的动作之一是先清空环境，再只加回必要变量：

```bash
env -i HOME=/tmp/env-profile-lab/home PATH=/usr/bin:/bin \
  bash --noprofile --norc -c \
  'printf "HOME=%s\nPATH=%s\nDEMO=%s\n" "$HOME" "$PATH" "${DEMO_APP_ENV:-unset}"; command -v python3'
```

输出应该包含：

```text
HOME=/tmp/env-profile-lab/home
PATH=/usr/bin:/bin
DEMO=unset
/usr/bin/python3
```

这段输出证明两件事：第一，`DEMO_APP_ENV` 不是系统天然存在的变量；第二，在最小 `PATH` 中仍能找到 `/usr/bin/python3`。当你怀疑某个变量来自 IDE、终端插件、conda、nvm 或个人 `.bashrc` 时，可以用这种方式构造对照组。

## 第四步：`.bashrc` 适合交互 shell

Bash 的启动文件和 shell 类型有关。交互式非 login shell 通常读取 `.bashrc`。实验里用临时 rc 文件模拟：

```bash
bash --rcfile /tmp/env-profile-lab/home/.bashrc -i -c \
  'printf "INTERACTIVE_MARKER=%s\n" "${INTERACTIVE_MARKER:-unset}"; printf "PATH_HEAD=%s\n" "${PATH%%:*}"' \
  2>/dev/null | grep -E '^(INTERACTIVE_MARKER|PATH_HEAD)='
```

输出：

```text
INTERACTIVE_MARKER=from_bashrc
PATH_HEAD=/tmp/env-profile-lab/home/interactive-bin
```

这说明 `.bashrc` 修改了交互 shell 的环境和 `PATH`。把别名、提示符、补全、交互工具放在 `.bashrc` 比较合理；把项目必须依赖的变量只放在个人 `.bashrc` 里，会让脚本、CI、服务进程很难复现。

## 第五步：profile 是 shell code，`source` 会改当前 shell

实验里的 `.bash_profile` 内容是：

```bash
export LOGIN_MARKER=from_bash_profile
export PATH="$HOME/login-bin:$PATH"
```

用 `source` 执行它：

```bash
bash --noprofile --norc -c \
  'source /tmp/env-profile-lab/home/.bash_profile; printf "LOGIN_MARKER=%s\n" "${LOGIN_MARKER:-unset}"; printf "PATH_HEAD=%s\n" "${PATH%%:*}"'
```

输出：

```text
LOGIN_MARKER=from_bash_profile
PATH_HEAD=/tmp/env-profile-lab/home/login-bin
```

`source file` 会在当前 shell 执行文件内容，所以变量和 `PATH` 修改会留在当前 shell。普通执行 `bash file` 会开新进程，修改只存在于那个子进程里。这是理解项目 `env.sh` 的基础。

## 第六步：非交互 Bash 可以通过 `BASH_ENV` 注入环境

非交互 Bash 运行脚本时不会按交互 shell 的方式读取 `.bashrc`。Bash 提供了 `BASH_ENV`：

```bash
BASH_ENV=/tmp/env-profile-lab/project/bash_env.sh \
  bash --noprofile --norc -c \
  'printf "NONINTERACTIVE_MARKER=%s\n" "${NONINTERACTIVE_MARKER:-unset}"'
```

输出：

```text
NONINTERACTIVE_MARKER=from_BASH_ENV
```

这很有用，也有风险。它说明非交互脚本也可能被环境变量改变行为。调试构建脚本时，如果怀疑环境污染，先记录 `env | sort` 的公共安全子集，必要时用 `env -i` 验证脚本在干净环境中的行为。

## 第七步：项目环境脚本应该显式、可复查

实验里的项目 `env.sh` 做三件事：

```bash
export PROJECT_ROOT=/tmp/env-profile-lab/project
export DEMO_APP_ENV=development
export DEMO_CONFIG=config/dev.toml
export PATH="$PROJECT_ROOT/bin:$PATH"
```

启用它并运行项目工具：

```bash
bash --noprofile --norc -c \
  'source /tmp/env-profile-lab/project/env.sh; command -v demo-env-tool; demo-env-tool; python3 -c "import os; print(os.getenv(\"DEMO_APP_ENV\")); print(os.getenv(\"DEMO_CONFIG\"))"'
```

输出：

```text
/tmp/env-profile-lab/project/bin/demo-env-tool
demo-env-tool from project-bin
development
config/dev.toml
```

这就是可复查项目环境的最小形态：先说明 `PATH` 被哪个目录扩展，再说明程序实际读到了哪些变量。真实项目里可以把可公开默认值放进 `.env.example`，把本机私有值放进未提交的本地文件。公共文章、README 和仓库里不要出现真实 token、数据库密码、云服务密钥或个人路径。

## 第八步：subshell 改动不会向父 shell 泄漏

用括号启动 subshell：

```bash
bash --noprofile --norc -c \
  '( source /tmp/env-profile-lab/project/env.sh; printf "inside=%s\n" "$DEMO_APP_ENV" ); printf "outside=%s\n" "${DEMO_APP_ENV:-unset}"'
```

输出：

```text
inside=development
outside=unset
```

这说明 subshell 可以继承父环境，也可以在内部 `source` 项目环境，但退出后不会改变父 shell。临时运行一次构建或测试时，subshell 是一种干净的隔离手段；需要持续在当前终端使用项目工具时，再显式 `source env.sh`。

## 第九步：运行完整实验

在实验目录执行：

```bash
./run_lab.sh
```

核心输出：

```text
== run env/profile probes ==
{"probes": 8, "failed": []}

== selected evidence ==
local-variable-not-inherited PASS ['unset']
exported-variable-inherited PASS ['visible']
interactive-bashrc PASS ['INTERACTIVE_MARKER=from_bashrc', 'PATH_HEAD=/tmp/env-profile-lab/home/interactive-bin']
project-env-source PASS ['/tmp/env-profile-lab/project/bin/demo-env-tool', 'demo-env-tool from project-bin', 'development', 'config/dev.toml']
subshell-does-not-leak-upward PASS ['inside=development', 'outside=unset']
```

生成的 `reports/environment_summary.md` 会把检查点整理成四项：哪些变量被 export，哪个启动文件或项目环境文件修改了它们，`PATH` 头部如何变化，哪些只是示例占位、哪些本地值不能提交。

## 常见错误

**把 shell 变量当成环境变量。** `FOO=bar` 只是在当前 shell 内部设置变量；程序读不到时先检查有没有 `export FOO`。

**把个人 `.bashrc` 当成项目依赖。** `.bashrc` 适合个人交互体验。项目需要的变量应放在项目文档、`env.sh`、`.env.example`、容器配置或 CI 配置里，并明确启用方式。

**在脚本里用 `source` 却以为会改父 shell。** 普通脚本是子进程，脚本里的 `source` 只改脚本进程自己。要改当前终端，必须在当前 shell 执行 `source ./env.sh`。

**把真实密钥写进 transcript。** transcript 应记录变量名、是否存在、非敏感示例值和配置路径。真实 secret 只应在本地密钥管理、未提交文件或安全的部署配置中出现。

**忽略 non-interactive shell。** CI、cron、systemd、Docker ENTRYPOINT 经常不是交互 shell。不要假设它们会读你的 `.bashrc`。

## 练习

1. 写一个 `env.sh`，导出 `APP_ENV=local` 并把 `./bin` 放到 `PATH` 前面。用 `command -v` 证明本地脚本被优先命中。
2. 用 `env -i HOME=/tmp/test-home PATH=/usr/bin:/bin bash --noprofile --norc -c 'env | sort'` 观察最小环境中有哪些变量。
3. 创建一个 `.env.example`，只写非敏感占位值；再写一段 README 说明如何复制为本地配置，但不要提交真实 secret。
4. 比较 `source ./env.sh`、`bash ./env.sh`、`( source ./env.sh; command )` 三种方式对当前 shell 的影响。

## 边界

本文只讲 Bash 和 Linux 进程环境的基础模型。Zsh、Fish、PowerShell、systemd unit、Docker Compose、Kubernetes、IDE run configuration 和 CI 都有自己的环境注入方式。把它们串起来时，仍然要回到同一个检查链：谁设置变量，谁继承变量，变量何时生效，证据在哪一行输出里。

## 参考资料

- [Bash Reference Manual: Bash Startup Files](https://www.gnu.org/software/bash/manual/bash.html#Bash-Startup-Files)
- [Bash Reference Manual: Bourne Shell Builtins](https://www.gnu.org/software/bash/manual/bash.html#Bourne-Shell-Builtins)
- [Linux man-pages: environ(7)](https://man7.org/linux/man-pages/man7/environ.7.html)
- [Linux man-pages: execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html)
- [GNU Coreutils manual: env invocation](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html)
- [Python documentation: venv](https://docs.python.org/3/library/venv.html)
- [The Twelve-Factor App: Config](https://12factor.net/config)
