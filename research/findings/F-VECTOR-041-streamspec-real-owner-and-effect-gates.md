---
status: static-verified-two-binaries
last_verified: 2026-10-12
evidence: E2-L
versions: installed AE2025 and AE2026 BEE.dll
---

# F-VECTOR-041 — Native editable StreamSpec contains a real BEE Layer owner and hierarchical StreamIDPath

## Result

The exported `BEE_GetStreamWithSpec(BEE_StreamSpec const*,TDB_Stream**)` does not treat StreamSpec as an arbitrary vector path or detached data object. In both installed BEE versions its entry is a short x64 register-adjusting thunk. The exact instruction sequence is:

```asm
mov r8, rdx
lea rdx, [rcx + 0x10]
mov rcx, qword ptr [rcx + 8]
jmp <native stream lookup body>
```

The caller's `BEE_StreamSpec*` resides in RCX, and its output pointer in RDX. This adapter passes the output argument into R8, an inline `TDB_StreamIDPath` address at `StreamSpec+0x10` into RDX, and the actual `BEE_Layer*` at `StreamSpec+0x08` into RCX. It then jumps to a native stream-resolution routine.

**Pinned addresses:** AE2025 export RVA `0x36c9d0`, target `0x36b570`; AE2026 export RVA `0x3773c0`, target `0x375ef0`. These are version-bound offsets, not stable plugin interfaces. The native resolved body calls an internal routine and then uses a vtable `+0x80` access on the returned host object (consistent with the analyzed native TDB leaf accessor). The complete owner/stream validity contract is NOT established from that call alone.

The actual `BEE_StreamTypeHasStream` in both versions calls `BEE_IsEffectStreamPath` and conditionally branches, demonstrating that the generic edit/write substrate distinguishes at least some Effect path identity from other native stream paths. This does not show an Effect-owned vector path is admissible, editable or rendered.

## Product implication

A new CNL path node ID or `BEE_VectorArt::OriginInfo` identifier cannot by itself become an AE-native editable property. The host stream-resolution boundary requires a real `BEE_Layer` owner and authentic `TDB_StreamIDPath` identity that the owner can resolve. Forging a standalone StreamSpec with a guessed owner/layout cannot satisfy creation, serialization, native Pen callbacks, Undo, cache or renderer.

This strengthens F-VECTOR-017/038: first acquire an independently attached host-recognized Contents child under an actual owner; only then can the generic stream editing/Undo route be tested. The native BEE_VectorLayer renderer remains a separate host override, not a generic Effect output contract.

## Reproduction

Static tools `trace_native_streamspec_resolver.py` and `verify_native_streamspec_owner_identity.py`; evidence `datasets/ae-native-streamspec-resolver-effect-gate-2025-2026.json` and `datasets/ae-native-streamspec-owner-identity-verified-2025-2026.json`. Tests pass in both pinned BEE.dll versions. No native BEE functions were called in-process.

See F-VECTOR-039/040 for top-level Effect and nested child Canonical Stream admission, and F-VECTOR-042 for Canonical UILayout initialization details. This remains research; no `CompNodeAE` changes or Phase F integration.
