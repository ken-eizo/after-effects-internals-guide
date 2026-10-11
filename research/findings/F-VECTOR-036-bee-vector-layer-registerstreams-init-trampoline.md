---
status: static-verified-two-pinned-host-binaries
last_verified: 2026-10-12
evidence: E2-L + H
versions: installed AE2025 / AE2026 BEE.dll
---

# F-VECTOR-036 — Native VectorLayer stream-registration entry dispatches through a separate evaluator initializer

## Question

Does the exported `BEE_VectorLayer::RegisterStreams` directly perform its complete stream registration, or does it call separate native subsystem initialization stages? This matters because a third-party TDB type creator, native Contents owner and BEE evaluator must be distinguished.

## New exact static witness

The exported vector layer RegisterStreams entry is a **five-byte near JMP**, not the body of a stream registration routine, in BOTH pinned BEE versions. Following the branch reaches a short native wrapper:

| Stage | AE2025 BEE RVA | AE2026 BEE RVA |
| --- | --- | --- |
| exported RegisterStreams | `0x6e4100` | `0x708a30` |
| wrapper target | `0x76b6f0` | `0x78cf60` |
| first direct CALL | `0x77c630` | `0x79d040` |
| second direct CALL | `0x6eef40` | `0x713550` |
| final JMP | `0x6fdcc0` | `0x7217c0` |

At each wrapper, the x64 instructions are: allocate 0x28 bytes of stack, set `CL=1`, call the first routine, call the second routine, release the stack space, and tail-jump to the last routine. The **second call** agrees with the BEE vector operator-registry initialization RVAs independently recorded in the prior native evaluator findings. The first routine and final tail are separate stages whose exact high-level contracts are not established by this trace alone.

This is stronger than scanning arbitrary bytes following the exported JMP and incorrectly attributing neighboring unrelated functions to RegisterStreams. The new verifier asserts both relative branch destinations, call order and `CL=1` against the actual PE machine code, with SHA256 receipts and no host execution.

## Impact on product feasibility

Native vector type creation is a multi-stage host-owned initialization, not a generic vector-return channel exposed by ordinary Effects. A hypothetical external MatchName accepted into TDB still cannot imply BEE evaluator installation, independent Contents ownership, AE Pen edit targets or `BEE_VectorLayer::Rasterize2DGraph` integration. This finding identifies the **exact initialization chain** to investigate next: identify the first native setup routine, ownership/lifetime policy of the BEE evaluator initialization and final tail stage, then test whether a separate extension insertion point exists. Importing the wrapper itself as a plugin's new-type registration is NOT a supported or demonstrated solution.

## Reproduction and limitations

Run `experiments/vector-shape/probe-src/tools/verify_bee_native_vector_startup_chain.py` on the exact locally installed BEE.dll binaries. Receipt: `datasets/ae-bee-vector-registerstreams-startup-chain-2025-2026.json`.

E2-L proves control-flow only; it does **not** establish the C++ prototypes for unexported destinations, state lifetime, foreign registration permission, safe calling convention, or any AEX runtime. No modified AE binary, installed AEX, Mask or Shape Layer is used in this analysis. The Phase F integration boundary remains untouched.
