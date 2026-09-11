//! Official Rust Client SDK for ContinuityOS.

use serde::{Deserialize, Serialize};

/// Operational corridor state enum conforming to ContinuityOS 12-state taxonomy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum CorridorState {
    Healthy,
    Degraded,
    OpenButUninsurable,
    OpenButNoCarrierCapacity,
    OpenButNavigationUntrusted,
    OpenButCommunicationsDegraded,
    RecoveryBacklogged,
    PhysicallyClosed,
    Closed,
    Unknown,
}

/// Operational status representation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CorridorStatus {
    pub corridor_id: String,
    pub effective_state: CorridorState,
    pub resilience_score: f64,
    pub closure_reason: Option<String>,
}

/// Lightweight tactical client.
pub struct ContinuityClient {
    pub base_url: String,
    pub api_key: Option<String>,
}

impl ContinuityClient {
    pub fn new(base_url: Option<String>, api_key: Option<String>) -> Self {
        Self {
            base_url: base_url.unwrap_or_else(|| "http://127.0.0.1:8082".to_string()),
            api_key,
        }
    }
}
