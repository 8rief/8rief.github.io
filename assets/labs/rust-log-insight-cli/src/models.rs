use serde::{Deserialize, Serialize};
use std::{collections::BTreeMap, fmt, str::FromStr};
use thiserror::Error;

#[derive(Debug, Error, Clone, PartialEq, Eq)]
#[error("unknown log level {0:?}")]
pub struct LevelParseError(pub String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Level {
    Debug,
    Info,
    Warn,
    Error,
}

impl Level {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Debug => "DEBUG",
            Self::Info => "INFO",
            Self::Warn => "WARN",
            Self::Error => "ERROR",
        }
    }
}

impl fmt::Display for Level {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

impl FromStr for Level {
    type Err = LevelParseError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value {
            "DEBUG" => Ok(Self::Debug),
            "INFO" => Ok(Self::Info),
            "WARN" | "WARNING" => Ok(Self::Warn),
            "ERROR" => Ok(Self::Error),
            other => Err(LevelParseError(other.to_owned())),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LogRecord {
    pub timestamp: String,
    pub level: Level,
    pub service: String,
    pub message: String,
    pub latency_ms: Option<u64>,
    pub fields: BTreeMap<String, String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LevelCount {
    pub level: Level,
    pub count: usize,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ServiceCount {
    pub service: String,
    pub count: usize,
    pub errors: usize,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Summary {
    pub total: usize,
    pub errors: usize,
    pub warnings: usize,
    pub slow_events: usize,
    pub error_rate: f64,
    pub level_counts: Vec<LevelCount>,
    pub service_counts: Vec<ServiceCount>,
}
