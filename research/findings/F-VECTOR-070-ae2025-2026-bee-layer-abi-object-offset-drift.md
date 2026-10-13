---
date: 2026-10-14
status: PASS genuine native Adobe BEE C++ ABI drift in pinned AE2025 versus AE2026
evidence: E2-L native installed BEE.dll machine instruction operands and SHA256
---
# F-VECTOR-070 — Native BEE_Layer member layout and virtual slot offsets changed across versions

The same native BEE_Layer::CloneAndAttach method in the two installed AE versions has materially different C++ object layout and virtual dispatch indices:

| Native object usage | AE2025 | AE2026 |
| --- | --- | --- |
| BEE_Layer::CloneAndAttach RVA | 0x2E20E0 | 0x2EB090 |
| this->CompItem pointer read | [rbp+0x2B8] | [rbp+0x260] |
| flag-check virtual dispatch of clone | [rdx+0x2A8] | [rdx+0x2B8] |
| native CompItem attachment call | 0x2E218F | 0x2EB140 |

In these functions RBP is confirmed to retain the original BEE_Layer this pointer. The CompItem member offset changed by 0x58 bytes between versions, while the related virtual function table slot moved by 0x10 bytes.

This is NOT ordinary address relocation: the actual private object layout and vtable offsets changed across versioned native code. Consequently a custom C++ subclass layout, vtable and pointer arithmetic from AE2025 cannot be assumed valid on AE2026. Exact installed DLL fingerprint checks, complete ABI version-specific guards, object allocation/teardown guarantees and fail-closed behavior would be needed even to investigate a private host-native bridge safely.

It is NOT shown that Adobe supports externally registered custom Layer subclasses. The generic clone code still requires imported TDB_StreamBase::Clone and RTTI conversion to BEE_Layer (F-VECTOR-068).

Reproducible evidence:
- experiments/vector-shape/probe-src/tools/verify_bee_layer_cross_version_abi_drift.py
- datasets/ae-bee-layer-clone-attach-cross-version-abi-drift-2025-2026.json

No private host execution or binary modification.
