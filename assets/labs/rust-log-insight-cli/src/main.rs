use anyhow::Result;
use clap::{Parser, Subcommand};
use rust_log_insight_cli::{analyzer, config::AppConfig, io, server};
use std::{net::SocketAddr, path::PathBuf};
use tracing::info;

#[derive(Debug, Parser)]
#[command(
    name = "rust-log-insight",
    version,
    about = "Summarize local structured logs"
)]
struct Cli {
    #[arg(long, default_value = "sample_config/log-insight.toml", global = true)]
    config: PathBuf,
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Parse a log file and write summary JSON plus event CSV.
    Summarize {
        #[arg(long, default_value = "sample_logs/app.log")]
        input: PathBuf,
        #[arg(long, default_value = "reports/summary.json")]
        json: PathBuf,
        #[arg(long, default_value = "reports/events.csv")]
        csv: PathBuf,
    },
    /// Serve the same summary through a local HTTP API.
    Serve {
        #[arg(long, default_value = "sample_logs/app.log")]
        input: PathBuf,
        #[arg(long, default_value = "127.0.0.1:18220")]
        addr: SocketAddr,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env().add_directive("info".parse()?),
        )
        .init();
    run(Cli::parse()).await
}

async fn run(cli: Cli) -> Result<()> {
    let config = AppConfig::load(&cli.config)?;
    match cli.command {
        Command::Summarize { input, json, csv } => {
            let records = io::read_log_file(&input)?;
            let summary = analyzer::summarize(&records, &config);
            io::write_summary_json(&json, &summary)?;
            io::write_events_csv(&csv, &records)?;
            info!(
                total = summary.total,
                errors = summary.errors,
                warnings = summary.warnings,
                slow_events = summary.slow_events,
                json = %json.display(),
                csv = %csv.display(),
                "summary written"
            );
            Ok(())
        }
        Command::Serve { input, addr } => {
            let records = io::read_log_file(&input)?;
            info!(%addr, count = records.len(), "starting local API");
            server::serve(addr, records, config).await
        }
    }
}
