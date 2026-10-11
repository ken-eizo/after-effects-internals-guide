---
status: strongly-supported-static
last_verified: 2026-10-12
evidence: E2-L + H
versions: installed AE2025 and AE2026 BEE.dll
---

# F-VECTOR-025 — Native VectorLayer creator, native renderer override and owner ABI

## Scope

The goal is an independently owned, dynamically editable native vector object, not a Mask, script-created native Shape Layer, SVG, custom UI or Effect PF_World rasterizer. No private host code was called or patched in this experiment.

## Actual production native renderer is virtual on the Layer class

MSVC virtual function tables exported by BEE_AVLayer and BEE_VectorLayer contain actual Rasterize2DGraph function addresses, at the SAME slot index within each native host version. Each concrete layer class has a DIFFERENT implementation:

| Binary | AV Rasterize2DGraph RVA | Vector Rasterize2DGraph RVA | slot/index |
| --- | --- | --- | --- |
| AE2025 | 0x28f520 | 0x6e3e90 | 235 / +0x758 |
| AE2026 | 0x298720 | 0x708720 | 238 / +0x770 |

The two vtables also have a common GetLayerType virtual at index 80 (+0x280). In both builds, BEE_AVLayer returns 0 and BEE_VectorLayer returns 4, directly observed in return-value instructions.

This directly proves native vector rendering is bound to concrete host Layer virtual dispatch, not a new Effect SDK output flag. Merely registering another BEE vector evaluator in a separate registry does not make an ordinary effect or AV layer select the VectorLayer renderer. Third-party subclass registration remains unproven.

## Native Creator callbacks allocate different Layer classes

The private factory has distinct BEE_AVLayer::Create and BEE_VectorLayer::Create callbacks returning TDB_StreamBase pointer. Both use U.dll tracked allocation and then directly call the matching concrete C++ Layer constructor with owner/context, TDB factory and MatchName data.

| Host | AVLayer allocated bytes | VectorLayer allocated bytes | Vector GetDefaultTypeMagic |
| --- | ---: | ---: | --- |
| 2025 | 0x2810 | 0x2820 | 0x05192004 |
| 2026 | 0x27D8 | 0x2830 | 0x05192004 |

These constants are from literal immediate arguments to U_MemTrackedObject new and GetDefaultTypeMagic native function returns. They do not provide complete class layouts. Both object sizes changed across versions. Creator RVAs: AVLayer 0x46ef0 / 0x467d0, VectorLayer 0x0b0970 / 0x0b64e0.

The host-specific BEE_VectorLayer::GetVectorArt creates a vector Group, forms a TDB StreamIDPath, calls BEE_VectorStream::PopulateVectorArt with a BEE_VectorLayer owner reference, and computes bounds. This is distinct from the inherited native virtual Rasterize2DGraph and cannot be represented as ordinary effect output.

## Native creation is also a command and project ownership path

BEE_CmdNewVectorLayer is a tiny adapter:
- AE2025 at 0x65cdd0: mov r8d,0x306 ; mov edx,0x65 ; jmp 0x667610.
- AE2026 at 0x6783e0: mov r8d,0x306 ; mov edx,0x6a ; jmp 0x682f90.

The shared implementation constructs a localized command title, obtains BEE_Project::GetUndoContext, opens an Undo group, calls BEE_DoCommand with its command argument and closes Undo. Another path BEE_ModelItem::CreateNewLayer calls BEE_CmdNewLayer; that function has a switch over built-in short identifiers and reaches the same common command logic. Values 0x65 and 0x6a are command identifiers, **not GetLayerType (4)**, which is a separate type space.

This means beyond a private Creator callback the host expects project association, real layer ownership, concrete Layer object vtable, native Undo/command lifecycle and a persistable layer type.

## What an independent native vector plugin actually needs

1. Complete registered native TDB creator, correct canonical instance, lifetime, ABI and serialization — third-party registration NOT proven.
2. Real host-recognized indexed Contents owner under plugin-controlled object, not existing Shape — NOT proven.
3. True BEE Layer/project identity and host command registration — NOT proven.
4. Native Pen/Selection binding to authored editable TDB paths — NOT proven.
5. Native VectorArt evaluation and Rasterize2DGraph dispatch to owner — NOT proven.

These are separate boundaries. The previously tested mask bridge delegates most to a built-in AV Layer, so it cannot establish a novel host-native effect owner.

## Evidence and limits

E2-L installed BEE 2025/2026 PE exports, x64 vtable slot decoding and bounded native code disassembly; NO live AE execution and NO memory modification. Class sizes and vtable offsets are version-sensitive. Generic command dispatch has indirect branches; only observed wrappers and calls are asserted.

The new conclusion is that host-native Shape rendering is implemented by an internal Layer virtual override. An Effect SDK output requires separate host owner/renderer integration; ordinary PF_Render does not expose that contract.

## Reproducibility

- datasets/ae-native-av-vs-vector-layer-raster-vtable-2025-2026.json
- datasets/ae-vector-layer-native-owner-vs-avlayer-render-2025-2026.json
- datasets/ae-native-shape-layer-command-type-adapter-2025-2026.json
- datasets/ae-native-vector-layer-creation-adapter-target-2025-2026.json
- Script copies under experiments/vector-shape/probe-src/tools: audit_av_vector_raster_vtables.py, audit_vector_native_owner_vs_avlayer_render.py, audit_native_shape_layer_kind_adapter.py, audit_shape_command_layer_creation_target.py.
