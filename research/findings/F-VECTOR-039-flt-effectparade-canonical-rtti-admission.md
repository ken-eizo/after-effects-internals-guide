---
status: static-verified-two-native-binaries; external-registration-unproven
last_verified: 2026-10-12
evidence: E2-L + H
versions: pinned AE2025/2026 FLT.dll, BEE.dll, TDB.dll
---

# F-VECTOR-039 — Effect Parade child admission is a Canonical Stream C++ RTTI test

## Problem and major finding

An external native vector **effect-owned Contents** is different from an extension to existing Shape Contents. Why do candidate `ADBE Vector Shape - ...` names pass native Shape parent admissibility yet fail ordinary Effect Parade? Native ELF-like type names alone are not enough.

The **real** exported `FLT_Parade::CanStore(TDB_MatchName const&)` was recovered and checked at instruction level, using both installed Windows x64 FLT.dll files. In AE2025 its RVA is `0x53580`, in AE2026 `0x55300`. In both builds it directly:

1. Calls the imported `TDB.dll!TDB_StreamBase::GetCanonicalStream(TDB_MatchName const&)` using the proposed MatchName.
2. Sets up MSVC `__RTDynamicCast` (`VCRUNTIME140.dll`) on that returned pointer, with the source TypeDescriptor `.?AVTDB_StreamBase@@` and destination TypeDescriptor `.?AVFLT_FCSeqSpec@@`.
3. Invokes the RTTI cast with `isReference=0`, checks `RAX` against null, returns `setne AL`.

**Therefore Effect Parade admission is conditional on the candidate's registered canonical native class being runtime-castable to FLT_FCSeqSpec**, not on a string starting with `ADBE Vector`. The exact code path was checked cross-version; no native method was called.

This creates a concrete negative result for the original experimental plan: registering the prebuilt `TDB_ParamPathStream::Create` under an invented MatchName is not sufficient to join the Effect Parade unless the resulting object also actually satisfies the `FLT_FCSeqSpec` type requirement. A boolean success from TDB factory registration alone cannot pass this gate.

## Where the Effect Parade is really owned

`BEE_EffectParade` is not merely an opaque VectorLayer/TDB sibling. Disassembly of its three constructors and CloneStream in both BEE binaries resolves imported `FLT.dll!FLT_Parade` constructors. `BEE_EffectParade::Create` allocates its own object and calls the native BEE constructor; cloning calls FLT's base constructor.

`FLT_FCSeqSpec` has two native exported vtable symbols, one for `FLTHost::ISequenceSpec` and another for `TDB_NamedStreamGroup`, plus native `Create`, `CloneStream`, `Read`, `Write` exports. It therefore spans the native **effect execution/sequence contract** and the **TDB authored property-group contract**. It is not a simple generic path object.

## Product consequences

For an ordinary Effect to genuinely own AE-native path/Contents without creating masks or Shape Layers, four distinct bridges must be established:

- A registered, properly owned canonical TDB stream whose class and lifetime match the FLT-style native effect child contract, not only the MatchName string.
- A host-recognized independent parent/child IDPath and TDB-owned persistent serialization under the effect.
- Native selection/Pen read-write target with the generic `BEE_CmdSetStreamFPVPlus`/Undo chain (F-VECTOR-038).
- Separate vector geometry evaluation and `BEE_VectorArt`/AGM/RG rendering output rather than PF_World.

An arbitrary `FLT_FCSeqSpec` subclass supplied by a third party has **NOT** been shown safe or registered. Layout, callbacks, FLT lifecycle, plugin unload, host-owned effect execution, Timeline, Pen and renderer remain unknown. Never call these private creators based on this static finding.

## Evidence

- `datasets/ae-flt-parade-canonical-rtti-2025-2026.json` (dynamic-cast, imported canonical getter and both RTTI descriptors)
- `datasets/ae-flt-effectparade-canstore-disassembly-2025-2026.json`
- `datasets/ae-effectparade-native-owner-factory-2025-2026.json`
- `datasets/ae-native-effect-owner-crossmodule-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-040-flt-effectparade-native-type-gate.md`

Repro scripts under `experiments/vector-shape/probe-src/tools/`: audit_flt_effectparade_canstore.py, verify_flt_parade_canonical_rtti_gate.py, audit_effectparade_native_owner.py, verify_native_effect_owner_boundary.py. All are static; none loads or calls a private Adobe DLL from an AEX.

## Critical scope correction — top-level Effect Parade vs parameters *within* one effect

The proven `FLT_Parade::CanStore` is the **top-level parent-admission gate for effect sequence objects**. It does NOT establish the admission rules for adding a new child Path, Group, or parameter *inside an already existing* `FLT_FCSeqSpec` effect. Those nested streams may be governed by a distinct `TDB_NamedStreamGroup` parent, canonical layout, and FLT effect parameter-definition machinery. Consequently:

- New arbitrary **top-level effect class** inserted into Effect Parade requires a canonical instance compatible with `FLT_FCSeqSpec` for this specific gate.
- An existing plugin Effect that seeks additional **native nested Contents** is a DIFFERENT question; the required type can only be determined after tracing `FLT_FCSeqSpec` child `CanStore` and canonical-layout construction. Do not assume every vector Path would need to subclass `FLT_FCSeqSpec`.
- Even meeting either parent admissibility gate never proves After Effects' Pen tool or BEE VectorArt renderer will use the path.

EXP-SHAPE-039 compares both parent types read-only in an actual AE process (once user runs it), but has not produced live observations yet. Falsification is clear: find the nested FCSeqSpec admission method and whether it permits a separate TDB vector-group type independent of the enclosing effect sequence.
