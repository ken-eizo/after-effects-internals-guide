---
status: pass-cross-version-static
date: 2026-10-12
evidence: E2-L
---
# EXP-SHAPE-047 — Decode all eleven Layer Style creator types

Trace all eleven calls to `TDB_ScRegisterStreams::Register` in native BEE2025/26 Layer Style startup to each RIP-relative factory callback. From the creator code, recover real native constructor and classify: **8 `TDB_Stream` value leaf constructors + 3 group constructors** (`AdvancedBlendingStreamGroup`, `BlendingOptionsStreamGroup`, `RootLayerStyleStreamGroup`). Independent verifier passes on both pinned versions.

Script: `verify_layerstyle_scoped_creator_types.py`. Data: `ae-layerstyle-eleven-creator-type-verification-2025-2026.json` and underlying source/constructor datasets. This is Adobe's internal startup schema, not plugin-defined independent native Contents; no private API executed. See F-VECTOR-047.
