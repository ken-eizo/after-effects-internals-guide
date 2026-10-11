---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L
versions: AE2025 and AE2026 BEE.dll, local static bytes only
---
# EXP-SHAPE-020 — Common indexed Contents command, shared native mask/vector path classification and SVG root ownership gate

## Goal

Separate three concepts: (1) TDB indexed children and host Undo, (2) selection classification for Mask/Vector paths, and (3) the owner precondition for SVG→native Contents importer. Test from machine code across AE2025/2026. Do not invoke private functions inside active AE.

## Experiments and actual observations

**General native indexed children**: BEE_CmdAddToIndexedStreamGroup is typed with BEE_Layer*, looks up parent TDB stream, creates a new child by MatchName, sets display name and enters host undo group. A full exact BEE native CALL scan found 13 direct callers in 2025 and 2026, including mask/material/light/layer-set code, contrasting with a specialized BEE_CmdAddVectorProperty(BEE_VectorLayer*) (9 native callers per version).

**Mask and vector sharing**: the exact BEE_IsShapeGroupOwnerStreamPath, BEE_IsShapeGroupStreamPath and BEE_IsShapeStreamPath native functions only inspect the terminal TDB_StreamID MatchName, and check paired Mask Parade/Atom/Shape vs native Vector Contents/Group/Shape names. BEE_GetMaskVertexSelH and BEE_GetMaskFeatherSelH actually call the shared shape-stream predicate. This confirms shared path-type classification, not complete Pen-handler interoperability.

**SVG importer preconditions**: in AE2026 BEE_CmdPasteSVGIntoLayer command, a callback at 0x57e400 builds the ROOT_VECTORS_GROUP path, invokes TDB_StreamGroup::FindStream (0x57e471), checks the result at 0x57e484 and **branches to cleanup if null** at 0x57e487. Only after additional native group virtual checks does it call BEE_PasteSVGIntoComp (0x57e554). Therefore this path cannot create root vectors for an arbitrary BEE_Layer that does not own the native root.

Second cleanup callback at 0x57e790 finds root and removes generated vector group entries by path/Undo, demonstrating a normal host stream-owner lifecycle.

## Verdict

Shared indexed hierarchy and selection internals are materially broader than built-in Shape Layer alone. But the SVG paste path is NOT a shortcut to creating independent effect-owned native Contents; a pre-existing legitimate Root Vectors group is required.

## Evidence

- research/findings/F-VECTOR-021-shared-indexed-contents-and-mask-shape-selection.md
- research/findings/F-VECTOR-022-svg-importer-requires-preexisting-native-root.md
- datasets/ae-native-indexed-contents-owner-command-xrefs-2025-2026.json
- datasets/ae-vector-owner-shape-path-predicate-disassembly-2025-2026.json
- datasets/ae-native-svg-paste-stream-owner-commandchain-2025-2026.json
- datasets/ae-svg-contents-owner-async-callback-and-find-2026.json
- datasets/ae-vector-root-contents-rip-ownership-xrefs-2026.json

All source scripts archived in experiments/vector-shape/probe-src/tools/. No AE project/plugin files modified.
