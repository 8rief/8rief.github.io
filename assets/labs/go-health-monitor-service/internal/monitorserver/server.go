package monitorserver

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"example.com/go-health-monitor-service/internal/checker"
	"example.com/go-health-monitor-service/internal/config"
)

// NewMonitorHandler returns the local HTTP API used by the capstone.
func NewMonitorHandler(targets []config.Target, client checker.HTTPClient, workers int, timeout time.Duration, logger *slog.Logger) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("GET /api/checks", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), timeout)
		defer cancel()
		results := checker.CheckAll(ctx, client, targets, workers)
		logger.Info("checks completed", "count", len(results))
		writeJSON(w, http.StatusOK, results)
	})
	return mux
}

// NewDemoTargetHandler creates deterministic local targets for the lab transcript.
func NewDemoTargetHandler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /ok", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("GET /fail", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"status": "failed"})
	})
	mux.HandleFunc("GET /slow", func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(200 * time.Millisecond)
		writeJSON(w, http.StatusOK, map[string]string{"status": "slow-ok"})
	})
	return mux
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
