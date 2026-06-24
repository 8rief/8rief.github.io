---
layout: post
title: "Go goroutines、channels 和标准工具链：用通信组织并发"
date: 2026-06-24 14:20:00 +0800
categories: computer-science-teaching
column: computer-science-teaching
column_title: "计算机技术教学"
excerpt: "用 goroutines、channels、context 和 Go 标准工具链，构建可测试的并发 worker pool。"
tags: [go, linux, goroutine, channel, concurrency, testing]
---
{% raw %}

> 主题：特色语言 / Go / goroutines / channels / 标准工具链  
> 本文命令已在 Ubuntu 24.04、Go 1.26.4 linux/amd64 环境下本地执行验证。实验使用 Go 官方二进制包，下载包 SHA256 已按 go.dev/dl 元数据校验。验证覆盖 `gofmt`、`go mod tidy`、`go test`、测试过滤、`go test -race`、`go vet`、`go run`，以及一个预期失败的数据竞争示例。

Rust 文章强调 ownership 和 borrow checker：让资源流动在编译阶段被检查。Go 的重点不同。Go 把并发放进语言和标准工具链：`go` 语句启动 goroutine，channel 在 goroutine 之间传值，`go test`、`go vet` 和 race detector 则把测试、静态检查和并发错误探测放进同一套命令里。

这篇文章抓住一条主线：**不要让多个 goroutine 直接争抢共享状态，优先用 channel 明确数据流和结果汇合点**。这不是说 mutex 没用；Go 官方文档也承认某些场景用锁更直接。工程上重要的是先画清数据从哪里来、由谁处理、在哪里汇总、取消信号如何传播，再选择 channel、mutex 或其他同步结构。

## 学习目标

读完并执行本文命令后，你应该能够：

1. 解释 goroutine、channel、worker pool、fan-out/fan-in 的关系。
2. 用 `context.Context` 给并发任务提供取消边界。
3. 写一个可测试的 channel worker pool，而不是把并发逻辑藏在 `main()` 里。
4. 用 `go test ./...`、`go test -run`、`go test -race`、`go vet ./...` 建立最小 Go 验证流。
5. 观察 race detector 如何报告两个 goroutine 对同一变量的冲突访问。

## 先修知识

建议先读：

- [Rust ownership、borrowing 和 Cargo：把资源流动交给编译器检查](/computer-science-teaching/2026/06/24/rust-ownership-borrowing-cargo.html)
- [GoogleTest 和可复现实验：让 C++ 测试能被定位、复跑和审计](/computer-science-teaching/2026/06/24/cpp-googletest-reproducible-tests.html)

需要知道：

- 函数、结构体、切片和错误返回的基本概念；
- 测试命令应该能复跑、能定位、能保存失败输出；
- 并发程序的难点通常不在“启动多个任务”，而在同步、取消、共享状态和结果汇合。

## 核心模型：goroutine 做事，channel 传递所有权式访问

Go 的经典建议是通过通信共享内存。Effective Go 和 Go codewalk 都强调：channel 可以在 goroutine 之间传递数据结构引用；如果把这种传递理解为“谁现在负责读写这份数据”，channel 就成了很自然的同步机制。

本文实验用一个 word-count worker pool 建立直觉：

![Go goroutine channel 工具链](/assets/diagrams/go-goroutines-channels-toolchain.svg)

数据流如下：

1. main goroutine 把 `Job` 发到 `jobCh`；
2. 多个 worker goroutine 从 `jobCh` 取任务；
3. worker 计算词数，把 `Result` 发到 `resultCh`；
4. 汇总方从 `resultCh` 收集结果；
5. `context.Context` 在取消时通知 feeder 和 worker 尽早退出；
6. `sync.WaitGroup` 等 worker 结束后关闭 `resultCh`。

channel 在这里承担两个作用：传递数据，同时建立同步点。发送和接收让 goroutine 之间的状态关系变得可见。

## 建立 Go module

创建目录：

```bash
mkdir -p go-goroutines-channels-toolchain/{pipeline,cmd/wordcount,race_demo,reports}
cd go-goroutines-channels-toolchain
```

写 `go.mod`：

```bash
cat > go.mod <<'MOD'
module example.com/go-pipeline-lab

go 1.26
MOD
```

本文不引入第三方依赖。这样可以把注意力集中在 Go 标准工具链和并发模型上。

## 写 worker pool 库

写 `pipeline/pipeline.go`：

```bash
cat > pipeline/pipeline.go <<'GO'
package pipeline

import (
	"context"
	"errors"
	"sort"
	"strings"
	"sync"
)

// Job is one piece of text that should be processed by a worker.
type Job struct {
	ID   int
	Text string
}

// Result is produced by a worker after processing one job.
type Result struct {
	JobID    int
	WorkerID int
	Words    int
}

// CountWords processes jobs with a fixed-size worker pool.
func CountWords(ctx context.Context, jobs []Job, workerCount int) ([]Result, error) {
	if workerCount <= 0 {
		return nil, errors.New("workerCount must be positive")
	}

	jobCh := make(chan Job)
	resultCh := make(chan Result)

	var wg sync.WaitGroup
	for workerID := 1; workerID <= workerCount; workerID++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for {
				select {
				case <-ctx.Done():
					return
				case job, ok := <-jobCh:
					if !ok {
						return
					}
					result := Result{
						JobID:    job.ID,
						WorkerID: id,
						Words:    len(strings.Fields(job.Text)),
					}
					select {
					case <-ctx.Done():
						return
					case resultCh <- result:
					}
				}
			}
		}(workerID)
	}

	go func() {
		defer close(jobCh)
		for _, job := range jobs {
			select {
			case <-ctx.Done():
				return
			case jobCh <- job:
			}
		}
	}()

	go func() {
		wg.Wait()
		close(resultCh)
	}()

	results := make([]Result, 0, len(jobs))
	for result := range resultCh {
		results = append(results, result)
	}

	if err := ctx.Err(); err != nil {
		return nil, err
	}

	sort.Slice(results, func(i, j int) bool {
		return results[i].JobID < results[j].JobID
	})
	return results, nil
}

// TotalWords sums the word counts in a result set.
func TotalWords(results []Result) int {
	total := 0
	for _, result := range results {
		total += result.Words
	}
	return total
}
GO
```

这段代码有几个关键边界：

- `jobCh` 只负责把 `Job` 分发给 worker；
- `resultCh` 只负责把 `Result` 汇回主 goroutine；
- feeder goroutine 在所有任务发送完后关闭 `jobCh`；
- 每个 worker 在 `jobCh` 关闭或 `ctx.Done()` 触发时退出；
- `WaitGroup` 等所有 worker 退出后关闭 `resultCh`；
- 收集完结果后按 `JobID` 排序，使测试输出稳定。

排序这一步很重要。并发执行会改变完成顺序，如果测试直接依赖完成顺序，就会变成偶发失败。工程测试要么接受无序结果，要么在汇总点做确定性排序。

## 写测试：正常路径、取消、边界和示例

写 `pipeline/pipeline_test.go`：

```bash
cat > pipeline/pipeline_test.go <<'GO'
package pipeline

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"
)

func TestCountWordsReturnsOneResultPerJob(t *testing.T) {
	jobs := []Job{
		{ID: 3, Text: "channels carry values"},
		{ID: 1, Text: "goroutines run functions"},
		{ID: 2, Text: "tests keep behavior visible"},
	}

	results, err := CountWords(context.Background(), jobs, 2)
	if err != nil {
		t.Fatalf("CountWords returned error: %v", err)
	}

	wantWords := map[int]int{1: 3, 2: 4, 3: 3}
	if len(results) != len(jobs) {
		t.Fatalf("got %d results, want %d", len(results), len(jobs))
	}
	for _, result := range results {
		if result.Words != wantWords[result.JobID] {
			t.Fatalf("job %d words=%d, want %d", result.JobID, result.Words, wantWords[result.JobID])
		}
		if result.WorkerID < 1 || result.WorkerID > 2 {
			t.Fatalf("worker id %d outside expected range", result.WorkerID)
		}
	}
	if TotalWords(results) != 10 {
		t.Fatalf("total words=%d, want 10", TotalWords(results))
	}
}

func TestCountWordsRejectsInvalidWorkerCount(t *testing.T) {
	_, err := CountWords(context.Background(), nil, 0)
	if err == nil {
		t.Fatal("expected an error for workerCount=0")
	}
}

func TestCountWordsReturnsContextCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := CountWords(ctx, []Job{{ID: 1, Text: "will not run"}}, 2)
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("err=%v, want context.Canceled", err)
	}
}

func TestCountWordsHandlesManyJobs(t *testing.T) {
	jobs := make([]Job, 100)
	for i := range jobs {
		jobs[i] = Job{ID: i + 1, Text: "one two three"}
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	results, err := CountWords(ctx, jobs, 8)
	if err != nil {
		t.Fatalf("CountWords returned error: %v", err)
	}
	if len(results) != 100 {
		t.Fatalf("len(results)=%d, want 100", len(results))
	}
	if TotalWords(results) != 300 {
		t.Fatalf("total words=%d, want 300", TotalWords(results))
	}
}

func ExampleCountWords() {
	results, err := CountWords(context.Background(), []Job{{ID: 1, Text: "go channels"}}, 1)
	if err != nil {
		panic(err)
	}
	fmt.Println(results[0].Words)
	// Output: 2
}
GO
```

这组测试覆盖四类情况：

1. 正常 worker pool 输出：每个 job 有一个 result，词数正确，worker id 在合理范围内；
2. 参数错误：`workerCount <= 0` 返回错误；
3. 取消路径：已经取消的 context 返回 `context.Canceled`；
4. 批量任务：100 个 job 在 8 个 worker 下完成，总词数稳定。

最后的 `ExampleCountWords` 是 Go 的 example test。它既是文档示例，也是 `go test` 会执行的测试。只要 `// Output:` 后的输出和真实输出不一致，测试就会失败。

## 写一个命令行入口

写 `cmd/wordcount/main.go`：

```bash
cat > cmd/wordcount/main.go <<'GO'
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"example.com/go-pipeline-lab/pipeline"
)

func main() {
	jobs := []pipeline.Job{
		{ID: 1, Text: "goroutines are lightweight concurrent functions"},
		{ID: 2, Text: "channels pass values between goroutines"},
		{ID: 3, Text: "tests and race detection make the workflow reproducible"},
	}

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	results, err := pipeline.CountWords(ctx, jobs, 3)
	if err != nil {
		log.Fatal(err)
	}
	for _, result := range results {
		fmt.Printf("job=%d worker=%d words=%d\n", result.JobID, result.WorkerID, result.Words)
	}
	fmt.Printf("total_words=%d\n", pipeline.TotalWords(results))
}
GO
```

命令行入口只组装输入、设置 timeout、调用库函数并打印结果。并发逻辑放在 `pipeline` 包里，测试才能直接覆盖。

## 运行标准验证流

执行：

```bash
gofmt -w pipeline cmd race_demo
go mod tidy
go test ./...
go test ./pipeline -run TestCountWordsReturnsOneResultPerJob -v
go test -race ./...
go vet ./...
go run ./cmd/wordcount
```

本地结果摘要：

```text
go test ./...
?    example.com/go-pipeline-lab/cmd/wordcount [no test files]
ok   example.com/go-pipeline-lab/pipeline      0.003s
?    example.com/go-pipeline-lab/race_demo     [no test files]

go test ./pipeline -run TestCountWordsReturnsOneResultPerJob -v
=== RUN   TestCountWordsReturnsOneResultPerJob
--- PASS: TestCountWordsReturnsOneResultPerJob (0.00s)
PASS

go test -race ./...
ok   example.com/go-pipeline-lab/pipeline      1.010s

go vet ./...                                  # 无输出，表示未发现报告项
```

`go run ./cmd/wordcount` 输出：

```text
job=1 worker=1 words=5
job=2 worker=2 words=5
job=3 worker=2 words=8
total_words=18
```

worker id 可能随调度变化，但 `job` 和 `words` 应保持一致。文章里的测试没有要求固定 worker id，只检查范围和汇总值。

## 观察 race detector 的失败输出

数据竞争示例不进入默认测试。写 `race_demo/race_demo_test.go`：

```bash
cat > race_demo/race_demo_test.go <<'GO'
//go:build race_demo

package race_demo

import "testing"

func TestIntentionalDataRace(t *testing.T) {
	counter := 0
	done := make(chan struct{}, 2)

	for i := 0; i < 2; i++ {
		go func() {
			for j := 0; j < 10000; j++ {
				counter++
			}
			done <- struct{}{}
		}()
	}

	<-done
	<-done
	if counter == 0 {
		t.Fatal("counter should have been incremented")
	}
}
GO
```

这个测试用 build tag `race_demo` 隔离。默认 `go test ./...` 不会执行它；需要显式打开：

```bash
go test -race -tags race_demo ./race_demo
```

本地得到预期失败，关键输出可以压缩成：

```text
WARNING: DATA RACE
Read at ... by goroutine ...
Previous write at ... by goroutine ...
--- FAIL: TestIntentionalDataRace
race detected during execution of test
FAIL
```

race detector 的边界也要说清楚。Go 官方文档说明，race detector 只能发现运行时实际执行到的 data race；测试覆盖不到的路径，它不能凭空证明安全。因此 `go test -race ./...` 是强证据，但不是完整证明。真实服务还应在接近真实负载的运行路径下使用 `-race` 构建或测试。

## 工具链各自负责什么

Go 的优势之一是常用工具都在标准 `go` 命令附近：

| 命令 | 作用 | 本文验证点 |
| --- | --- | --- |
| `gofmt -w` | 统一格式 | 修改源码后格式化并检查无差异 |
| `go mod tidy` | 整理 module 依赖 | 本文无外部依赖，但仍保证 `go.mod` 干净 |
| `go test ./...` | 跑所有包测试和 example | pipeline 包测试通过 |
| `go test -run ...` | 局部复跑 | 只跑一个目标测试 |
| `go test -race ./...` | 插桩检测运行时数据竞争 | 正常包 race 测试通过 |
| `go vet ./...` | 报告可疑构造 | 本文示例无报告 |
| `go run ./cmd/wordcount` | 运行可执行入口 | CLI 输出可解释结果 |

这套验证流比“直接运行 main”强得多。它把格式、模块依赖、单测、example、race detector、静态检查和可执行入口都纳入了同一条命令链。

## 常见错误

### 1. 把并发逻辑全部写进 main

`main()` 应该组装输入、处理命令行和输出结果。核心并发逻辑应该放进可测试的 package。这样测试可以直接调用 `CountWords()`，而不需要通过解析命令行输出验证行为。

### 2. 测试依赖 goroutine 完成顺序

goroutine 调度顺序不稳定。测试应该检查集合、总数、映射关系或排序后的结果。本文在 `CountWords()` 中按 `JobID` 排序，就是为了把并发完成顺序从 API 输出里隔离出去。

### 3. 只用 channel，不设计关闭规则

channel 关闭是协议的一部分。谁发送，谁关闭；接收方通常不关闭。本文由 feeder 关闭 `jobCh`，由等待 worker 的 goroutine 关闭 `resultCh`。如果关闭规则不清楚，很容易出现 panic、泄漏或阻塞。

### 4. 以为 `go test -race` 会证明没有数据竞争

race detector 只能检查实际执行路径。没有跑到的代码不会被检查。它适合做 release gate 和调试工具，但不能替代测试覆盖、代码审查和清晰的同步设计。

## 实践检查清单

为一个 Go 并发小项目建立验证流时，可以按这个顺序检查：

1. 并发逻辑是否在可测试 package 中，而不是只在 `main()` 中？
2. 输入 channel、输出 channel 和关闭责任是否清晰？
3. 是否有 `context.Context` 或其他取消边界？
4. 测试是否避免依赖 goroutine 调度顺序？
5. 是否有 `go test ./...` 和目标测试过滤命令？
6. 是否跑过 `go test -race ./...`？
7. 是否跑过 `go vet ./...`？
8. 是否保留了一个可解释的 race detector 失败样例，帮助理解工具输出？

## 练习

1. 给 `CountWords()` 增加一个带缓冲的 `jobCh`，比较无缓冲和缓冲 channel 的行为差异。
2. 增加一个 `MaxWords` 字段，让 worker 在某个 job 超过阈值时通过 context 取消整条 pipeline。
3. 把结果排序移出 `CountWords()`，改为由测试自己排序，比较 API 设计差异。
4. 用 `sync.Mutex` 修复 `race_demo`，再用 `go test -race -tags race_demo ./race_demo` 验证 race 消失。

## 参考资料

- [Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency)
- [Go Codewalk: Share Memory By Communicating](https://go.dev/doc/codewalk/sharemem/)
- [Data Race Detector](https://go.dev/doc/articles/race_detector)
- [cmd/go: go command documentation](https://pkg.go.dev/cmd/go)
- [cmd/vet: vet command documentation](https://pkg.go.dev/cmd/vet)

{% endraw %}
