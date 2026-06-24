---
layout: post
title: "Rust ownership、borrowing 和 Cargo：把资源流动交给编译器检查"
date: 2026-06-24 13:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
tags: [rust, linux, ownership, borrowing, cargo, reproducibility]
---
{% raw %}

> 主题：特色语言 / Rust / ownership / borrowing / Cargo  
> 本文命令已在 Ubuntu 24.04、Rust 1.95.0、Cargo 1.95.0、rustfmt 1.9.0 环境下本地执行验证。实验覆盖 `cargo fmt --check`、`cargo check --locked`、`cargo test --locked`、单测过滤、`cargo run --locked`、`cargo doc --locked --no-deps`，以及 3 个预期失败的 borrow checker 例子。

前面 6 篇 C++ 文章把资源生命周期、所有权、构建系统和测试体系串了一遍。Rust 适合作为第一个特色语言主题，因为它把 C++ 里需要靠 RAII、智能指针和代码审查共同维护的资源边界，进一步推到了语言类型系统和编译器检查里。

这篇文章不把 Rust 当成“另一种语法”来讲，而是抓住一条工程主线：一个值在什么时候被拥有、什么时候被借用、什么时候可以修改、什么时候会被释放。Cargo 则把这些检查组织成固定工作流，让格式、编译检查、测试、文档测试和可执行示例都能复现。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 ownership、move、borrow、mutable borrow 和 lifetime 的基本关系。
2. 用 `cargo fmt --check`、`cargo check --locked`、`cargo test --locked` 建立最小 Rust 验证流。
3. 写包含 unit test、integration test 和 doc test 的小型 Cargo 项目。
4. 复现 `E0382`、`E0499`、`E0106` 这三类常见 borrow checker 错误。
5. 把 Rust 的所有权模型和前面 C++ 的 RAII/`unique_ptr`/`shared_ptr` 做概念对照。

## 先修知识

建议先读：

- [RAII 和资源生命周期：让 C++ 对象负责释放资源](/computer-science-teaching/2026/06/24/cpp-raii-resource-lifetime.html)
- [unique_ptr、shared_ptr 和 raw pointer：把所有权写进类型](/computer-science-teaching/2026/06/24/cpp-ownership-smart-pointers.html)
- [GoogleTest 和可复现实验：让 C++ 测试能被定位、复跑和审计](/computer-science-teaching/2026/06/24/cpp-googletest-reproducible-tests.html)

需要知道：

- C++ 中“谁拥有资源、谁释放资源”的问题；
- 基本命令行和项目目录结构；
- 测试应当能复跑、能定位、能保存失败证据。

## 核心模型：一个值只有一个 owner，借用必须受约束

Rust Book 对 ownership 的解释是：ownership 是 Rust 最独特的特性，它让 Rust 在不使用垃圾回收器的情况下提供内存安全保证。它的规则可以压缩成三点：每个值有一个 owner；同一时刻只有一个 owner；owner 离开作用域时值被 drop。

借用规则解决的是“访问但不接管”的问题：`&T` 是不可变借用，`&mut T` 是可变借用。编译器要求同一段时间内要么有多个不可变借用，要么有一个可变借用。这个限制把“读者和写者同时访问同一对象”的风险提前到了编译阶段。

![Rust ownership 和 Cargo 工作流](/assets/diagrams/rust-ownership-cargo.svg)

可以用这张对照表建立直觉：

| 问题 | C++ 常见表达 | Rust 表达 |
| --- | --- | --- |
| 独占拥有 | `std::unique_ptr<T>` 或值对象 | 值的 owner，move 后原变量不可用 |
| 只读观察 | `const T&` 或 `const T*` | `&T` |
| 独占修改 | `T&`、`T*`，靠约定避免别名写 | `&mut T`，编译器阻止同时多写 |
| 生命周期边界 | RAII 析构、智能指针、审查 | owner 作用域结束自动 drop，borrow checker 检查引用有效性 |
| 构建和验证 | CMake/Ninja/CTest | Cargo fmt/check/test/doc/run |

## 建立 Cargo 项目

创建目录：

```bash
mkdir -p rust-ownership-cargo/{src,tests,compile_fail,reports}
cd rust-ownership-cargo
```

写 `Cargo.toml`：

```bash
cat > Cargo.toml <<'TOML'
[package]
name = "ownership_lab"
version = "0.1.0"
edition = "2024"

[dependencies]
TOML
```

这里使用 2024 edition，且不引入第三方依赖。实验重点是 ownership/borrowing 和 Cargo 自带工作流。

## 写一个能体现所有权的库

写 `src/lib.rs`：

```bash
cat > src/lib.rs <<'RS'
//! Small examples for ownership, borrowing, lifetimes, and Cargo tests.
//!
//! ```
//! use ownership_lab::{Document, append_suffix, title_view};
//!
//! let mut doc = Document::new("note", "rust ownership keeps resource flow explicit");
//! assert_eq!(title_view(&doc), "note");
//! append_suffix(&mut doc, "-v2");
//! assert_eq!(doc.title(), "note-v2");
//! ```

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Document {
    title: String,
    body: String,
}

impl Document {
    pub fn new(title: impl Into<String>, body: impl Into<String>) -> Self {
        Self {
            title: title.into(),
            body: body.into(),
        }
    }

    pub fn title(&self) -> &str {
        &self.title
    }

    pub fn body(&self) -> &str {
        &self.body
    }

    pub fn append_to_title(&mut self, suffix: &str) {
        self.title.push_str(suffix);
    }

    pub fn word_count(&self) -> usize {
        self.body.split_whitespace().count()
    }

    pub fn into_parts(self) -> (String, String) {
        (self.title, self.body)
    }
}

pub fn consume_document(doc: Document) -> usize {
    doc.word_count()
}

pub fn title_view(doc: &Document) -> &str {
    doc.title()
}

pub fn append_suffix(doc: &mut Document, suffix: &str) {
    doc.append_to_title(suffix);
}

pub fn longer_title<'a>(left: &'a Document, right: &'a Document) -> &'a str {
    if left.title().len() >= right.title().len() {
        left.title()
    } else {
        right.title()
    }
}

pub fn first_word(text: &str) -> &str {
    text.split_whitespace().next().unwrap_or("")
}

pub fn summarize(doc: &Document) -> String {
    format!(
        "{}: {} words, first word: {}",
        doc.title(),
        doc.word_count(),
        first_word(doc.body())
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn borrowing_does_not_consume_the_document() {
        let doc = Document::new("borrow", "read without taking ownership");
        assert_eq!(title_view(&doc), "borrow");
        assert_eq!(doc.word_count(), 4);
    }

    #[test]
    fn mutable_borrow_allows_controlled_update() {
        let mut doc = Document::new("draft", "change one owner through one mutable borrow");
        append_suffix(&mut doc, "-reviewed");
        assert_eq!(doc.title(), "draft-reviewed");
    }

    #[test]
    fn owning_function_consumes_value() {
        let doc = Document::new("owned", "move into the function");
        assert_eq!(consume_document(doc), 4);
    }

    #[test]
    fn explicit_lifetime_ties_result_to_inputs() {
        let short = Document::new("a", "body");
        let long = Document::new("long-title", "body");
        assert_eq!(longer_title(&short, &long), "long-title");
    }

    #[test]
    fn summarize_builds_stable_output() {
        let doc = Document::new("note", "rust makes ownership visible");
        assert_eq!(summarize(&doc), "note: 4 words, first word: rust");
    }
}
RS
```

这段代码里有几类典型边界：

- `Document` 拥有两个 `String`；
- `title(&self) -> &str` 和 `body(&self) -> &str` 返回只读借用；
- `append_to_title(&mut self, ...)` 要求独占可变借用；
- `into_parts(self)` 消费 `self`，把两个 `String` 所有权交出去；
- `longer_title<'a>(...) -> &'a str` 用显式 lifetime 表示返回引用来自两个输入之一；
- doc comment 中的代码块会被 `cargo test` 当作 doctest 运行。

写命令行入口 `src/main.rs`：

```bash
cat > src/main.rs <<'RS'
use ownership_lab::{Document, append_suffix, consume_document, summarize, title_view};

fn main() {
    let mut doc = Document::new("cargo-lab", "ownership borrowing and cargo form a workflow");
    println!("borrowed title: {}", title_view(&doc));
    append_suffix(&mut doc, "-v1");
    println!("after mutable borrow: {}", summarize(&doc));
    let count = consume_document(doc);
    println!("consumed document word count: {count}");
}
RS
```

这个入口刻意按顺序展示三件事：先不可变借用标题，再通过 `&mut` 修改标题，最后把整个文档 move 进 `consume_document()`。move 之后原变量不能再使用。

## 写 integration test

写 `tests/workflow.rs`：

```bash
cat > tests/workflow.rs <<'RS'
use ownership_lab::{Document, append_suffix, longer_title, summarize};

#[test]
fn integration_test_uses_public_api() {
    let mut doc = Document::new("integration", "public api should be enough");
    append_suffix(&mut doc, "-ok");
    assert_eq!(
        summarize(&doc),
        "integration-ok: 5 words, first word: public"
    );
}

#[test]
fn longer_title_returns_a_borrowed_input() {
    let a = Document::new("short", "one");
    let b = Document::new("much-longer", "two");
    let view = longer_title(&a, &b);
    assert_eq!(view, "much-longer");
}
RS
```

`src/lib.rs` 里的 `#[cfg(test)] mod tests` 是 unit test，可以访问当前模块内部。`tests/workflow.rs` 是 integration test，只通过 crate 的 public API 使用库。这一点很重要：integration test 更接近外部使用者视角，能检查公开接口是否足够稳定。

## 格式、检查、测试、运行

先生成 lockfile，再跑固定验证流：

```bash
cargo generate-lockfile
cargo fmt -- --check
cargo check --locked
cargo test --locked
cargo test --locked borrowing_does_not_consume_the_document
cargo run --locked
cargo doc --locked --no-deps
```

本地验证结果摘要：

```text
cargo fmt -- --check              # 通过
cargo check --locked              # 通过
cargo test --locked               # unit tests 5 passed, integration tests 2 passed, doctest 1 passed
cargo test --locked borrowing...  # 只复跑 1 个目标单测
cargo run --locked                # 输出借用、修改、消费三步结果
cargo doc --locked --no-deps      # 生成本 crate 文档
```

`cargo run --locked` 的输出：

```text
borrowed title: cargo-lab
after mutable borrow: cargo-lab-v1: 7 words, first word: ownership
consumed document word count: 7
```

这说明值先被借用，然后被可变借用修改，最后被 move 到消费函数里。验证命令中使用 `--locked`，是为了要求 Cargo 使用当前 `Cargo.lock`，避免依赖解析结果在不同机器或不同时间发生变化。本文项目没有第三方依赖，但这个习惯在真实项目里很重要。

## 预期失败 1：move 后继续使用

写 `compile_fail/use_after_move.rs`：

```bash
cat > compile_fail/use_after_move.rs <<'RS'
struct Document {
    title: String,
}

fn consume(doc: Document) -> usize {
    doc.title.len()
}

fn main() {
    let doc = Document { title: String::from("move") };
    let len = consume(doc);
    println!("{len}");
    println!("{}", doc.title);
}
RS
```

编译：

```bash
rustc --edition=2024 compile_fail/use_after_move.rs -o target/use_after_move
```

本地得到预期错误：

```text
error[E0382]: borrow of moved value: `doc`
value moved here
value borrowed here after move
```

`consume(doc)` 接管了 `doc` 的所有权。调用之后，原来的 `doc` 变量不再可用。这和 C++ 中把 `unique_ptr` move 进函数后的状态很接近，但 Rust 编译器会直接禁止继续使用已 move 的值。

## 预期失败 2：同时存在两个可变借用

写 `compile_fail/two_mut_borrows.rs`：

```bash
cat > compile_fail/two_mut_borrows.rs <<'RS'
fn main() {
    let mut title = String::from("draft");
    let first = &mut title;
    let second = &mut title;
    first.push_str("-one");
    second.push_str("-two");
    println!("{title}");
}
RS
```

编译：

```bash
rustc --edition=2024 compile_fail/two_mut_borrows.rs -o target/two_mut_borrows
```

本地得到预期错误：

```text
error[E0499]: cannot borrow `title` as mutable more than once at a time
first mutable borrow occurs here
second mutable borrow occurs here
```

这条规则对应的是写权限排他性。同一时间只能有一个 `&mut`。如果两个可变引用同时存在，谁先写、谁后写、原值是否仍然有效都会变得难以审查。Rust 把这种风险限制在编译阶段。

## 预期失败 3：返回悬垂引用

写 `compile_fail/dangling_reference.rs`：

```bash
cat > compile_fail/dangling_reference.rs <<'RS'
fn dangling() -> &str {
    let local = String::from("temporary");
    &local
}

fn main() {
    println!("{}", dangling());
}
RS
```

编译：

```bash
rustc --edition=2024 compile_fail/dangling_reference.rs -o target/dangling_reference
```

本地得到预期错误：

```text
error[E0106]: missing lifetime specifier
this function's return type contains a borrowed value, but there is no value for it to be borrowed from
```

`local` 在函数结束时会被释放，返回 `&local` 会制造悬垂引用。Rust 不允许函数返回一个没有来源约束的借用。编译器甚至会提示：你可能应该返回 owned `String`，而不是 `&str`。

## Cargo 工作流的工程意义

把这组命令连起来，能形成一个很小但有实际价值的 Rust release gate：

```bash
cargo fmt -- --check
cargo check --locked
cargo test --locked
cargo doc --locked --no-deps
```

它们分别回答不同问题：

- `cargo fmt -- --check`：代码格式是否稳定；
- `cargo check --locked`：类型、借用、生命周期、模块依赖是否能通过快速编译检查；
- `cargo test --locked`：unit test、integration test、doctest 是否通过；
- `cargo doc --locked --no-deps`：公开 API 文档是否能生成，文档代码是否和实现保持一致。

如果要和 C++ 工作流对照，可以把 `cargo check` 理解为一次很强的静态边界检查，把 `cargo test` 理解为 CTest/GoogleTest 式行为验证，把 `cargo doc` 理解为“文档示例也必须能编译运行”的接口约束。

## 常见错误

### 1. 为了绕过 borrow checker 到处 clone

`clone()` 会复制数据，有时是正确选择，例如确实需要两个独立 owned value。为了让代码编译而盲目 clone，会掩盖真正的所有权设计问题。先判断函数是否真的需要接管所有权；如果只读，用 `&T`；如果要修改，用 `&mut T`；如果需要保存，才考虑 owned value。

### 2. 把 lifetime 当成“延长生命周期”的语法

Lifetime annotation 不会让值活得更久。它只是描述引用之间的关系，让编译器知道返回引用来自哪里。`longer_title<'a>(...) -> &'a str` 的含义是返回值的有效期不超过两个输入引用的共同有效范围。

### 3. 忽略 doctest

Rust 文档里的代码块默认可以被测试。对公共 API 来说，这很有价值：文档示例和真实接口不容易漂移。写文档时要把示例当成可执行合同，而不是只给读者看的伪代码。

### 4. 不保存 compile-fail 证据

借用错误往往是学习 Rust 的关键材料。本文把 3 个失败例子放在 `compile_fail/`，并把 `rustc` 的错误输出保存到 `reports/`。这样可以反复对照错误码、出错位置和修复方向。

## 实践检查清单

开始一个小型 Rust 项目时，可以先建立这条检查线：

1. `Cargo.toml` 是否明确 edition？
2. 是否提交 `Cargo.lock`，并在验证命令里使用 `--locked`？
3. 是否有 unit test、integration test 和至少一个 doctest？
4. 是否能用测试名过滤复跑单个测试？
5. 是否有 compile-fail 示例帮助理解 move、可变借用和悬垂引用？
6. 是否把 `cargo fmt -- --check`、`cargo check --locked`、`cargo test --locked` 放进固定验证流程？
7. 公共 API 文档是否能通过 `cargo doc --locked --no-deps` 生成？

## 练习

1. 把 `consume_document(doc)` 改成 `consume_document(&doc)`，观察函数签名和调用方使用方式如何变化。
2. 给 `Document` 增加 `tags: Vec<String>`，写一个函数返回第一个 tag 的 `Option<&str>`，说明返回引用来自哪里。
3. 把 `first_word()` 改成返回 owned `String`，比较调用方是否还需要 lifetime 约束。
4. 增加一个 integration test，验证 `into_parts(self)` 会消费 `Document` 并返回两个 owned `String`。

## 参考资料

- [The Rust Programming Language: Understanding Ownership](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
- [The Rust Programming Language: References and Borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html)
- [The Rust Programming Language: Validating References with Lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html)
- [The Cargo Book: cargo test](https://doc.rust-lang.org/cargo/commands/cargo-test.html)
- [The Cargo Book: cargo check](https://doc.rust-lang.org/cargo/commands/cargo-check.html)
- [The Cargo Book: cargo run](https://doc.rust-lang.org/cargo/commands/cargo-run.html)

{% endraw %}
