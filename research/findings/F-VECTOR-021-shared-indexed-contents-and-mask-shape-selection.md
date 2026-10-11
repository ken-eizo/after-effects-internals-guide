---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L + H
versions: installed AE2025 and AE2026 BEE.dll, TDB.dll
---
# F-VECTOR-021 — Generic indexed Contents insertion and mask/shape path selection share native primitives

## Discovery: generic indexed child command is real and broadly used

The native function BEE_CmdAddToIndexedStreamGroup(BEE_Layer*, TDB_StreamIDPath const&, TDB_MatchName const*, ...) is exported and calls BEE_Layer::GetUndoContext, TDB_StreamGroup::FindStream, TDB_StreamBase::CreateStream, TDB_StreamBase::SetDisplayName and BEE_StartGroupWithNameFromStreamOperation / BEE_EndGroup. The same behavior is verified by code in two installed versions:

- AE2025 BEE RVA 0x657820, AE2026 BEE RVA 0x672a20.
- Both versions: **13 direct BEE callers**, including BEE_AVLayer::CreateSet, BEE_LayerSet::AddProperty, Light environment stream initialization, MaterialOverride stream synchronization, and EffectMaskHelper commands.
- Separate BEE_CmdAddVectorProperty(BEE_VectorLayer*, ...) calls a native selection-modification command and has **9 direct native callers** per version.

Therefore native indexed-child storage + Undo is not a capability restricted to the VectorLayer concrete class. Specialized Shape UX insertion has an additional layer-specific command.

## Mask and vector classification share exact MatchName predicates

Three short exported native predicates take **only TDB_StreamIDPath const&**, fetch the last stream ID and compare the associated MatchName. They do not accept a concrete BEE_VectorLayer argument:

| Native path predicate | Accepted end categories from machine-code constants |
| --- | --- |
| BEE_IsShapeGroupOwnerStreamPath | MASK_PARADE or VectorStream VECTORS_GROUP |
| BEE_IsShapeGroupStreamPath | MASK_ATOM or VectorStream SHAPE_GROUP |
| BEE_IsShapeStreamPath | built-in mask shape or VectorStream SHAPE |

In AE2026 the three functions are respectively at RVAs 0x3777f0, 0x377840 and 0x377890. AE2025 has matching implementations at 0x36cdb0, 0x36ce00 and 0x36ce50.

A complete .text direct-call scan shows native BEE_GetMaskVertexSelH and BEE_GetMaskFeatherSelH **actually call** BEE_IsShapeStreamPath for stream type recognition, in BOTH installed versions. Generic BEE_StreamSpec objects carry BEE_Layer* and TDB_StreamIDPath. Thus mask and shape paths share some real editor/selection plumbing, not just similar UI.

Likewise BEE_GetShapePathsVec(BEE_Layer*, vector<TDB_StreamIDPath>*) uses FindStream on its root, then native virtual recursion. It is generic at the formal BEE_Layer argument but requires a real native stream tree.

## Scope and incomplete contracts

This is evidence for a **shared indexed property/selection substrate**, not proof that an ordinary Effect SDK effect can create its own host-recognized indexed property tree. The BEE host still controls the owning Layer, TDB stream factory and canonical streams. It does NOT establish native Pen drag control or BEE_VectorArt output from an effect. The specialized renderer still invokes BEE_VectorStream::PopulateVectorArt with BEE_VectorLayer as its owner.

Direct call counts omit indirect function-pointer/virtual calls and other host modules. All inspected private functions remained uninvoked by our external plugins.

## Product outlook

If CompNodeAE can legitimately establish an editable TDB child group on an independently owned BEE layer/effect, generic Undo, hierarchical stream names and part of native selection may be reusable, reducing custom Timeline UI work. More ambitiously, mask and vector share enough type-classification machinery to justify studying a common editable path abstraction across multiple AE host owners. This is currently **conditional product potential**, not an installed capability.

## Evidence

- datasets/ae-native-svg-paste-stream-owner-commandchain-2025-2026.json
- datasets/ae-native-indexed-contents-owner-command-xrefs-2025-2026.json
- datasets/ae-vector-owner-shape-path-predicate-disassembly-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_svg_paste_owner_commandchain.py
- experiments/vector-shape/probe-src/tools/audit_native_contents_owner_command_xrefs.py
- experiments/vector-shape/probe-src/tools/audit_vector_owner_shape_path_predicates.py
