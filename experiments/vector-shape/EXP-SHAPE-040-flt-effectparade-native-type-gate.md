---
status: pass-two-native-binary-static
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-040 — FLT Effect Parade native Canonical Stream/RTTI type gate

Goal: identify the actual native class admission condition for genuine Effect Parade children, not merely a string-prefix test.

The code of `FLT_Parade::CanStore` was disassembled in the installed AE2025 and AE2026 FLT.dll binaries. Independent tests assert that the imported `TDB_StreamBase::GetCanonicalStream` is called, the code takes MSVC source TypeDescriptor `TDB_StreamBase` and destination TypeDescriptor `FLT_FCSeqSpec`, calls the imported VCRUNTIME `__RTDynamicCast` via its thunk, then checks the returned pointer against null and returns a boolean. Both version-specific tests passed.

The BEE side separately confirms `BEE_EffectParade` constructors delegate into imported `FLT_Parade`. The native FLT effect class exposes both `FLTHost::ISequenceSpec` and `TDB_NamedStreamGroup` vtables plus Create, CloneStream, Read and Write. Cross-module evidence tests pass in BOTH versions.

Result: A new MatchName alone cannot pass Effect Parade admission unless the registered canonical stream is an appropriate native FLT sequence-spec class. This is a necessary gate only; creator ownership, safe unload, independent hierarchy, Pen editing and VectorArt rendering are not proved. No private Adobe API was executed.

Sources: `datasets/ae-flt-parade-canonical-rtti-2025-2026.json`, `datasets/ae-native-effect-owner-crossmodule-2025-2026.json`, and matching reproducible PE scripts under `experiments/vector-shape/probe-src/tools/`. See F-VECTOR-039.
