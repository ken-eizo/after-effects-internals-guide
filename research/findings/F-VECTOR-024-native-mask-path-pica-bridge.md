---
status: sdk-grounded-compiled-not-host-tested
last_verified: 2026-10-12
evidence: E0-H + E0-S + compiled-PE + H
versions: Adobe AE SDK25.6, Windows x64 local build, AE2026 pending
---

# F-VECTOR-024 — Code-authored PICA curves into REAL native editable masks on an ordinary AE layer

## Why this is a distinct host-native experiment

The already-host-confirmed CompNodeAE Vector Effect generates Bezier curves but only uses its own pixel compositor. A newly built AEGP now consumes the *real separately compiled* PICA provider's 4 cubic segments and creates a host-owned native Mask Outline on a normal solid or footage layer (no Shape Layer, no ExtendScript, no external rasterizer). The exact native Mask Path is potentially editable with AE's Pen and Selection tools, participates in layer Mask Parade, host Undo, project serialization and, when ADD is selected, AE's native mask renderer.

This is a native *mask* interface, not a new effect-owned Vector Contents, not BEE_VectorArt output, not custom BEE operator installation, and not a live link from edited mask back to CNL code. Scripting can create regular masks too; the unique verified incremental engineering feature is the direct C++ PICA geometry-to-authored host-native stream bridge, NOT discovery of an unknown native API.

## Implemented artifact

D:/Developer/ShapeLayerAE/build/native_editable_path/Release/NativeEditablePathBridge.aex

NativeEditablePathBridge.cpp (AEGP with its own PiPL) registers three explicit Animation menu commands:

- CompNodeAE: Create Native Editable Mask from PICA — create a native closed four-vertex Bezier Mask Path on a selected ordinary AV layer, mask mode NONE, preserving the visible layer.
- CompNodeAE: Native Mask Renderer (ADD, Clips Layer) — same geometry but Mask Mode ADD, allowing the host's native mask compositor to cut out the selected ordinary layer (still NOT the Shape renderer).
- CompNodeAE: Inspect Native Owner Roots (Read Only) — record selected layer object type and the actual root group's direct TDB/AEGP child MatchNames at TEMP/CNL_NativePath_OwnerProbe.tsv without modifying the project.

Commands are opt-in, reject non-AV owners, refuse if the PICA geometry provider is missing, reject invalid source size/NaN geometry, and use native Undo. A failed partial insertion is explicitly deleted. There are no private BEE/TDB API calls.

## Exact cubic geometry preserving tangents

Native AEGP_MaskVertex tangents are relative to each vertex (see SDK AE_EffectSuites.h / AE_GeneralPlug.h). The source cubics are 4 segments, each described by absolute control points P0,P1,P2,P3. For vertex i:

- anchor = curve[i].P0 + (source_width/2, source_height/2)
- native out tangent = curve[i].P1 - curve[i].P0
- native in tangent = curve[previous].P2 - curve[i].P0

AEGP_CreateVertex followed by AEGP_SetMaskOutlineVertexInfo and AEGP_SetMaskOutlineOpen(FALSE) constructs the same closed cubic geometry. The existing Adobe SDK distributed AEGP/Projector/Projector.cpp demonstrates the mask outline creation pattern and the SetStreamValue/DisposeStreamValue lifecycle.

## Scope and evidence level

Compiled successfully by Visual Studio 2022 x64 with SDK25.6. The AEX has a valid PiPL resource and EntryPointFunc; no BEE.dll or TDB.dll import. A static verifier checked command names, callback opt-in guards, native stream APIs, tangent assignment, invalid geometry guards, cleanup and stored the SHA256 receipt at D:/Developer/ShapeLayerAE/results/native_editable_path_qa_20261012.json.

**Not yet installed by assistant, not yet user-tested in AE; therefore NOT claimed successful native Pen editing or native Mask rendering.** The user explicitly controls all installation and real AE UI tests.

## Why this matters for the larger CompNodeAE goal

F-VECTOR-021 found exact native BEE Shape/Mask selected-path classification shares terminal TDB_MatchName predicates and generalized BEE_StreamSpec. The new AEGP is a practical external entry point into this genuine common editor infrastructure. Compare the same active layer before/after a PICA-created Mask and a separate built-in Shape Layer using its read-only owner tree probe. This can isolate which owner, source ID, stream and renderer contracts already work for an ordinary AV layer.

The goal remains a standard Effect SDK plug-in that OWNS independent Contents, native Pen editing and native BEE_VectorArt output. Mask ownership is BEE AV layer-owned, not the effect. The native mask renderer is not the production Shape vector operator renderer. Only a genuinely new effect-owned host stream and BEE operator would satisfy the final breakthrough.

## Experiments

EXP-SHAPE-022 and manifests; experiments/vector-shape/native-editable-path-lab/ (source-only), no proprietary Adobe binaries.
