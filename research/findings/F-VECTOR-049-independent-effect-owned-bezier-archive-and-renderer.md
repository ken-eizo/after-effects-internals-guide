---
status: pass-offline-real-AEX-two-independent-builds-host-test-pending
date: 2026-10-12
evidence: E2-L + offline compiled AE-SDK-host-mock; NO in-host AE execution
sdk: Adobe After Effects SDK 25.6 x64, VS2022 Windows
---

# F-VECTOR-049 — Independent effect-owned cubic Contents data and renderer implemented without Mask/Shape carriers

## This is actual new plugin code, not another native API symbol hypothesis

Prior F-VECTOR-039–048 proved important proprietary TDB/BEE owner/factory/Canonical UILayout boundaries but found no demonstrated third-party native group registration, Pen target, or BEE VectorArt route. A separate earlier proof `CompNodeAEVectorEffect.aex` rendered external PICA vector geometry but did **not** store its own editable/persistent geometry in the Effect.

The new built `CNLOwnedVectorEffect.aex` now embeds the original standalone `CNLNativeVectorCore` directly and owns **an independent Group/Path/Bezier document** through a real `PF_Param_ARBITRARY_DATA` parameter. This is not stored in a Mask or Shape Layer. The default document has root Contents, child group and true double-precision four-cubic ellipse; a separate test-created nested document has multiple groups and two differently positioned curves.

## Implemented host storage contract

The compiled AEX implements `PF_Cmd_ARBITRARY_CALLBACK` with **NEW, DISPOSE, COPY, FLAT_SIZE, FLATTEN, UNFLATTEN, INTERP, COMPARE, PRINT_SIZE, PRINT and SCAN**. The custom host-owned handle stores only a tiny fixed header and CNL's versioned/checksum-protected `CNLVEC01` archive; binary FLATTEN/UNFLATTEN exchange precisely the archive bytes, not an unsafe struct with pointers. Validation rejects malformed, truncated, corrupted, oversized (1 MiB cap) and unsupported archive versions before attaching a host handle.

PRINT/SCAN use reversible `CNLVEC1:` followed by uppercase hexadecimal archive bytes, not the earlier throwaway descriptive text. Text parsing checks the exact prefix, even digit count, hex validity, size bound and full CNL archive integrity. Keyframe interpolation is explicitly **step/discrete** (at t less than 0.5 take left; otherwise right), avoiding bogus assumptions about different hierarchy/keyframe vertex topology.

Effect render path: host arbitrary parameter bytes → CNL deserializer → iterative traversal of CNL-owned Groups/Paths → genuine CNL cubic segments → the compiled 8bpc antialiasing CPU renderer → public PF_World. Stroke Width/Stroke Color/Transparent Input are visible standard AE Effect controls. No external PICA source, no TDB/BEE/FLT private imports, no host Mask/Shape generation. The 8bpc renderer is currently a staging implementation, NOT the requested native BEE_VectorArt output.

## Independent repeatability

Two separately compiled real Windows x64 AEX binaries were created:

1. Original `D:/Developer/ShapeLayerAE/labs/native_vector_document_effect` source, native AEX in `D:/Developer/ShapeLayerAE/build/native_vector_document_effect/Release/CNLOwnedVectorEffect.aex`.
2. A source-only *standalone AEIG archive* `experiments/vector-shape/native-owned-vector-effect-lab` with its own copied original core C++/header, renderer, host mock and SDK PiPL generator; a fresh compilation outside the repository at `D:/Developer/ShapeLayerAE/build/aeig-owned-vector-independent` with no previous build outputs.

Both builds PASS compiled AEX load by standalone mock (not AE), per-effect parameter registration, host-style allocation/disposal, independent nested document creation, checksum integrity, binary roundtrip, PRINT/SCAN roundtrip, deliberately corrupted/truncated archive rejection, both default and nested document image hash differences, visible change on Stroke Width, transparent overlay and underlying source compositing, plus no leaked simulated handles.

Both are verified with PE import/exports and PiPL checks. The compiled AEX imports only Windows/VC runtime dependencies and **no TDB.dll, BEE.dll or FLT.dll**. Its CNL source handles all geometry and archive operations; the temporary standalone host mock is not an AE process.

## What is **NOT** demonstrated, despite a functioning AEX

- Actual AE 2026 application acceptance, parameter saves to AEP, close/reopen/undo compatibility, or native timeline cache lifecycle are **unverified until a user-controlled host test**.
- PF_Param_ARBITRARY_DATA is host serialized as an Effect parameter, **not** an actual Adobe `TDB_NamedStreamGroup` with independently inserted host-owned `Contents` child in the Effect Parade.
- Adobe's Pen/Selection does not target this custom CNL archive. No native editable vertices in Composition Viewer and no `BEE_Layer` + `TDB_StreamIDPath` native identity were established.
- Renderer is CPU 8bpc `PF_World`, not `BEE_VectorArt`/RG and not GPU/16/32-bpc. UI currently exposes stroke/color only, not CNL vertex manipulation.
- The AEX is not ready to integrate into `CompNodeAE`; Phase F is deliberately paused pending the user's design decision.

This is a crucial **data owner + persistent serialization callbacks + visible renderer path** proof while native AE editable Contents/Pen/RenderGraph remain distinct open requirements. It avoids lying about the full native plugin.

## Evidence

- `experiments/vector-shape/native-owned-vector-effect-lab/` — self-contained original source, CMake, PiPL, native CNL core, standalone mock and verifier (Adobe SDK not redistributed).
- `datasets/ae-owned-vector-document-effect-original-offline-receipt-20261012.json`
- `datasets/ae-owned-vector-document-effect-independent-offline-receipt-20261012.json`
- `experiments/vector-shape/EXP-SHAPE-049-effect-owned-native-cubic-archive-bridge.md`.

Only manual, disposable AE-host installation would establish actual AE 2026 acceptance and persistence. Do NOT test the unrelated private-registry disposable AEX.
