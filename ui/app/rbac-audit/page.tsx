"use client";

import { useState } from "react";
import Link from "next/link";

interface AccessTestScenario {
  userId: string;
  tenantId: string;
  targetTenantId: string;
  role: string;
  clearance: string;
  permission: string;
  nationality: string;
  expectedResult: "AUTHORIZED" | "DENIED";
  reason: string;
}

const SAMPLE_RBAC_SCENARIOS: AccessTestScenario[] = [
  {
    userId: "OPERATOR-OTT-41",
    tenantId: "DND-RCAF-TRENTON",
    targetTenantId: "DND-RCAF-TRENTON",
    role: "OPERATOR_ANALYST",
    clearance: "SECRET",
    permission: "COMPILE_PLAN",
    nationality: "CAN",
    expectedResult: "AUTHORIZED",
    reason: "Nominal same-tenant plan compilation with valid Secret clearance",
  },
  {
    userId: "ALLIED-LIAISON-09",
    tenantId: "DND-RCAF-TRENTON",
    targetTenantId: "DND-RCAF-TRENTON",
    role: "NATO_LIAISON_VIEWER",
    clearance: "SECRET",
    permission: "MUTATE_NETWORK",
    nationality: "USA",
    expectedResult: "DENIED",
    reason: "Role lacks permission 'MUTATE_NETWORK' (View-only liaison role)",
  },
  {
    userId: "AUDITOR-CCG-02",
    tenantId: "CANADIAN-COAST-GUARD",
    targetTenantId: "DND-RCAF-TRENTON",
    role: "SECURITY_AUDITOR",
    clearance: "SECRET",
    permission: "VERIFY_LEDGER",
    nationality: "CAN",
    expectedResult: "DENIED",
    reason: "Cross-tenant boundary violation: CCG auditor cannot inspect DND tenant without Sovereign Commander role",
  },
  {
    userId: "COMMANDER-JTF-01",
    tenantId: "CANADIAN-ARMED-FORCES-HQ",
    targetTenantId: "DND-RCAF-TRENTON",
    role: "SOVEREIGN_COMMANDER",
    clearance: "TOP_SECRET",
    permission: "TRIGGER_WARGAME",
    nationality: "CAN",
    expectedResult: "AUTHORIZED",
    reason: "Sovereign Commander has full cross-tenant emergency authority across all Canadian enclaves",
  },
];

export default function RBACAuditPage() {
  const [selectedRole, setSelectedRole] = useState<string>("OPERATOR_ANALYST");
  const [selectedClearance, setSelectedClearance] = useState<string>("SECRET");
  const [targetTenant, setTargetTenant] = useState<string>("DND-RCAF-TRENTON");
  const [homeTenant, setHomeTenant] = useState<string>("DND-RCAF-TRENTON");

  const isCrossTenant = homeTenant !== targetTenant && selectedRole !== "SOVEREIGN_COMMANDER";

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Multi-Tenant Sovereign Role-Based Access Control &amp; Tenancy</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Sovereign Clearance &amp; Multi-Tenant RBAC Inspector
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Enforces tenant isolation boundaries, Canadian classification levels (Protected B &rarr; Top Secret),
          and national dissemination caveats (CANADIAN_EYES_ONLY, NATO_SECRET).
        </p>
      </header>

      {/* Interactive Authorization Simulator */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", margin: "0 0 1rem 0" }}>🔐 Interactive Clearance &amp; RBAC Evaluator</h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Assigned Role:
            </label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            >
              <option value="SOVEREIGN_COMMANDER">Sovereign Commander (Cross-Enclave)</option>
              <option value="TENANT_ADMIN">Tenant Administrator</option>
              <option value="OPERATOR_ANALYST">Operator Analyst</option>
              <option value="SECURITY_AUDITOR">Security Auditor</option>
              <option value="SCIF_AIRGAP_OPERATOR">SCIF Air-Gap Operator</option>
              <option value="NATO_LIAISON_VIEWER">NATO Liaison Viewer</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Clearance Level:
            </label>
            <select
              value={selectedClearance}
              onChange={(e) => setSelectedClearance(e.target.value)}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            >
              <option value="TOP_SECRET">TOP SECRET (Level 3)</option>
              <option value="SECRET">SECRET (Level 2)</option>
              <option value="PROTECTED_B">PROTECTED B (Level 1)</option>
              <option value="UNCLASSIFIED">UNCLASSIFIED</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              User Home Tenant:
            </label>
            <select
              value={homeTenant}
              onChange={(e) => setHomeTenant(e.target.value)}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            >
              <option value="DND-RCAF-TRENTON">DND RCAF Trenton</option>
              <option value="CANADIAN-COAST-GUARD">Canadian Coast Guard</option>
              <option value="TRANSPORT-CANADA-HQ">Transport Canada HQ</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Target Resource Tenant:
            </label>
            <select
              value={targetTenant}
              onChange={(e) => setTargetTenant(e.target.value)}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            >
              <option value="DND-RCAF-TRENTON">DND RCAF Trenton</option>
              <option value="CANADIAN-COAST-GUARD">Canadian Coast Guard</option>
              <option value="TRANSPORT-CANADA-HQ">Transport Canada HQ</option>
            </select>
          </div>
        </div>

        {/* Evaluation Output Box */}
        <div
          style={{
            background: isCrossTenant ? "rgba(255, 0, 60, 0.08)" : "rgba(74, 222, 128, 0.08)",
            border: isCrossTenant ? "1px solid rgba(255, 0, 60, 0.3)" : "1px solid rgba(74, 222, 128, 0.3)",
            borderRadius: "8px",
            padding: "1.2rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
            <span style={{ fontFamily: "var(--mono)", fontSize: "0.8rem", color: "var(--muted)" }}>
              AUTHORIZATION VERDICT
            </span>
            <span
              style={{
                fontFamily: "var(--mono)",
                fontWeight: 800,
                fontSize: "0.85rem",
                color: isCrossTenant ? "#ff4d6d" : "var(--accent-2)",
              }}
            >
              {isCrossTenant ? "⛔ ACCESS DENIED (CROSS-TENANT VIOLATION)" : "✅ AUTHORIZED (POLICY COMPLIANT)"}
            </span>
          </div>
          <div style={{ fontSize: "0.88rem", color: "var(--text)" }}>
            {isCrossTenant
              ? `User in '${homeTenant}' cannot access data in '${targetTenant}' without Sovereign Commander credentials.`
              : `Identity validated with valid '${selectedRole}' role and '${selectedClearance}' clearance.`}
          </div>
        </div>
      </div>

      {/* Scenario Register Table */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", margin: "0 0 1rem 0" }}>📋 Canadian Government Enclave Test Register</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {SAMPLE_RBAC_SCENARIOS.map((s, idx) => (
            <div
              key={idx}
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "1rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                <strong style={{ fontSize: "0.95rem" }}>
                  {s.userId} ({s.role}) &rarr; {s.permission}
                </strong>
                <span
                  style={{
                    fontFamily: "var(--mono)",
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    color: s.expectedResult === "AUTHORIZED" ? "var(--accent-2)" : "#ff4d6d",
                  }}
                >
                  {s.expectedResult}
                </span>
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                Enclaves: <code>{s.tenantId}</code> &rarr; <code>{s.targetTenantId}</code> • Clearance: {s.clearance} ({s.nationality})
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--muted-2)", marginTop: "0.3rem" }}>
                Rationale: {s.reason}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/war-room" className="btn btn-primary">
          ← Back to War Room
        </Link>
        <Link href="/scif-attestation" className="btn btn-ghost">
          Inspect SCIF Hardware Attestation →
        </Link>
      </div>
    </div>
  );
}
