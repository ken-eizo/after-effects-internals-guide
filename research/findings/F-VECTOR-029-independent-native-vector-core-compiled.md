---
status: compiled-and-verified-host-independent
last_verified: 2026-10-12
evidence: E2-B plus E2-L context
versions: Windows x64 MSVC VS2022; AE SDK25.6 is NOT required to build this library
---

# F-VECTOR-029 — Plugin-owned Contents data engine built without Mask or Shape Layer

## Why an independent core is necessary but NOT sufficient

The intended CompNodeAE vector plugin must generate real cubic paths as persistent, plugin-owned values and eventually make them recognized by After Effects as host-native editable Contents. Public Mask and Shape paths cannot solve the latter owner problem. The first practical source implementation of the former is now compiled as CNLNativeVectorCore.dll, a standalone native C++ library with a stable external C ABI. This is new executable code, not just an architecture theory.

There is **no AE host-native registration** in this DLL; it is not itself an AEX and cannot be inserted into the AE timeline or edited through AE Pen tools. Even though it owns geometry, its document hierarchy is a CNL model, not an Adobe TDB_IndexedStreamGroup instance, its archive format is not AEP/SLU, and it does not call any private Adobe API.

## Completed native C++ features

- Explicit CNL_NODE_GROUP and CNL_NODE_PATH with stable 64-bit IDs and checked parent ownership.
- Indexed nested Contents with insertion and moving, cycle rejection, identity preservation, and read-only traversal.
- Genuine two-dimensional double-precision cubic Bezier vertex positions and relative incoming/outgoing control handles.
- A C ABI function returning 3rd-order cubic segments directly without rasterization (closed or open paths).
- Code-driven ellipse generator exposing 4 cubic segments, with valid independent native geometry data; no conversion through SVG/Mask/Shape.
- A real deep-copy document clone; edits to a cloned path do not mutate original documents.
- CNL-owned deterministic, versioned, checksummed, little-endian serialized document format; exact binary roundtrip with ID and hierarchy retention.
- Input validation for invalid coordinates, invalid parent kinds, cycle moves, buffer lengths, corrupt checksums and unsupported archive versions.
- Iterative traversal in the serializer, validated against 2048 nested groups (avoids native C++ stack overflow from recursive group serialization).
- Stable C ABI, built Windows x64 DLL+import library; no Adobe BEE/TDB/AGM DLL imports.

## Concrete build and independent verification

Local build output:
D:/Developer/ShapeLayerAE/build/native_vector_core/Release/CNLNativeVectorCore.dll

Independent test executable:
D:/Developer/ShapeLayerAE/build/native_vector_core/Release/NativeVectorCoreTest.exe

The project was compiled with CMake and Visual Studio 2022 in Release mode. Actual native DLL verification:
- CTest: 100% tests passed.
- Python ctypes loaded this specific compiled DLL, created a 64-bit node group and generated ellipse, copied 4 cubic paths across the dynamic C ABI, serialized/reloaded a document and verified hierarchy.
- A PE verifier matched the complete 20-function exported C API list, x64 machine architecture and absence of BEE.dll/TDB.dll/AGM.dll imports.
- Release receipt: datasets/ae-native-vector-core-release-receipt-20261012.json. SHA256 and local testing output are recorded there.

Source-only lab:
experiments/vector-shape/native-vector-core-lab/
(CNLNativeVectorCore.cpp/.h, NativeVectorCoreTest.cpp, CMakeLists.txt, test_external_c_abi.py, verify_release.py, README.md).

## The future integration contract

The bridge from the independent CNL model to Adobe-owned native behavior needs:

1. A verified, version-pinned external TDB stream type Creator with correct native clone, canonical, serialize and ownership lifecycle. F-VECTOR-026/027 identify pieces but no external registration has been attempted.
2. A legitimate host-recognized parent that owns the custom Contents indexed group in AE's Timeline, Undo and AEP project, rather than a second data tree rendered as a fake overlay.
3. Routing of native editor hit testing and Pen/Selection tools to that owner, preserving TDB_StreamIDPath and path OriginInfo.
4. Registration or equivalent integration with BEE's separate MatchName-to-Operator evaluator registry (F-VECTOR-028), observing reference counting and module unload.
5. BEE_VectorArt -> RG/AGM rendering with host-native context and cache/time dependencies; PF_World-only effect output would not satisfy the goal.

CNLNativeVectorCore's C ABI is deliberately independent of private MSVC C++ class layouts so that it can be integrated through a future version-specific host adapter while remaining stable itself. The core C API does not pretend to be compatible with Adobe's private TDB ABI. New AEX modules and host registry tests must be gated separately and remain user-controlled.

## Important limitations

This is a tested DLL, **not the final AE plugin**, not a native host Contents type, not AE-native path editing, not an operator or layer registered with BEE/TDB, and not a host vector renderer. It is not yet thread safe for concurrent mutation: host adapters must serialize writes or provide immutable snapshots. Serializing the core document produces a CNL archive, NOT an AEP-native object. The direct source CNL document model is suitable for further integration, but does not remove the host-native owner barrier.

## Larger creative future

If the host integration succeeds, CNL code-generated vector paths and arbitrary procedural geometry could become independent first-class AE-native typed objects, with editable paths, custom vector modifiers and node-generated Contents rather than a raster effect or a built-in Shape/Mask wrapper. That is the envisioned next generation of CompNodeAE, not a claim of present host capability.
