---
status: pass-compiled-independent-module
last_verified: 2026-10-12
evidence: E2-B
versions: MSVC VS2022 Release Windows x64; Adobe host not used
---

# EXP-SHAPE-026 — CompNodeAE independent native Contents and cubic-path data core

## Hypothesis and strict limits

A stable plugin-owned document and vector geometry model can be built without a Mask, Shape Layer or Effect SDK PF_World, and can be serialized/cloned outside the host. This would be an implementable core for a future AE native-TDB/BEE adapter but is NOT itself a replacement for Adobe's native renderer, timeline or Pen tools.

## Artifact actually built

CNLNativeVectorCore.dll from self-contained original C++17 project.

Local binary:
D:/Developer/ShapeLayerAE/build/native_vector_core/Release/CNLNativeVectorCore.dll

Original source:
D:/Developer/ShapeLayerAE/labs/native_vector_core/

AEIG source-only copy:
experiments/vector-shape/native-vector-core-lab/

C API: 20 exported functions (document, group, path, arbitrary vector vertices, code-generated ellipse, double-precision cubic segments, full document clone, checked parent move, binary serialization/deserialization).

## Validation executed (not just planned)

- CMake VS2022 Release x64 build: PASS.
- CTest actual NativeVectorCoreTest.exe: PASS 100% tests.
- Multiple nested groups and 75 generated paths, stable node ID and child ownership: PASS.
- Code-generated closed ellipse into four cubic Bezier segments: PASS.
- Native relative vertex tangent to absolute cubic control conversion: PASS.
- Clone does not mutate original path: PASS.
- Move preventing parent cycles and invalid Group/Path parent kinds: PASS.
- Two byte-identical archive serializations; save/reload yields same byte stream and hierarchy: PASS.
- Reject corrupt CRC, invalid version, malformed ID, invalid vertex coordinates and insufficient copy buffers: PASS.
- Iterative 2048-deep group hierarchy serialization and reload: PASS.
- Python external ctypes dynamically loading compiled DLL and using 64-bit IDs, generated Bezier data and roundtrip: PASS.
- PE executable architecture, 20 exact exported functions, and no BEE/TDB/AGM dynamic imports: PASS.

Build receipt is in datasets/ae-native-vector-core-release-receipt-20261012.json, with binary hash and repeatable test outputs.

## Reproduce safely (no installation)

In PowerShell:

    cmake -S "D:\Developer\ShapeLayerAE\labs\native_vector_core" -B "D:\Developer\ShapeLayerAE\build\native_vector_core" -G "Visual Studio 17 2022" -A x64
    cmake --build "D:\Developer\ShapeLayerAE\build\native_vector_core" --config Release
    ctest --test-dir "D:\Developer\ShapeLayerAE\build\native_vector_core" -C Release --output-on-failure
    python "D:\Developer\ShapeLayerAE\labs\native_vector_core\test_external_c_abi.py"
    python "D:\Developer\ShapeLayerAE\labs\native_vector_core\verify_release.py"

Do not copy this DLL into the AE Plug-ins folder. It is a reusable C/C++ library, not an AEX or complete TDB-host bridge.

## Remaining unimplemented native host contracts

1. Actual plugin-defined TDB_StreamBase factory Creator (F-VECTOR-026), canonical/class lifetime, CloneStream/Read/Write and correct host owner registration.
2. AE host-recognized custom Timeline Contents indexed tree that belongs to CompNodeAE rather than a built-in Shape Layer or Mask.
3. AE native Pen/Selection/Move/Gizmo editing of this actual plugin-owned path (currently only CNL Core API edits it).
4. Registration of a BEE native vector evaluator for CNL type without leaking a host-owned C++ vtable across plug-in unload (F-VECTOR-028).
5. BEE_VectorArt/RG/AGM production renderer path from an independent host object rather than a PF_World frame.

Until these are proven, the core must not be described as a native AE shape-like effect. It is a real necessary source-side feature, but not proof of the host extension hypothesis.

## Future product significance

This code offers a stable language-neutral native vector-value interface. CNL can generate/edit Contents from code, with persistent identity and cubic precision. If the private AE host integration becomes feasible, the model can be adapted to a completely new editable native vector plugin, whereas an Effect SDK raster preview would have no reusable host vector-value contract.
