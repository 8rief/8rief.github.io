use crate::{
    config::AppConfig,
    models::{Level, LevelCount, LogRecord, ServiceCount, Summary},
};
use std::collections::BTreeMap;

pub fn summarize(records: &[LogRecord], config: &AppConfig) -> Summary {
    let mut level_counts: BTreeMap<Level, usize> = BTreeMap::new();
    let mut service_counts: BTreeMap<String, (usize, usize)> = BTreeMap::new();
    let mut errors = 0;
    let mut warnings = 0;
    let mut slow_events = 0;

    for record in records {
        *level_counts.entry(record.level).or_default() += 1;
        let entry = service_counts.entry(record.service.clone()).or_default();
        entry.0 += 1;
        match record.level {
            Level::Error => {
                errors += 1;
                entry.1 += 1;
            }
            Level::Warn => warnings += 1,
            Level::Debug | Level::Info => {}
        }
        if record
            .latency_ms
            .is_some_and(|latency| latency >= config.slow_latency_ms)
        {
            slow_events += 1;
        }
    }

    let total = records.len();
    Summary {
        total,
        errors,
        warnings,
        slow_events,
        error_rate: if total == 0 {
            0.0
        } else {
            errors as f64 / total as f64
        },
        level_counts: level_counts
            .into_iter()
            .map(|(level, count)| LevelCount { level, count })
            .collect(),
        service_counts: service_counts
            .into_iter()
            .map(|(service, (count, errors))| ServiceCount {
                service,
                count,
                errors,
            })
            .collect(),
    }
}

#[cfg(test)]
mod tests {
    use super::summarize;
    use crate::{config::AppConfig, parser::parse_lines};

    #[test]
    fn summarizes_levels_services_and_slow_events() {
        let records = parse_lines(
            "2026-06-25T12:00:00Z INFO api ok latency_ms=10\n\
             2026-06-25T12:00:01Z ERROR api fail latency_ms=60\n\
             2026-06-25T12:00:02Z WARN worker retry latency_ms=70\n",
        )
        .expect("valid fixture");
        let summary = summarize(
            &records,
            &AppConfig {
                error_rate_warning: 0.25,
                slow_latency_ms: 50,
            },
        );
        assert_eq!(summary.total, 3);
        assert_eq!(summary.errors, 1);
        assert_eq!(summary.warnings, 1);
        assert_eq!(summary.slow_events, 2);
        assert!((summary.error_rate - (1.0 / 3.0)).abs() < f64::EPSILON);
    }
}
