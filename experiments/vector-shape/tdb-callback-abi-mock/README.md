# Offline typed native registry ABI mock, NOT the Adobe ABI

Compiles a Windows x64 **DLL and separate EXE** under the same MSVC runtime. Exercises passing a std::function by value across module boundaries, retaining a function object's closure, eager stream construction, a mock MatchName-like 16-byte key, explicit reverse-order deregistration and owner/closure destruction.

This does **not** invoke TDB.dll, BEE.dll, call private Adobe functions, or prove their structures/ownership are correct. The class methods are *functional analogues* of the verified native IsLeaf/GetAsLeaf/SetupCanonicalLayout observations, not compiler-accurate reproductions of AE object layouts.

Build:
    cmake -S D:\Developer\ShapeLayerAE\labs\tdb_callback_abi_mock -B D:\Developer\ShapeLayerAE\build\tdb_callback_abi_mock -G "Visual Studio 17 2022" -A x64
    cmake --build D:\Developer\ShapeLayerAE\build\tdb_callback_abi_mock --config Release
    ctest --test-dir D:\Developer\ShapeLayerAE\build\tdb_callback_abi_mock -C Release --output-on-failure

Important: real native TDB factory registration may retain callbacks even after project close and cannot be simulated by this mock. Do NOT deploy in AE. See F-VECTOR-030/031 and EXP-SHAPE-027/029.


## Exact-native type-signature audit (2026-10-12)

A concrete review found that the original fifth native Creator callback argument was unsigned rather than the correct bool. The offline mock was corrected to (const MatchName&, factory pointer, bool, unsigned int, bool).

NativeABISignatureProbe.cpp now compiles a true MSVC COFF C++ decorated symbol containing the full native TDB class names and std::function Creator template parameter types. verify_symbol_abi.py compares the exact mangled parameter suffix against real RegisterFactoryFunc exports from BOTH the installed AE2025 and AE2026 TDB.dll versions. Both match.

This verifies decorated TEMPLATE TYPES only. It cannot prove lifetime, allocator, C++ object invariants, late host registration or eventual AE native Contents / Pen / VectorArt output.
