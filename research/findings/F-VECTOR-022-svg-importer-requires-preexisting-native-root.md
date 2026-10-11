---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L + H
versions: installed AE2026 BEE.dll
---
# F-VECTOR-022 — SVG paste callback REQUIRES an existing native Root Vectors stream

## Falsification of a tempting shortcut

Previous F-VECTOR-018 noted BEE_PasteSVGIntoComp(BEE_Layer*, ...) accepts a generic BEE_Layer* formal parameter. This raised the hypothesis that it could create native Contents on arbitrary non-vector host layers. We have now traced the **caller before the actual conversion call** and established a stricter precondition.

BEE_CmdPasteSVGIntoLayer (AE2026 BEE RVA 0x57e210) schedules a command via BEE_DoCommand and native Undo context. One native callback begins at RVA **0x57e400** and performs:

1. RVA **0x57e444**: loads the EXACT exported BEE_VectorStream::StreamName_ROOT_VECTORS_GROUP static MatchName.
2. RVA **0x57e44f** constructs TDB_StreamID; RVA **0x57e45d** constructs TDB_StreamIDPath.
3. RVA **0x57e471** calls TDB_StreamGroup::FindStream on the provided native owner stream tree.
4. RVA **0x57e484** tests the returned stream pointer; RVA **0x57e487** branches to an exit/cleanup path at **0x57e752** when the root is absent.
5. Only on the successful existing-root branch, RVA **0x57e493** invokes the returned stream's vtable +0x88, checks its return value at **0x57e49c**, and invokes a second group method through vtable +0x168 at **0x57e4b4**.
6. Only after these checks, RVA **0x57e554** calls BEE_PasteSVGIntoComp. The converting function in F-VECTOR-018 also refers to ROOT_VECTORS_GROUP, AGM translation and layer mutation suppression.

A separate native callback at **0x57e790** explicitly finds ROOT_VECTORS_GROUP before constructing a synthetic child path with VECTOR_GROUP and calling BEE_CmdRemoveIndexedGroupEntry (RVA 0x57e8cf), with Undo and stream-removed-callback suppression. This further demonstrates pre-existing owner-side Contents semantics.

These are decoded executable branches and direct native CALL targets in the exact pinned local AE2026 BEE.dll. No external plugin invoked this private operation.

## Result and caveat

The observed SVG paste command path **does not bootstrap a missing ROOT_VECTORS_GROUP**. Generic BEE_Layer* parameter type is insufficient as evidence that arbitrary non-vector layer ownership is accepted.

The vtable +0x88 and +0x168 method identities have not been assigned here. The callback might also require hidden layer state, selection state, style/color settings and Undo invariants. Observations are static execution logic, not a validated custom owner runtime.

A custom layer which ALREADY owns a proper host-canonical Root Vectors stream *might* traverse this branch, but native Shape render, Timeline serialization, Pen tools and effect ownership remain independent unsolved gates.

## Product outlook

**Do not propose direct private SVG paste into arbitrary effect layers as a ready shortcut.** The productive route is to investigate how a host native Layer receives/owns Root Vectors and whether ownership is extensible or necessarily coupled to BEE_VectorLayer. For near-term creator workflows, the supported native SVG import into a **standard Shape Layer** remains an optional explicit bake operation, not an effect-owned live vector output.

## Evidence

- datasets/ae-svg-contents-owner-async-callback-and-find-2026.json
- datasets/ae-vector-root-contents-rip-ownership-xrefs-2026.json
- datasets/ae-native-svg-paste-stream-owner-commandchain-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_native_svg_command_callback.py
- experiments/vector-shape/probe-src/tools/audit_native_vector_root_matchname_xrefs.py
