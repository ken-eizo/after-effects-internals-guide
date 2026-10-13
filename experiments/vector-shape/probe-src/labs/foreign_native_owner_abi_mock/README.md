# ChapeLayer Cross-DLL Native Owner ABI mock

**Actual, built MSVC Windows x64 native DLL interop test. NOT Adobe BEE/TDB.**

Goal: reproduce the *shape* of the original BEE_Layer::CloneAndAttach
contract recovered in F-VECTOR-068 without guessing/private-calling Adobe
classes. This tests the fundamental C++/Windows rules needed for any
independent native Layer class.

## Built targets

- MockHostABI.dll — simulator of an exported TDB_StreamBase and
  BEE_Layer C++ base ABI, with a virtual clone and RTTI.
- ChapeForeignOwner.dll — a distinct extension DLL defining a true
  externally compiled ChapeNativeLayer C++ subclass with type ID 42.
- ChapeCrossDLLNativeOwnerTest.exe — simulates a CompItem-style owner.

## Actual tests

- Load external provider via Win32 LoadLibrary + GetProcAddress.
- Demand the agreed ABI version before first use.
- Create a foreign native object and call virtual clone across DLLs.
- Dynamic_cast cloned TDB_StreamBase to shared imported BEE_Layer RTTI.
- Reject a TDB_StreamBase instance that is NOT a BEE_Layer.
- Transfer the actual clone (not original) into the Comp owner collection.
- Preserve stable layer identity through clone and inspect type ID.
- Ensure no plugin DLL unload is attempted while **any** original or
  cloned foreign vtable-bearing objects remain alive.
- Destroy all host and plugin-owned instances, validate live count 0,
  then FreeLibrary.

This exercise matters because the **real** Adobe function calls exported
TDB_StreamBase::Clone and then performs __RTDynamicCast from
TDB_StreamBase to BEE_Layer before attaching. But this test uses only the
*simulated* exported C++ base classes, not Adobe's binary classes.

## Reproduce

    cmake -S D:\Developer\ShapeLayerAE\labs\foreign_native_owner_abi_mock -B D:\Developer\ShapeLayerAE\build\foreign_native_owner_abi_mock -G "Visual Studio 17 2022" -A x64
    cmake --build D:\Developer\ShapeLayerAE\build\foreign_native_owner_abi_mock --config Release
    ctest --test-dir D:\Developer\ShapeLayerAE\build\foreign_native_owner_abi_mock -C Release --output-on-failure

## Critical blockers to real Adobe native ChapeLayer

The mock **intentionally contains an external constructor and host Comp
owner that Adobe's publicly supported SDK DOES NOT expose**.

Passing this executable therefore proves *none* of:
- an unmodified AE CompItem accepting a CNL BEE_Layer derived class;
- registering TDB_StreamBase foreign subclass in real TDB type factories;
- a new integer Layer kind in the closed BEE_Layer::CreateLayerFromType;
- native AE Timeline Contents, native Editor Pen/Selection, host Undo;
- actual VectorArt/AGM/RenderGraph rendering or .aep save/reopen.

In fact F-VECTOR-070 shows 2025/2026 native BEE_Layer layout and vtable
offsets differ. Never transplant these MOCK classes into AE, modify Adobe
DLLs, or call private constructor/attach functions from the test. The
purpose is to validate our own C++ owner lifecycle independently of the
still-unproven Adobe extension ABI.

No CompNodeAE files touched. No AE GUI or Adobe private calls.
