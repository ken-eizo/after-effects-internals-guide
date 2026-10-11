---
status: hypothesis
last_verified: 2026-10-11
evidence: H + E0-G + E2-L leads
versions: SDK 25.6; AE 2025 runtime
---
# H-SHAPE-002 — External geometry-to-native-rasterizer bridge

**Question:** Can a custom plug-in provide path/graphic geometry to AE's *production* vector evaluator/rasterizer without emitting only an effect pixel world and without constructing a standard Shape Layer?

**H1:** A reusable geometry-provider interface exists at the BEE_VectorArt/AGM/RG boundary and can be integrated with a new host-recognized object type.

**H2:** VectorArt/AGM translation is implemented privately for host-owned vector layers; third-party effects lack a compatible geometry output contract.

**H3:** AGM primitives can rasterize vector geometry within a plug-in, but the resulting effect is still pixel-output only; this does **not** meet full native Shape parity.

Falsification: H1 requires a safe documented or independently verified attach/create/identity/invalidations route, plus AE-native vector edit/render behavior. H2 is falsified by such a route. H3 is falsified if a plug-in demonstrably hands an actual vector object into AE's native evaluation stack rather than returning pixels.

Distinguish UI Drawbot from production vector rendering; distinguish Artisan 3D render replacement from Shape Layer evaluation. Baseline EXP-SHAPE-003/005, then gated EXP-SHAPE-006. E2-L evidence: `F-VECTOR-002`; public contract: Adobe Drawbot and Artisan docs.
