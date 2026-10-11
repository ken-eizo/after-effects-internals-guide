---
status: confirmed-in-host
last_verified: 2026-10-11
evidence: E0-H + E0-S + compiled-PE + E2-X + H
versions: Adobe SDK25.6 / Visual Studio 2022 x64 build, Windows
---
# F-VECTOR-019 — Adobe-supported PICA suites permit non-raster Bezier data exchange between an AEGP and an effect

## Adobe-distributed executable API pattern (E0-S)

Distributed SDK source Examples/AEGP/Sweetie/Sweetie.cpp registers a DuckSuite function-pointer table through SPSuitesSuite::AddSuite(kSPRuntimeSuiteList, null host, suite name, api version, internal version, procedure table, SuiteRef). The SDK effect Examples/Effect/Checkout/Checkout.cpp acquires that same suite via AEFX_SuiteScoper and invokes it. The corresponding documented SDK header Examples/Headers/SP/SPSuites.h explicitly says suites are used by plug-ins to interact with the application and with each other. This establishes **the mechanism** as an Adobe-sample-supported extension surface, unlike the private TDB/BEE geometry registries.

SPBasic.h discusses unload/reload safety and replacing procedure pointers before unloading; a trivial global registry pointer is not production-safe across dynamic unloading. The consumer must acquire/release suites correctly; the producer must remain loaded while its function pointers are in use. **One actual AE2026 host run confirmed PICA geometry handoff**, but provider/consumer restart ordering, MFR concurrency, error recovery and project/session lifetime still require controlled testing.

## Original source-only proof created in ShapeLayerAE

lab: D:/Developer/ShapeLayerAE/labs/vector_bridge/

- VectorBridgeSuite.h defines a C-compatible versioned suite with double-precision cubic Bezier POD (8 doubles, 64 bytes), schema and caller-owned buffers; no PF_World, no native Adobe private objects.
- VectorBridgeAEGP.cpp registers the suite via public Adobe PICA. DescribePath returns a closed 4-segment contour; CopyCubicPath creates a time-dependent circle/ellipse in layer-local coordinates.
- VectorBridgeConsumer.cpp registers an **actual Effect SDK plug-in** and acquires the custom suite to retrieve the four numeric cubic curves. The effect itself passes its input pixels through unchanged and exposes the connection status via its About response. It does NOT return BEE_VectorArt as its output.
- Two original PiPL .r resources and a standalone CMake project build both plug-ins separately.
- VectorBridgeHostMock.cpp is a minimal third-party PICA stand-in for a separate binary ABI smoke test; it is not Adobe After Effects. It was subsequently executed and passed after its PF_UtilCallbacks::ansi.sprintf stub was initialized.

Both independently compiled .aex artifacts passed static PE verification of AMD64, expected exports, resource directories, matching Suite identifier and no static BEE.dll/TDB.dll imports. In **user-observed AE2026 execution**, `Vector Bridge Consumer (Research)` showed **`PICA suite: connected`**, **`Native Bezier segments: 4; first X: 100.00`** in its About dialog (E2-X). The original built version emitted recoverable code-vs-PiPL version and flags mismatch dialogs, and an MFR notice. A corrected consumer binary was built, its serialized PiPL verified, and its AEGP+Effect runtime handshake passed an **independent PICA mock**; the corrected binary was **not yet retested inside AE**. Original proof and patch receipts are separated in F-VECTOR-020 / EXP-SHAPE-019.

## New actual product capability if next gate passes

A cross-effect procedural vector information protocol is viable *in principle* without waiting for a private Shape extension. A CompNodeAE producer could publish an immutable geometry snapshot, and a different CNL-aware effect plug-in could consume it without any intermediate texture. Native AE render scheduling, transfer identity and composition cache invalidation do not automatically follow from a PICA suite, however; a PICA suite is a **process service**, not an AE render dependency declaration. Future designs must use explicit effect-input identities, epoch/versioning and host-correct checkout under MFR.

**No claim** of native Contents, AE Pen Tool interoperability, Adobe VectorArt output, new render node type or general effect-to-effect socket availability is made.

## Sources and reproducibility

Adobe-distributed SDK 25.6 local headers Examples/Headers/SP/SPSuites.h, SPBasic.h and Examples/AEGP/Sweetie + Examples/Effect/Checkout; source copied as original lab only (not Adobe SDK source). Exact source is mirrored in experiments/vector-shape/vector-bridge-lab; reproducible CMake build instructions in the lab README; compiled files deliberately omitted from Git.
