---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025 and AE2026 TDB.dll
---

# F-VECTOR-027 — Native Stream cloning, serialization and persistent parent identity

## Goal, scope and independent success definition

The intended plugin will own editable AE-native vector values and indexed Contents without constructing existing Masks or Shape Layers. This finding uses exact installed native code to reconstruct clone, save, load and ownership behavior; it does NOT prove external host registration or native BEE VectorArt output.

## Verified real native Stream methods

Read-only x64 exported-method and .pdata-bounded disassembly gives:

| Native method | AE2025 RVA | AE2026 RVA | Behavior supported by resolved calls |
| --- | --- | --- | --- |
| TDB_StreamBase::Clone | 0x42b0 | 0x45f0 | virtual clone dispatch through vtable +0x8 |
| TDB_Stream::CloneStream | 0x36020 | 0x36a80 | tracked allocation and clone constructor with TDB_CloneStreamParams |
| TDB_ParamPathStream::CloneStream | 0x10360 | 0x10400 | dedicated derived path-like stream clone constructor |
| TDB_StreamGroup::Read | 0x3d4c0 | 0x3e040 | base Read, ReadUniqueStreamID, MatchName Read and EndOfGroupMarker |
| TDB_StreamGroup::Write | 0x43ef0 | 0x44a50 | begin SLU chunk, base Write, unique Stream ID, canonical lookup, MatchName and EndOfGroupMarker |
| TDB_Stream::Read | 0x12470 | 0x123d0 | base Read, underlying SLU atoms, native stream cache/keys, ReadUniqueStreamID |
| TDB_Stream::Write | 0x13e40 | 0x14260 | native KeyData, HasKeys, GetExpression, SLU atoms and WriteUniqueStreamID |
| TDB_StreamBase::SetParent | 0x3f0e0 | 0x3fb20 | parent notifications, stream rescale and several parent/leaf virtual branches |
| TDB_StreamGroup::SetupCanonicalLayout | 0x3fac0 | 0x40520 | native canonical layout and SetUILayout, with separated-dimensions behavior |

The native project data model is not merely a Bezier array: the host owns unique source stream identity, serialized metadata, typed group layout, canonical schema, time-value state and parent notifications. The group writer consults the canonical stream and records a native unique ID; the reader reconstructs type identities. An independent plugin-owned type cannot be cloned by copying opaque host memory or made persistent by inventing a private .aep byte layout.

Direct Read/Write callgraphs do not prove the complete opaque SLU wire format; attempts to guess that format are explicitly outside the current experiment. Each native class would have to implement legitimate virtual Clone/Read/Write and cooperate with the host's project owner and serializer.

## Separate edit/evaluation/render blockers

Native clone and serializer routines do not themselves create Pen/Selection targets, new native owner Layer types or BEE_VectorArt output. Native authoring and renderer dispatch remain separate gates (F-VECTOR-025/026). A separate TDB_ParamPathStream clone method existing inside TDB.dll is not proof that an effect may instantiate a path with true independent AE editor semantics.

## Reproducibility

- datasets/ae-tdb-native-clone-serialization-parent-callgraph-2025-2026.json
- datasets/ae-native-vector-owner-serialization-gates-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_tdb_clone_serialization_owner.py
- experiments/vector-shape/probe-src/tools/verify_native_vector_clone_io_bee_abi.py
- EXP-SHAPE-025-native-stream-io-and-bee-registry.md

E2-L only. No Adobe private native code invoked. No original DLL or project file redistributed.

## Large plugin vision

If an independent owner and legal private registry ABI can be established, CompNodeAE can retain persistent native Contents with vector values, editable path anchors, expressions/animation and undo identity; native BEE evaluators could eventually transform the data directly into VectorArt rather than PF_World. This capability is NOT yet implemented inside AE.
