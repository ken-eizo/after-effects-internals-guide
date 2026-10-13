---
date: 2026-10-14
status: PASS actual Windows MSVC x64 compiled cross-DLL owner mock; NOT Adobe host acceptance
evidence: three real native binaries + CTest 1/1
---
# F-VECTOR-069 — Cross-DLL C++ foreign Layer cloning, RTTI, Comp ownership and safe lifetime tested

To implement (rather than merely reason about) the necessary native class contracts discovered in F-VECTOR-068, a brand-new native Windows x64 test was built in D:/Developer/ShapeLayerAE/labs/foreign_native_owner_abi_mock:

- MockHostABI.dll exports C++ base classes MockTDB_StreamBase and MockBEE_Layer.
- ChapeForeignOwner.dll defines a real externally compiled ChapeNativeLayer derivative, and a separate TDB-only CustomNonLayer derivative, with virtual Clone and correct constructor/destructor tracking.
- ChapeCrossDLLNativeOwnerTest.exe dynamically loads that module using Win32 LoadLibrary, verifies an ABI version, creates provider objects, calls polymorphic Clone across modules, performs dynamic_cast from TDB base to Layer, and accepts only valid BEE Layer clone objects into a Comp owner collection.
- It rejects a non-Layer TDB object, distinguishes original from cloned object, preserves stable identity, and checks that no module unload is attempted while any provider virtual method table is still reachable. All instances are destroyed before FreeLibrary.

The executable MSVC Release test passed CTest 1/1.

CRITICAL LIMITATION: The DLLs contain our MOCK base class ABI, not real Adobe TDB_StreamBase or BEE_Layer. The simulated Comp owner and extension factory are our code. Adobe AEGP does not publicly provide these hooks. A mock that accepts a foreign class does not demonstrate that the stock unmodified Adobe AE 2026 will do so. AE-native ChapeLayer, Contents, Pen/Selection, host Undo and BEE_VectorArt remain unimplemented and unproven.

Rebuild from:
experiments/vector-shape/probe-src/labs/foreign_native_owner_abi_mock
Evidence: EXP-SHAPE-069.

No Adobe DLL loaded by the experiment and no Adobe host or user project modified.
