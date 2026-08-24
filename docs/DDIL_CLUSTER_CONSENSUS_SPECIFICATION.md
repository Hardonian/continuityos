# DDIL SCIF Cluster State Consensus & Replication Specification

## 1. Context & Operational Environment

Tactical SCIF enclaves (Ottawa HQ, Halifax, Esquimalt, Resolute Bay FOL) operate under Disconnected, Degraded, Intermittent, and Low-Bandwidth (DDIL) tactical network conditions. Standard distributed consensus protocols (e.g. etcd, ZooKeeper) fail when network partitions persist for days or weeks.

---

## 2. Aegis Continuity Raft-Inspired DDIL Protocol

Aegis Continuity implements an air-gapped, partition-tolerant state synchronization engine:

1. **Monotonic Term & Log Indices**: Every command (evidence commit, incident log, threat directive) receives a monotonically increasing index.
2. **SHA-256 Merkle State Root**: Nodes summarize their complete state history into a 32-byte Merkle tree root hash.
3. **P2P Delta Sync**: When intermittent connectivity occurs (e.g., low-bandwidth SATCOM pass, acoustic handshake, sneakernet USB token):
   - Initiating node queries the peer's `last_log_index`.
   - Replicates only the delta log entries since that index.
   - Computes the new combined Merkle root and confirms cryptographic consensus.

---

## 3. CLI Command Reference

```bash
# Check local cluster status
continuity cluster-status --node-id SCIF-HQ-OTTAWA

# Synchronize state with peer node
continuity cluster-sync --node-id SCIF-HQ-OTTAWA --peer-id SCIF-HALIFAX --last-log-index 1240
```
