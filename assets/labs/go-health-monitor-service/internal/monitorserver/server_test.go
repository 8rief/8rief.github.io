package monitorserver

import (
	"encoding/json"
	"log/slog"
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"example.com/go-health-monitor-service/internal/checker"
	"example.com/go-health-monitor-service/internal/config"
)

func TestMonitorAPIRunsChecks(t *testing.T) {
	target := newIPv4TestServer(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer target.Close()

	handler := NewMonitorHandler(
		[]config.Target{{Name: "target", URL: target.URL}},
		target.Client(),
		2,
		500*time.Millisecond,
		slog.Default(),
	)
	server := newIPv4TestServer(t, handler)
	defer server.Close()

	resp, err := server.Client().Get(server.URL + "/api/checks")
	if err != nil {
		t.Fatalf("GET /api/checks: %v", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status=%d, want 200", resp.StatusCode)
	}
	var results []checker.Result
	if err := json.NewDecoder(resp.Body).Decode(&results); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if len(results) != 1 || !results[0].OK {
		t.Fatalf("unexpected results: %#v", results)
	}
}

func TestDemoTargetHandler(t *testing.T) {
	server := newIPv4TestServer(t, NewDemoTargetHandler())
	defer server.Close()

	cases := map[string]int{"/ok": http.StatusOK, "/fail": http.StatusInternalServerError, "/slow": http.StatusOK}
	for path, wantStatus := range cases {
		resp, err := server.Client().Get(server.URL + path)
		if err != nil {
			t.Fatalf("GET %s: %v", path, err)
		}
		_ = resp.Body.Close()
		if resp.StatusCode != wantStatus {
			t.Fatalf("%s status=%d, want %d", path, resp.StatusCode, wantStatus)
		}
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
