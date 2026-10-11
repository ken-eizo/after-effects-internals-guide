---
status: pass-static
last_verified: 2026-10-12
evidence: E2-L
versions: installed AE2025 and AE2026 BEE.dll
---

# EXP-SHAPE-023 — Identify native layer-renderer owner boundary (without Mask or Shape creation)

## Question and non-goals

Does AE's native Shape rendering use a polymorphic layer-owned render entry rather than a hidden Effect SDK vector-output parameter? What new host-native class/owner constraints would a CompNodeAE extension need to implement? Mask/Path/Shape scripting and ordinary PF_World drawing do not satisfy this experiment.

No private runtime functions were invoked, no new AEX built or installed, no AE user project interacted with.

## Method

Four original read-only local scripts:
- audit_vector_native_owner_vs_avlayer_render.py: exact export to x64 .pdata-bounded code / native function call graph (two builds).
- audit_av_vector_raster_vtables.py: read actual exported AV and VectorLayer MSVC vftables and identify direct virtual function RVA/slot, plus GetLayerType.
- audit_native_shape_layer_kind_adapter.py: disassemble native VectorLayer and AVLayer Create allocations, Layer type returns and command wrappers.
- audit_shape_command_layer_creation_target.py: follow native command adapters to shared Undo and BEE_DoCommand wrapper.

The scripts persist exact input SHA256 and raw decoding. No runtime instrumentation or patching.

## Results

1. AVLayer::Rasterize2DGraph and VectorLayer::Rasterize2DGraph are actually at THE SAME virtual slot in their respective classes: index 235 / +0x758 (2025), index 238 / +0x770 (2026). The physical function targets differ for AV vs Vector.
2. GetLayerType uses virtual index 80 / +0x280 in both classes and binaries. Vector returns 4, AV returns 0.
3. Native TDB Create callbacks allocate different C++ class sizes (2025 AV=0x2810, Vector=0x2820; 2026 AV=0x27d8, Vector=0x2830), then invoke distinct constructors.
4. VectorLayer default type magic is 0x05192004 in both inspected versions, unrelated to layer creation command identifiers.
5. BEE_CmdNewVectorLayer passes native command id 0x65 in 2025 vs 0x6a in 2026 via a shared BEE Undo wrapper (resource id 0x306 in both). ModelItem::CreateNewLayer / BEE_CmdNewLayer is another path through host layer command dispatch.

This proves layer type, rendering dispatch, creator allocation and project command identity are separate host contracts. It does not prove third-party subclass/plugin registration.

## Outcome

E2-L evidence positive for a host-native *layer virtual render contract*. **External plugin creating an independently owned host-recognized Contents/geometry layer remains NOT TESTED**. A mere BEE operator or TDB callback registration cannot be treated as native renderer output until a host owner exists.

## Next meaningful experimental gate

Examine the two native registries' complete callback/object ownership and how BEE comp/item layer identities are instantiated from factory entries, without calling private APIs. A gated standalone/disposable-AE attempt would need exact version, safety rollback and a fully valid ref-counted class and canonical stream; a dummy callback or host vtable memory patch is not acceptable.

## Raw material

datasets/ae-native-av-vs-vector-layer-raster-vtable-2025-2026.json
datasets/ae-vector-layer-native-owner-vs-avlayer-render-2025-2026.json
datasets/ae-native-shape-layer-command-type-adapter-2025-2026.json
datasets/ae-native-vector-layer-creation-adapter-target-2025-2026.json
F-VECTOR-025.
