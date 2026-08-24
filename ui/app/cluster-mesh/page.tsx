"use client";

import { useState } from "react";
import Link from "next/link";

interface SCIFNode {
  id: string;
  name: string;
  role: "LEADER" | "FOLLOWER" | "ISOLATED_SCIF";
  bandwidth: string;
  airGapped: boolean;
  term: number;
  lastLogIndex: number;
  merkleRoot: string;
  status: "SYNCED" | "DDIL_DEGRADED" | "STANDALONE";
}

const SAMPLE_SCIF_NODES: SCIFNode[] = [
  {
    id: "SCIF-HQ-OTTAWA",
    name: "DND Carling Campus National Command SCIF",
    role: "LEADER",
    bandwidth: "10 Gbps Air-Gap Fiber",
    airGapped: true,
    term: 14,
    lastLogIndex: 1248,
    merkleRoot: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    status: "SYNCED",
  },
  {
    id: "SCIF-NODE-HALIFAX",
    name: "CFB Halifax Maritime Operations SCIF",
    role: "FOLLOWER",
    bandwidth: "512 Kbps Tactical SATCOM (DDIL)",
    airGapped: true,
    term: 14,
    lastLogIndex: 1248,
    merkleRoot: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    status: "SYNCED",
  },
  {
    id: "SCIF-NODE-ESQUIMALT",
    name: "CFB Esquimalt Pacific Naval Base SCIF",
    role: "FOLLOWER",
    bandwidth: "256 Kbps High-Frequency HF Radio",
    airGapped: true,
    term: 14,
    lastLogIndex: 1245,
    merkleRoot: "3c9909afec25354d551dae21590bb26e38d53f2173b8d3dc3eee4c047e7ab1c1",
    status: "DDIL_DEGRADED",
  },
  {
    id: "SCIF-NODE-RESOLUTE",
    name: "Resolute Bay Arctic Forward Enclave (FOL)",
    role: "ISOLATED_SCIF",
    bandwidth: "0 Kbps (Scheduled Acoustic/Sneakernet Dump)",
    airGapped: true,
    term: 12,
    lastLogIndex: 1190,
    merkleRoot: "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
    status: "STANDALONE",
  },
];

export default function ClusterMeshPage() {
  const [nodes, setNodes] = useState<SCIFNode[]>(SAMPLE_SCIF_NODES);
  const [isReplicating, setIsReplicating] = useState<boolean>(false);

  const triggerDeltaSync = () => {
    setIsReplicating(true);
    setTimeout(() => {
      setNodes(
        nodes.map((n) => ({
          ...n,
          lastLogIndex: 1248,
          merkleRoot: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
          status: "SYNCED",
        }))
      );
      setIsReplicating(false);
    }, 1000);
  };

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Tactical Air-Gapped DDIL State Machine Replication</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Sovereign SCIF Cluster &amp; Raft State Synchronizer
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Distributed consensus and cryptographic log replication engine operating across air-gapped
          Sensitive Compartmented Information Facilities (SCIF) in Disconnected, Degraded, Intermittent,
          and Low-Bandwidth (DDIL) tactical networks.
        </p>
      </header>

      {/* Action Header Card */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <strong style={{ fontSize: "1.1rem" }}>🔒 Raft Consensus Cluster State (Term 14)</strong>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "0.2rem" }}>
            Merkle Root: <code style={{ color: "var(--accent)" }}>7f83b165...9069</code> (SHA-256 State Tree)
          </div>
        </div>
        <button
          onClick={triggerDeltaSync}
          disabled={isReplicating}
          className="btn btn-primary"
          style={{ padding: "0.6rem 1.2rem" }}
        >
          {isReplicating ? "Replicating Delta Logs..." : "⚡ Execute P2P Delta Sync"}
        </button>
      </div>

      {/* Grid of Nodes */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.2rem", marginBottom: "2rem" }}>
        {nodes.map((node) => (
          <div
            key={node.id}
            style={{
              background: "var(--panel)",
              border:
                node.status === "SYNCED"
                  ? "1px solid var(--border)"
                  : node.status === "DDIL_DEGRADED"
                  ? "1px solid rgba(251, 191, 36, 0.4)"
                  : "1px solid rgba(248, 113, 113, 0.4)",
              borderRadius: "10px",
              padding: "1.4rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
              <strong style={{ fontSize: "1.05rem" }}>{node.name}</strong>
              <span
                style={{
                  background:
                    node.status === "SYNCED"
                      ? "rgba(74, 222, 128, 0.15)"
                      : node.status === "DDIL_DEGRADED"
                      ? "rgba(251, 191, 36, 0.15)"
                      : "rgba(248, 113, 113, 0.15)",
                  color:
                    node.status === "SYNCED"
                      ? "var(--accent-2)"
                      : node.status === "DDIL_DEGRADED"
                      ? "var(--accent-3)"
                      : "var(--danger)",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  fontFamily: "var(--mono)",
                  padding: "0.15rem 0.45rem",
                  borderRadius: "4px",
                }}
              >
                {node.status}
              </span>
            </div>

            <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.8rem" }}>
              Node ID: <code>{node.id}</code> • Role: <strong>{node.role}</strong>
            </div>

            <div
              style={{
                background: "var(--panel-2)",
                padding: "0.8rem",
                borderRadius: "6px",
                fontSize: "0.78rem",
                fontFamily: "var(--mono)",
                display: "flex",
                flexDirection: "column",
                gap: "0.3rem",
              }}
            >
              <div>Bandwidth: <span style={{ color: "var(--text)" }}>{node.bandwidth}</span></div>
              <div>Log Index: <span style={{ color: "var(--accent)" }}>#{node.lastLogIndex}</span></div>
              <div>State Hash: <span style={{ color: "var(--muted)" }}>{node.merkleRoot.substring(0, 24)}...</span></div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/war-room" className="btn btn-primary">
          ← Back to War Room
        </Link>
        <Link href="/quantum-crypto" className="btn btn-ghost">
          Post-Quantum Cryptography &amp; ZKP →
        </Link>
      </div>
    </div>
  );
}
