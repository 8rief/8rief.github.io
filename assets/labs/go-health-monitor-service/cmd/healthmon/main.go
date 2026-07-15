package main

import (
	"context"
	"errors"
	"flag"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"example.com/go-health-monitor-service/internal/checker"
	"example.com/go-health-monitor-service/internal/config"
	"example.com/go-health-monitor-service/internal/monitorserver"
	"example.com/go-health-monitor-service/internal/report"
)

func main() {
	logger := slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: slog.LevelInfo}))
	if err := run(os.Args[1:], logger); err != nil {
		logger.Error("command failed", "error", err)
		os.Exit(1)
	}
}

func run(args []string, logger *slog.Logger) error {
	if len(args) == 0 {
		return usageError()
	}
	switch args[0] {
	case "check":
		return runCheck(args[1:], logger)
	case "serve":
		return runServe(args[1:], logger)
	case "demo":
		return runDemo(args[1:], logger)
	case "help", "-h", "--help":
		printUsage()
		return nil
	default:
		return usageError()
	}
}

func runCheck(args []string, logger *slog.Logger) error {
	fs := flag.NewFlagSet("check", flag.ContinueOnError)
	configPath := fs.String("config", "sample_config/targets.json", "path to target JSON")
	jsonPath := fs.String("json", "reports/results.json", "path for JSON report")
	csvPath := fs.String("csv", "reports/results.csv", "path for CSV report")
	workers := fs.Int("workers", 2, "maximum concurrent checks")
	timeout := fs.Duration("timeout", 800*time.Millisecond, "request timeout")
	if err := fs.Parse(args); err != nil {
		return err
	}
	targets, err := config.LoadTargets(*configPath)
	if err != nil {
		return err
	}
	client := &http.Client{Timeout: *timeout}
	ctx, cancel := context.WithTimeout(context.Background(), *timeout*time.Duration(len(targets)+1))
	defer cancel()
	results := checker.CheckAll(ctx, client, targets, *workers)
	if err := report.WriteJSON(*jsonPath, results); err != nil {
		return err
	}
	if err := report.WriteCSV(*csvPath, results); err != nil {
		return err
	}
	okCount := 0
	for _, result := range results {
		if result.OK {
			okCount++
		}
	}
	logger.Info("checks finished", "ok", okCount, "total", len(results), "json", *jsonPath, "csv", *csvPath)
	return nil
}

func runServe(args []string, logger *slog.Logger) error {
	fs := flag.NewFlagSet("serve", flag.ContinueOnError)
	addr := fs.String("addr", "127.0.0.1:18190", "listen address")
	configPath := fs.String("config", "sample_config/targets.json", "path to target JSON")
	workers := fs.Int("workers", 2, "maximum concurrent checks")
	timeout := fs.Duration("timeout", 800*time.Millisecond, "request timeout")
	if err := fs.Parse(args); err != nil {
		return err
	}
	targets, err := config.LoadTargets(*configPath)
	if err != nil {
		return err
	}
	client := &http.Client{Timeout: *timeout}
	handler := monitorserver.NewMonitorHandler(targets, client, *workers, *timeout, logger)
	return serveWithShutdown(*addr, handler, logger)
}

func runDemo(args []string, logger *slog.Logger) error {
	fs := flag.NewFlagSet("demo", flag.ContinueOnError)
	addr := fs.String("addr", "127.0.0.1:18191", "listen address")
	if err := fs.Parse(args); err != nil {
		return err
	}
	return serveWithShutdown(*addr, monitorserver.NewDemoTargetHandler(), logger)
}

func serveWithShutdown(addr string, handler http.Handler, logger *slog.Logger) error {
	server := &http.Server{
		Addr:              addr,
		Handler:           handler,
		ReadHeaderTimeout: 2 * time.Second,
	}
	serverErrors := make(chan error, 1)
	go func() {
		logger.Info("server listening", "addr", addr)
		serverErrors <- server.ListenAndServe()
	}()
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	select {
	case err := <-serverErrors:
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return err
	case <-stop:
		logger.Info("shutdown requested", "addr", addr)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	return server.Shutdown(ctx)
}

func usageError() error {
	printUsage()
	return errors.New("expected one of: check, serve, demo")
}

func printUsage() {
	fmt.Fprintln(os.Stderr, "usage: healthmon <check|serve|demo> [flags]")
}
