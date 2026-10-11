---
status: hypothesis
last_verified: 2026-10-11
evidence: H + E2-L leads
versions: AE 2025 binary leads; SDK 25.6
---
# H-SHAPE-001 — Native dynamic stream type registration boundary

**Question:** Can a plug-in independently register and instantiate a host-owned native indexed Contents-like property group, instead of adding streams to an already-existing group?

**H1 (extensible factory):** AE maintains an internal registration facility that can accept third-party stream type constructors and owner associations. A safe independently created plug-in group would be recognized by the Timeline with native add/remove/reorder semantics. **Falsification:** proof that the registration table only accepts a closed set of host-owned types or fails to register a new plugin type under supported conditions.

**H2 (closed factory):** `TDB_StreamFactory` and relevant `BEE_VectorStream` subclasses exist but their registration lifecycle is host-private. **Falsification:** a repeatable host-side or public supported extension registration pathway creating a new stream type without an existing native Shape Layer.

**H3 (owner gate):** The Timeline requires a specific vector layer/object owner even if stream factories are generic. **Falsification:** a new owner type with a native indexed Contents registered and working without native Shape Layer ownership.

Evidence: `datasets/ae-2025-vector-shape-symbols.csv` constructor-like exports (E2-L); Adobe AEGP DynamicStreamSuite controls existing indexed groups (E0-G/H). These facts do **not** validate H1, H2 or H3.

Test plan: EXP-SHAPE-001 (baseline read-only traversal), EXP-SHAPE-003 (factory call-site static analysis), EXP-SHAPE-006 (later guarded registration experiment). Require original host output and regression on save/undo/restart before promotion.
