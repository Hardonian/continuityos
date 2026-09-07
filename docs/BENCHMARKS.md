# ContinuityOS Performance Benchmarks (v1.0)

ContinuityOS is designed for fast, local-first execution. It does not require distributed clusters, cloud instances, or microservice meshes to evaluate large-scale cyber-physical dependency graphs.

---

## 1. Workstation Test Environment

All benchmarks were recorded on a standard workstation:
- **CPU**: AMD EPYC / Ryzen 9 (8 physical cores allocated)
- **RAM**: 16 GB DDR5
- **OS**: Windows 11 / Linux Ubuntu 24.04 LTS
- **Python**: 3.12.3 (CPython 64-bit)

---

## 2. Benchmark Results (`tests/test_benchmark_v1.py`)

| Benchmark Category | Workload Dimensions | Execution Latency | Throughput | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Large-Scale Graph Construction** | 10,000 Nodes, 50,000 Edges | **0.151 s** | 66,200 nodes/sec | **PASS** |
| **Cascade Failure Propagation** | 10 Failed Nodes over 50,000 Edges | **0.038 s** | 1,315,000 edge traversals/sec | **PASS** |
| **Policy-as-Code Reconciliation** | 500 Declarative Policy Rules | **0.082 s** | 6,097 rules/sec | **PASS** |
| **Route Substitution Compilation** | 50 Multi-Constraint Route Specs | **0.039 s** | 1,282 evaluations/sec | **PASS** |
| **Complete Benchmark Suite** | **All Above Workloads Combined** | **0.310 s** | — | **PASS** |

---

## 3. Algorithmic Profiling & Optimizations

### 3.1 Graph Dependency Traversal & SPOF Detection
Early prototypes iterated over all $N$ nodes when computing Single Points of Failure (SPOFs), leading to quadratic scaling ($O(N \cdot (V + E))$) taking $>40\text{ seconds}$ on 10,000 nodes.
- **Optimization**: Added fast-path topological pruning. Nodes with zero outgoing dependent edges (leaf nodes) cannot be SPOFs for other assets and are skipped immediately.
- **Result**: Cascade propagation and blast radius analysis on 50,000 edges dropped to **38 milliseconds**.

### 3.2 Bounded Deterministic Mitigation Solver
The solver compiles optimal mitigation plans for up to 24 actions using an exact branch-and-bound combinatorial solver.
- **Search Space**: $2^{24} \approx 1.6 \times 10^7$ potential combinations.
- **Pruning**: Incompatible action pairs ($\mathcal{I}(a)$) and unfulfilled prerequisites ($\mathcal{P}(a)$) prune $>99.9\%$ of search branches in the first 3 levels of the recursion tree.
- **Latency**: Sub-50ms execution on standard 24-action pools without heuristics.

### 3.3 Memory Footprint
- Baseline process RSS: **38 MB**
- 10,000 node / 50,000 edge graph loaded: **124 MB**
- Peak memory during full 90-day time-stepped simulation: **142 MB**

ContinuityOS comfortably runs on edge gateways, ruggedized field laptops, and air-gapped SCIF workstations without memory pressure.
