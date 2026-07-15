package checker

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"example.com/go-health-monitor-service/internal/config"
)

// Result is the observable outcome of one target check.
type Result struct {
	Name       string `json:"name"`
	URL        string `json:"url"`
	OK         bool   `json:"ok"`
	StatusCode int    `json:"status_code"`
	LatencyMS  int64  `json:"latency_ms"`
	Error      string `json:"error,omitempty"`
	CheckedAt  string `json:"checked_at"`
}

// HTTPClient is the part of http.Client used by the checker.
type HTTPClient interface {
	Do(req *http.Request) (*http.Response, error)
}

// Check sends one GET request and records status, latency, and error state.
func Check(ctx context.Context, client HTTPClient, target config.Target) Result {
	start := time.Now()
	result := Result{
		Name:      target.Name,
		URL:       target.URL,
		CheckedAt: start.UTC().Format(time.RFC3339),
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.URL, nil)
	if err != nil {
		result.Error = fmt.Sprintf("build request: %v", err)
		result.LatencyMS = elapsedMillis(start)
		return result
	}
	resp, err := client.Do(req)
	if err != nil {
		result.Error = fmt.Sprintf("request failed: %v", err)
		result.LatencyMS = elapsedMillis(start)
		return result
	}
	defer resp.Body.Close()
	result.StatusCode = resp.StatusCode
	result.OK = resp.StatusCode >= 200 && resp.StatusCode < 400
	result.LatencyMS = elapsedMillis(start)
	return result
}

// CheckAll runs checks with bounded worker concurrency and preserves input order.
func CheckAll(ctx context.Context, client HTTPClient, targets []config.Target, workers int) []Result {
	if workers < 1 {
		workers = 1
	}
	if workers > len(targets) && len(targets) > 0 {
		workers = len(targets)
	}
	type job struct {
		index  int
		target config.Target
	}
	jobs := make(chan job)
	results := make([]Result, len(targets))
	var wg sync.WaitGroup
	for range workers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for item := range jobs {
				results[item.index] = Check(ctx, client, item.target)
			}
		}()
	}
	for i, target := range targets {
		select {
		case <-ctx.Done():
			results[i] = Result{Name: target.Name, URL: target.URL, Error: ctx.Err().Error(), CheckedAt: time.Now().UTC().Format(time.RFC3339)}
		case jobs <- job{index: i, target: target}:
		}
	}
	close(jobs)
	wg.Wait()
	return results
}

func elapsedMillis(start time.Time) int64 {
	elapsed := time.Since(start).Milliseconds()
	if elapsed < 0 {
		return 0
	}
	return elapsed
}
