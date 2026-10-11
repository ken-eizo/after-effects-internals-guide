---
status: compiled-awaiting-user-AE-host-test
last_verified: 2026-10-12
evidence: E0-H + E0-S + compiled-PE
versions: Adobe SDK 25.6, AE2026 target
---

# EXP-SHAPE-022 — Native Pen-Editable Mask Path From PICA Without a Shape Layer

## Test question

Can a separately built AEGP receive procedural cubic geometry from the host-confirmed public PICA provider and author a true native AE Mask Path on a selected ordinary AV layer? Does AE's own native Pen tool edit it, and does AE's Mask ADD compositor use that geometry without our PF_World rasterizer?

This is a **host-owned native Mask**, not a new effect-owned Contents stream or BEE_VectorArt operator. The user will independently test it.

## Compiled stage

Built D:/Developer/ShapeLayerAE/build/native_editable_path/Release/NativeEditablePathBridge.aex, with correct SDK25.6 PiPL, exported EntryPointFunc and no private Adobe BEE/TDB imports. Static PE/source verification PASS, captured by D:/Developer/ShapeLayerAE/results/native_editable_path_qa_20261012.json.

The assistant did not install the plugin or interact with AE UI.

## Required host procedure (user-controlled)

1. Install the new NativeEditablePathBridge AEX separately; retain the working VectorBridgeAEGP provider. Restart AE on a test project, select a normal solid.
2. Animation menu > CompNodeAE: Create Native Editable Mask from PICA. Inspect Mask 1 > Mask Path under this same solid. Use Pen/Selection tool to edit the four genuine cubic points. Mask NONE should preserve underlying solid pixels.
3. Undo and redo; optionally save/reopen a throwaway project to check native persistence.
4. On a second solid call Animation > CompNodeAE: Native Mask Renderer (ADD, Clips Layer). Check that the actual host native mask compositor clips the layer and the Pen edit updates that matte.
5. Run Animation > CompNodeAE: Inspect Native Owner Roots (Read Only) on both normal solid and built-in Shape Layer. The output is TEMP/CNL_NativePath_OwnerProbe.tsv and is overwritten per call; preserve copies.
6. Return screenshots and precise errors if any. The assistant will then promote evidence to E2-X only if the actual host test succeeds.

## Progress status and falsification

- Windows x64 compiled AEGP/real PiPL: PASS.
- PICA source geometry independently confirmed inside AE2026 in preceding F-VECTOR-020: PASS (earlier experiment).
- This new plugin actually creating a native mask inside AE: NOT YET TESTED.
- Native Pen editing and mask ADD compositor: NOT YET TESTED.
- Independent effect-owned Contents and native Shape renderer: NOT IMPLEMENTED.

## What this product feature enables, conditionally

The practical bridge would let a procedural plug-in create a true host-native Mask Path on an ordinary footage/solid layer, ready for native Pen editing, Timeline keyframes, host Undo, save/reopen and native mask compositing. This is qualitatively distinct from merely rasterizing a curve in an effect, while still falling short of an effect-owned Contents tree.

Code and reproducer: experiments/vector-shape/native-editable-path-lab; research/findings/F-VECTOR-024-native-mask-path-pica-bridge.md.
