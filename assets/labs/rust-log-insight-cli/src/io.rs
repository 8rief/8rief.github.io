use crate::{
    models::{LogRecord, Summary},
    parser,
};
use anyhow::{Context, Result};
use std::{fs, path::Path};

pub fn read_log_file(path: impl AsRef<Path>) -> Result<Vec<LogRecord>> {
    let path = path.as_ref();
    let text =
        fs::read_to_string(path).with_context(|| format!("read log file {}", path.display()))?;
    parser::parse_lines(&text).with_context(|| format!("parse log file {}", path.display()))
}

pub fn write_summary_json(path: impl AsRef<Path>, summary: &Summary) -> Result<()> {
    let path = path.as_ref();
    ensure_parent(path)?;
    let text = serde_json::to_string_pretty(summary).context("encode summary JSON")?;
    fs::write(path, format!("{text}\n"))
        .with_context(|| format!("write JSON report {}", path.display()))
}

pub fn write_events_csv(path: impl AsRef<Path>, records: &[LogRecord]) -> Result<()> {
    let path = path.as_ref();
    ensure_parent(path)?;
    let mut writer = csv::Writer::from_path(path)
        .with_context(|| format!("create CSV report {}", path.display()))?;
    writer.write_record(["timestamp", "level", "service", "message", "latency_ms"])?;
    for record in records {
        writer.write_record([
            record.timestamp.as_str(),
            record.level.as_str(),
            record.service.as_str(),
            record.message.as_str(),
            &record
                .latency_ms
                .map(|value| value.to_string())
                .unwrap_or_default(),
        ])?;
    }
    writer.flush().context("flush CSV report")
}

fn ensure_parent(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .with_context(|| format!("create output directory {}", parent.display()))?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{write_events_csv, write_summary_json};
    use crate::{analyzer::summarize, config::AppConfig, parser::parse_lines};

    #[test]
    fn writes_json_and_csv_reports() {
        let temp = tempfile::tempdir().expect("tempdir");
        let records =
            parse_lines("2026-06-25T12:00:00Z INFO api ok latency_ms=10\n").expect("valid fixture");
        let summary = summarize(&records, &AppConfig::default());
        let json_path = temp.path().join("nested/summary.json");
        let csv_path = temp.path().join("events.csv");
        write_summary_json(&json_path, &summary).expect("json report");
        write_events_csv(&csv_path, &records).expect("csv report");
        let json = std::fs::read_to_string(json_path).expect("read json");
        assert!(json.contains("\"total\": 1"));
        let csv = std::fs::read_to_string(csv_path).expect("read csv");
        assert!(csv.contains("timestamp,level,service,message,latency_ms"));
    }
}
