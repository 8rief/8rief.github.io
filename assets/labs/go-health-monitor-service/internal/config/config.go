package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
	"strings"
)

// Target describes one HTTP endpoint monitored by the lab.
type Target struct {
	Name string `json:"name"`
	URL  string `json:"url"`
}

// LoadTargets reads and validates a JSON target list.
func LoadTargets(path string) ([]Target, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read config: %w", err)
	}
	var targets []Target
	if err := json.Unmarshal(data, &targets); err != nil {
		return nil, fmt.Errorf("parse config json: %w", err)
	}
	if len(targets) == 0 {
		return nil, errors.New("config must contain at least one target")
	}
	seen := map[string]struct{}{}
	for i, target := range targets {
		if err := validateTarget(target); err != nil {
			return nil, fmt.Errorf("target %d: %w", i, err)
		}
		key := strings.ToLower(target.Name)
		if _, ok := seen[key]; ok {
			return nil, fmt.Errorf("target %d: duplicate name %q", i, target.Name)
		}
		seen[key] = struct{}{}
	}
	return targets, nil
}

func validateTarget(target Target) error {
	if strings.TrimSpace(target.Name) == "" {
		return errors.New("name is required")
	}
	parsed, err := url.Parse(target.URL)
	if err != nil {
		return fmt.Errorf("invalid url: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return fmt.Errorf("unsupported url scheme %q", parsed.Scheme)
	}
	if parsed.Hostname() == "" {
		return errors.New("url host is required")
	}
	if !isLoopbackHost(parsed.Hostname()) {
		return fmt.Errorf("host %q is outside the local lab boundary", parsed.Hostname())
	}
	return nil
}

func isLoopbackHost(host string) bool {
	lower := strings.ToLower(host)
	if lower == "localhost" {
		return true
	}
	ip := net.ParseIP(lower)
	return ip != nil && ip.IsLoopback()
}
