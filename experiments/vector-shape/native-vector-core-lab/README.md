# CNLNativeVectorCore — independent native vector document engine

A native C++17 standalone x64 DLL (20 exported C API functions), intended as the stable CompNodeAE-owned vector document/data engine for a FUTURE genuine AE-native editable vector plugin.

**Status: built and independently verified, NOT integrated with AE native TDB/BEE.**
No AEX is produced by this lab. There is no host-native AE Contents/Pen/VectorArt support yet. This is NOT another Mask/Shape or PF_World workaround.

## Implemented and tested

- 64-bit stable IDs; hierarchical Group / Path, indexed children, cycle-safe move
- Exact cubic geometry in double precision, anchor and relative in/out handles
- Native four-segment ellipse generator; direct C API copy of cubic segments (absolute P0/P1/P2/P3)
- Deep clone, deterministic CNL-owned binary archive with version and FNV checksum
- Native data validation and 2048-deep iterative hierarchy serialization
- Pure extern C ABI for future AEGP/effect/host adapter without sharing private MSVC class vtables or std::function with the caller

## Build and test (on source machine; no AE install)

    cmake -S D:\Developer\ShapeLayerAE\labs\native_vector_core -B D:\Developer\ShapeLayerAE\build\native_vector_core -G "Visual Studio 17 2022" -A x64
    cmake --build D:\Developer\ShapeLayerAE\build\native_vector_core --config Release
    ctest --test-dir D:\Developer\ShapeLayerAE\build\native_vector_core -C Release --output-on-failure
    python D:\Developer\ShapeLayerAE\labs\native_vector_core\test_external_c_abi.py
    python D:\Developer\ShapeLayerAE\labs\native_vector_core\verify_release.py

Built library: D:\Developer\ShapeLayerAE\build\native_vector_core\Release\CNLNativeVectorCore.dll
Built test: D:\Developer\ShapeLayerAE\build\native_vector_core\Release\NativeVectorCoreTest.exe
Build receipt: D:\Developer\ShapeLayerAE\results\native_vector_core_release_receipt_20261012.json

When building this copied source from another folder, call CMake with that folder and set environment variable CNL_NATIVE_VECTOR_CORE_DLL to the resulting DLL path for the ctypes test. The verifier currently assumes the author's local ShapeLayerAE build folder.

## Contents and path conventions

- Root NodeId = 1, name Contents, type GROUP; creates no Adobe TDB object.
- Every new node gets a stable 64-bit ID and an owning parent. Groups accept groups/paths. Paths have 2+ vertices, closed paths have 3+.
- CNL_PathVertex: double x,y; double in_dx,in_dy; double out_dx,out_dy. Handles are RELATIVE to anchor (same conventional representation as host native mask vertices, without using masks).
- CNL_CubicBezier: absolute P0, P1 = P0 + out, P2 = next anchor + next in, P3 = next anchor.
- Archive is CNLVEC01 little-endian, checksum-protected and not AEP, SLU or Adobe binary-compatible.
- Objects may only be concurrently read when not being mutated; callers must coordinate writes. Host adapters should eventually produce immutable snapshots under AE's MFR execution model.
- Any DLL export (no C++ ABI crossing) returns an explicit CNL_Status; callers keep and release their own CNL_Document pointer through cnl_document_destroy.

## Do NOT misclassify this result

The current library cannot be added to After Effects as an effect or AEGP; no private registration is executed. It does not make Adobe's Pen tool target CNL vertices and does not replace AE VectorLayer's Rasterize2DGraph. It is the plugin-controlled authoring data portion only.

The genuinely novel AE host capability remains: new third-party TDB native type -> owned native indexed Contents -> native Pen editing -> BEE evaluator -> BEE_VectorArt -> RG rendering, with no Mask or built-in Shape owner. See AEIG F-VECTOR-025..029, EXP-SHAPE-024..026.
