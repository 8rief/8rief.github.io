use crate::models::{Level, LogRecord};
use std::{collections::BTreeMap, str::FromStr};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum ParseLogError {
    #[error("line must contain at least timestamp, level, service, and message")]
    MissingColumns,
    #[error("invalid level: {0}")]
    InvalidLevel(String),
    #[error("latency_ms must be an unsigned integer, got {0:?}")]
    InvalidLatency(String),
}

pub fn parse_line(line: &str) -> Result<LogRecord, ParseLogError> {
    let mut parts = line.split_whitespace();
    let timestamp = parts
        .next()
        .ok_or(ParseLogError::MissingColumns)?
        .to_owned();
    let level_text = parts.next().ok_or(ParseLogError::MissingColumns)?;
    let level = Level::from_str(level_text).map_err(|err| ParseLogError::InvalidLevel(err.0))?;
    let service = parts
        .next()
        .ok_or(ParseLogError::MissingColumns)?
        .to_owned();
    let message = parts
        .next()
        .ok_or(ParseLogError::MissingColumns)?
        .to_owned();
    let mut fields = BTreeMap::new();
    let mut latency_ms = None;
    for part in parts {
        if let Some((key, value)) = part.split_once('=') {
            if key == "latency_ms" {
                latency_ms = Some(
                    value
                        .parse::<u64>()
                        .map_err(|_| ParseLogError::InvalidLatency(value.to_owned()))?,
                );
            }
            fields.insert(key.to_owned(), value.to_owned());
        }
    }
    Ok(LogRecord {
        timestamp,
        level,
        service,
        message,
        latency_ms,
        fields,
    })
}

pub fn parse_lines(text: &str) -> Result<Vec<LogRecord>, ParseLogError> {
    text.lines()
        .filter(|line| !line.trim().is_empty())
        .map(parse_line)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::{ParseLogError, parse_line};
    use crate::models::Level;

    #[test]
    fn parses_structured_line() {
        let record = parse_line(
            "2026-06-25T12:00:00Z ERROR api request_failed latency_ms=44 route=/v1/items",
        )
        .expect("valid line");
        assert_eq!(record.level, Level::Error);
        assert_eq!(record.service, "api");
        assert_eq!(record.latency_ms, Some(44));
        assert_eq!(record.fields["route"], "/v1/items");
    }

    #[test]
    fn rejects_unknown_level() {
        let err = parse_line("2026-06-25T12:00:00Z NOTICE api request_ok")
            .expect_err("invalid level should fail");
        assert_eq!(err, ParseLogError::InvalidLevel("NOTICE".to_owned()));
    }
}
