---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: AE2025/2026 TDB.dll
---
# EXP-SHAPE-013 — Eager creator callback invocation and canonical lifecycle

The objective was to determine whether the native `TDB_StreamFactory::RegisterFactoryFunc` only stores the callback or invokes it while registering a stream type. Using exact installed AE2025/2026 TDB.dll exports, x64 .pdata-bounded disassembly and direct callsite resolution, the host code **calls CreateStream during RegisterFactoryFunc**, and may call `RegisterSeparatedDimensions` and `RegisterCanonicalInstance` before returning. Both versions also have duplicate registration detection and explicit unregister functions.

**Observation E2-L:** Factory creator callbacks are not safely replaceable with incomplete stubs. The callback must be callable during registration and its returned object must satisfy native virtual and lifetime invariants immediately.

No BEE/TDB native code was executed by this static experiment, no proprietary binaries distributed, and no AE project modified. The external v3 plugin's earlier host experiment only called a read-only getter (different E2-X claim).

Data: `datasets/ae-tdb-factory-lifetime-canonical-controlflow-2025-2026.json`. Reproduction: `experiments/vector-shape/probe-src/tools/audit_tdb_factory_lifetime.py`. Next: fully reconstruct creator ABI/canonical ownership before any reversible registration test in a disposable host.
