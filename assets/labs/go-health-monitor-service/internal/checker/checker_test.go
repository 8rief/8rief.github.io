package checker

import (
	"context"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"example.com/go-health-monitor-service/internal/config"
)

func TestCheckRecordsHTTPStatus(t *testing.T) {
	server := newIPv4TestServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusTeapot)
	}))
	defer server.Close()

	client := server.Client()
	result := Check(context.Background(), client, config.Target{Name: "teapot", URL: server.URL})
	if result.OK {
		t.Fatal("expected non-OK result for status 418")
	}
	if result.StatusCode != http.StatusTeapot {
		t.Fatalf("StatusCode=%d, want 418", result.StatusCode)
	}
}

func TestCheckHonorsContextTimeout(t *testing.T) {
	server := newIPv4TestServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(100 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel()
	result := Check(ctx, server.Client(), config.Target{Name: "slow", URL: server.URL})
	if result.Error == "" {
		t.Fatal("expected timeout error")
	}
}

func TestCheckAllPreservesInputOrder(t *testing.T) {
	server := newIPv4TestServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/fail" {
			w.WriteHeader(http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	targets := []config.Target{
		{Name: "one", URL: server.URL + "/one"},
		{Name: "two", URL: server.URL + "/fail"},
		{Name: "three", URL: server.URL + "/three"},
	}
	results := CheckAll(context.Background(), server.Client(), targets, 8)
	if len(results) != len(targets) {
		t.Fatalf("len(results)=%d, want %d", len(results), len(targets))
	}
	for i := range targets {
		if results[i].Name != targets[i].Name {
			t.Fatalf("results[%d].Name=%q, want %q", i, results[i].Name, targets[i].Name)
		}
	}
	if results[1].OK {
		t.Fatal("second target should be non-OK")
	}
}

func newIPv4TestServer(t *testing.T, handler http.Handler) *httptest.Server {
	t.Helper()
	listener, err := net.Listen("tcp4", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen on local IPv4: %v", err)
	}
	server := httptest.NewUnstartedServer(handler)
	server.Listener = listener
	server.Start()
	return server
}
