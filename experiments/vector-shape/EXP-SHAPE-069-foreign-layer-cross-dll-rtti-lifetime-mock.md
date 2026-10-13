---
date: 2026-10-14
status: PASS actual independent MSVC Windows x64 C++ DLL interop 1/1 CTest
---
# EXP-SHAPE-069 — Native foreign C++ Layer RTTI/Clone/Comp ownership mock

Actual MSVC compiler built MockHostABI.dll, ChapeForeignOwner.dll, and ChapeCrossDLLNativeOwnerTest.exe. The host loads the separate provider through Win32 GetProcAddress, validates ABI version, creates its new ChapeNativeLayer subclass, executes polymorphic Clone across DLL boundaries, performs dynamic_cast from a shared exported StreamBase to a Layer base, and transfers the clone into a Comp owner collection. A separate non-Layer TDB object is rejected. Stable ID is preserved, all vtable-bearing instances are destroyed and counted before FreeLibrary.

CTest 1/1 PASS on Windows x64 Release.

This mock intentionally defines its own classes and extension registry, not Adobe's BEE/TDB ABI. It does not prove that unmodified Adobe AE accepts a foreign BEE_Layer, and it cannot be installed as an AE native Layer. Its purpose is to verify C++/DLL ownership and RTTI lifetime invariants offline. Details in F-VECTOR-069.
