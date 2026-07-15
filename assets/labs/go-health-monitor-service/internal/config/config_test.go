package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeTempConfig(t *testing.T, body string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "targets.json")
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatalf("write config: %v", err)
	}
	return path
}

func TestLoadTargetsAcceptsLoopbackTargets(t *testing.T) {
	path := writeTempConfig(t, `[{"name":"api","url":"http://127.0.0.1:18080/health"},{"name":"local","url":"http://localhost:18080/health"}]`)
	targets, err := LoadTargets(path)
	if err != nil {
		t.Fatalf("LoadTargets returned error: %v", err)
	}
	if got := len(targets); got != 2 {
		t.Fatalf("len(targets)=%d, want 2", got)
	}
}

func TestLoadTargetsRejectsExternalHost(t *testing.T) {
	path := writeTempConfig(t, `[{"name":"external","url":"https://example.com"}]`)
	_, err := LoadTargets(path)
	if err == nil {
		t.Fatal("LoadTargets accepted an external host")
	}
	if !strings.Contains(err.Error(), "outside the local lab boundary") {
		t.Fatalf("unexpected error: %v", err)
	}
}

func TestLoadTargetsRejectsDuplicateNames(t *testing.T) {
	path := writeTempConfig(t, `[{"name":"api","url":"http://127.0.0.1:1/a"},{"name":"API","url":"http://127.0.0.1:1/b"}]`)
	_, err := LoadTargets(path)
	if err == nil || !strings.Contains(err.Error(), "duplicate") {
		t.Fatalf("expected duplicate-name error, got %v", err)
	}
}
