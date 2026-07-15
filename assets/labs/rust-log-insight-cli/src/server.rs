use crate::{
    analyzer,
    config::AppConfig,
    models::{LogRecord, Summary},
};
use anyhow::Result;
use axum::{Json, Router, extract::State, routing::get};
use serde::Serialize;
use std::{net::SocketAddr, sync::Arc};
use tokio::{net::TcpListener, signal};
use tracing::info;

#[derive(Clone)]
pub struct AppState {
    records: Arc<Vec<LogRecord>>,
    config: AppConfig,
}

impl AppState {
    pub fn new(records: Vec<LogRecord>, config: AppConfig) -> Self {
        Self {
            records: Arc::new(records),
            config,
        }
    }
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: &'static str,
}

pub fn build_router(records: Vec<LogRecord>, config: AppConfig) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/api/summary", get(summary))
        .route("/api/events", get(events))
        .with_state(AppState::new(records, config))
}

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse { status: "ok" })
}

async fn summary(State(state): State<AppState>) -> Json<Summary> {
    Json(analyzer::summarize(&state.records, &state.config))
}

async fn events(State(state): State<AppState>) -> Json<Vec<LogRecord>> {
    Json((*state.records).clone())
}

pub async fn serve(addr: SocketAddr, records: Vec<LogRecord>, config: AppConfig) -> Result<()> {
    let listener = TcpListener::bind(addr).await?;
    let local_addr = listener.local_addr()?;
    info!(%local_addr, "listening");
    axum::serve(listener, build_router(records, config))
        .with_graceful_shutdown(shutdown_signal())
        .await?;
    Ok(())
}

async fn shutdown_signal() {
    let _ = signal::ctrl_c().await;
    info!("shutdown requested");
}
