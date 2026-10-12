---
status: pass-independent-offline-AEX-builds
date: 2026-10-12
evidence: E2-L + compiled public SDK Effect host mock
---

# EXP-SHAPE-049 — Build actual effect-owned CNL vector document bridge, test save callbacks and render

## Requirements

Create a **concrete new Adobe Effect AEX** that owns a standalone independent CNL cubic path archive under a real Adobe public SDK parameter, no Shape Layer, no Mask, no external PICA geometry dependency. Prove host-format callbacks (binary and string), complex nested path traversal and a meaningful rendered output. Do not touch `D:/Developer/CompNodeAE`, perform any AE GUI operations or execute private TDB registration.

## Source and compiled evidence

Complete archived source: `experiments/vector-shape/native-owned-vector-effect-lab/`, self-contained except for the user's own Adobe SDK 25.6. Relevant files: `CNLOwnedVectorEffect.cpp`, `CNLNativeVectorCore.cpp/h`, `VectorRenderer.h`, `VectorBridgeSuite.h`, `OwnedVectorHostMock.cpp`, `CNLOwnedVectorEffect_PiPL.r`, `CMakeLists.txt`, `build_pipl.py`, `verify_owned_vector_aex.py`.

Build 1 at `ShapeLayerAE/build/native_vector_document_effect`, and build 2 at `ShapeLayerAE/build/aeig-owned-vector-independent` **from the archived AEIG copy**. Both x64 Release builds, both PiPL and dependency PE verifications, and both CTest host-mock runs PASS.

Host mock opens the **actual separately built AEX** and calls its real `EffectMain` for GlobalSetup, ParamsSetup, ArbitraryCallback, Render. Six host handle categories undergo NEW/COPY/UNFLATTEN/PRINT-SCAN/INTERP/Dispose. Test generates deeply nested CNL document containing two ellipses using the AEX's native CNL C ABI and verifies the renderer's changed 640x480 output pixels/hash relative to the default doc. It confirms stroke slider changes pixels and optionally preserves input, rejects malformed archives and malformed text, checks comparable documents and simulated host allocations balance to zero.

The PE/PiPL verifier additionally ensures no private FLT/BEE/TDB import, an explicit independent new Effect match name, source not invoking Mask/Shape creation, 8bpc CPU rendering only, correct CNL C API exports, and receipt with exact SHA256 of binary.

**Not observed:** actual AE2026 host acceptance, AEP file persistence and reopening, native Contents/AE Pen, BEE_VectorArt, GPU dispatch, non-8bpc precision.

## Results

See sanitized build receipts:

- `datasets/ae-owned-vector-document-effect-original-offline-receipt-20261012.json`
- `datasets/ae-owned-vector-document-effect-independent-offline-receipt-20261012.json`

### Follow-up experiment

User may install **only `CNLOwnedVectorEffect.aex`** manually to an AE2026 *disposable* project and report: valid plug-in load, effect category/controls, visible ellipse, stroke/color/source checkbox behavior, saving/closing/reopening test, AE warning messages and any crash. This is a public SDK AEX and does not call risky Adobe private registration. User controls all host interactions. Do **not** install/run `CNLPrivateTDBDisposable.aex`.

## Gates

The foundation addresses the plugin-owned data part of C and an independent CPU render path, **not** Phase C host-owned native TDB property tree or Phase D native Pen/Undo or Phase E BEE/RenderGraph. There is no justification to start Phase F integration or edit CompNodeAE.
