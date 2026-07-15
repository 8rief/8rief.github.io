use std::{path::PathBuf, process::Command};

fn fixture_path(name: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(name)
}

#[test]
fn summarize_command_writes_reports() {
    let temp = tempfile::tempdir().expect("tempdir");
    let bin = env!("CARGO_BIN_EXE_rust-log-insight-cli");
    let json = temp.path().join("summary.json");
    let csv = temp.path().join("events.csv");
    let output = Command::new(bin)
        .args([
            "--config",
            fixture_path("sample_config/log-insight.toml")
                .to_str()
                .unwrap(),
            "summarize",
            "--input",
            fixture_path("sample_logs/app.log").to_str().unwrap(),
            "--json",
            json.to_str().unwrap(),
            "--csv",
            csv.to_str().unwrap(),
        ])
        .output()
        .expect("run summarize command");
    assert!(
        output.status.success(),
        "stdout={} stderr={}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    let summary = std::fs::read_to_string(json).expect("summary json");
    assert!(summary.contains("\"total\": 6"));
    assert!(summary.contains("\"errors\": 2"));
    let events = std::fs::read_to_string(csv).expect("events csv");
    assert!(events.contains("ERROR,auth,login_failed"));
}
