---
status: pass-static-both-host-binaries
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-035 — VectorLayer RegisterStreams trampoline and native evaluator initialization

## Goal

Recover precise initialization control flow of the native `BEE_VectorLayer::RegisterStreams` entry instead of interpreting the function entry as all adjacent bytes. Establish the native stream-vs-evaluator startup boundary before considering foreign vector type/provider registration.

## Method

Use exact installed AE2025 and AE2026 `BEE.dll`; inspect PE exports, SHA256, first five bytes of the `RegisterStreams` export and disassemble the resolved target with Capstone. Assert that the exported instruction is a JMP to the wrapper, that the wrapper sets `CL=1`, calls two distinct routines in order, and tail-jumps to another routine. This is fully offline; no AE process or private C++ API is invoked.

## Reproducible results

| Symbolic stage | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| RegisterStreams exported thunk | 0x6e4100 | 0x708a30 |
| thunk target | 0x76b6f0 | 0x78cf60 |
| first init call | 0x77c630 | 0x79d040 |
| BEE evaluator registry init call | 0x6eef40 | 0x713550 |
| tail jump | 0x6fdcc0 | 0x7217c0 |

The second native call matches the separately determined evaluator registration singleton entry. Exact call argument/ownership contracts of the other two targets have NOT been determined. In particular, this proves no third-party extension insertion point and no independent renderer ownership.

## Artifacts

- `experiments/vector-shape/probe-src/tools/verify_bee_native_vector_startup_chain.py`
- `datasets/ae-bee-vector-registerstreams-startup-chain-2025-2026.json`
- `research/findings/F-VECTOR-036-bee-vector-layer-registerstreams-init-trampoline.md`

## Next falsifiable step

Follow the first and tail routines' real callers, owner identity and initialization order without executing host mutators. Determine whether a separate factory/evaluator registration can coexist with independent Timeline and RenderGraph ownership. Stop if required contracts remain opaque; do not substitute ordinary masks or built-in Shape Layer effects.
