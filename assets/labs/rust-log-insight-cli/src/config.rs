use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::{fs, path::Path};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AppConfig {
    pub error_rate_warning: f64,
    pub slow_latency_ms: u64,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            error_rate_warning: 0.25,
            slow_latency_ms: 50,
        }
    }
}

impl AppConfig {
    pub fn load(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let text = fs::read_to_string(path)
            .with_context(|| format!("read config file {}", path.display()))?;
        let config: Self = toml::from_str(&text)
            .with_context(|| format!("parse TOML config {}", path.display()))?;
        config.validate()?;
        Ok(config)
    }

    pub fn validate(&self) -> Result<()> {
        anyhow::ensure!(
            (0.0..=1.0).contains(&self.error_rate_warning),
            "error_rate_warning must be between 0 and 1"
        );
        anyhow::ensure!(self.slow_latency_ms > 0, "slow_latency_ms must be positive");
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::AppConfig;

    #[test]
    fn validates_error_rate_range() {
        let config = AppConfig {
            error_rate_warning: 1.2,
            slow_latency_ms: 10,
        };
        assert!(config.validate().is_err());
    }
}
