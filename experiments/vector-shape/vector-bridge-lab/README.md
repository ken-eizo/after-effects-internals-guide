# CompNodeAE PICA Vector Bridge Lab (SDK 25.6)

This is a **research-stage, compiled two-plug-in demonstrator** of non-raster native numeric path exchange. It is not a native Shape Layer replacement and it is not an AEGP/BEE private-API registration test.

## Source architecture

- VectorBridgeSuite.h — original stable v1 interface: four caller-owned 64-byte cubic Beziers, double precision, time numerator and denominator, explicit path kind/schema guard. This returns geometry **not pixels**.
- VectorBridgeAEGP.cpp — native Adobe AEGP, uses the **public PICA SPSuitesSuite::AddSuite** API to register a named geometry provider. Returns time-varying circle or ellipse Bezier data.
- VectorBridgeConsumer.cpp — ordinary Adobe Effect SDK plugin, acquires the geometry PICA Suite. Its render selector still copies the original PF_World input unchanged. About returns the number of received Bezier segments. Pixel compositing remains Adobe's ordinary effect contract.
- VectorBridgeHostMock.cpp — standalone minimal PICA test runner for the two actual compiled AEX binaries. **Executed successfully** after supplying the mock PF_UtilCallbacks::ansi.sprintf required by the effect About handler. It is not an AE runtime substitute.
- verify_vector_bridge_staging.py — uses PE metadata inspection only (no execution) to verify entrypoints, PiPL resource directories, suite identifier and hashes.

Adobe's distributed SDK25.6 Examples/AEGP/Sweetie demonstrates an AEGP suite provider; Examples/Effect/Checkout demonstrates a real effect acquiring and using that suite. This original lab was independently written, not copied from Adobe sample code.

## Build (Windows, Visual Studio 2022, local SDK)

    cmake -S D:\Developer\ShapeLayerAE\labs\vector_bridge -B D:\Developer\ShapeLayerAE\build\vector_bridge -G "Visual Studio 17 2022" -A x64
    cmake --build D:\Developer\ShapeLayerAE\build\vector_bridge --config Release
    python D:\Developer\ShapeLayerAE\labs\vector_bridge\verify_vector_bridge_staging.py

Build outputs:

    D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeAEGP.aex
    D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeConsumer.aex
    D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeHostMock.exe

Only the two .aex files would be installed in a **separate, disposable test AE environment**. Do not replace the existing installed ShapeLayerAE v3, and do not experiment on a production project. Host integration is **pending**, including AEGP load-order, suite lifecycle, EffectMain About reporting, per-frame geometry and MFR/dependency safety.

**Actual AE2026 observation (user screenshots, 2026-10-11):** applying Consumer to a solid displayed `PICA suite: connected`, `Native Bezier segments: 4; first X: 100.00`. The original Consumer AEX also displayed version mismatch (code 1.0 / PiPL 0.2), global flags mismatch (0x400 / 0x0), and a performance/MFR warning; these were *nonfatal metadata declarations*, not a vector handoff failure. The updated build fixes PiPL `REVe=524289`, `OLGe=0`, `2LGe=134217728`, and C++ flags match. `verify_pipl_metadata.py` parses these values from the compiled `.aex` PiPL resource. It also passes the independent mock cross-DLL test at frame 0 and t=.5 seconds. **The fixed AEX still needs a real AE host retest** after closing AE and replacing the Consumer; do not hot replace loaded plugins. The suite's geometry is procedurally constructed from requested time, not per-user instance data; v1 is a transport/ABI proof, not a completed dynamic node system. The consumer's PF_World copy remains a passthrough, not AE-native vector output.

## Critical engineering gaps

1. Module and suite lifetime, AEGP registration/release, service ownership, suite availability if plugin load order differs.
2. Producer/effect instance IDs and native frame/subframe time semantics, coordinate transforms and shape group hierarchy.
3. Immutable geometry snapshots across render threads, allocator rules and error handling; no mutable shared pointers across plugin boundaries.
4. AE-native dependency graph, change invalidation and deterministic render evaluation. PICA call != host RenderGraph dependency.
5. Native Timeline/Path tool/VectorArt ownership. The Adobe BEE/TDB private registries remain a separate research track.

No user-visible claim of an effect that itself owns native AE Shape Contents is made. This lab gives a **technically plausible independent vector data protocol** for multiple cooperating CompNodeAE or third-party effects, pending real-host observation.


## 2026-10-12 — Actually generated a non-raster vector artwork from the AEGP

VectorBridgeToSVG.cpp is now a separate x64 program that calls the **actual compiled VectorBridgeAEGP.aex** through a minimal public PICA service stub, then requests its native double-precision four-cubic Bézier geometry at a rational time. It transforms the returned numerical cubic control points, creates **28 editable path elements / 112 cubic Bezier segments**, and serializes a 1024x1024 SVG with only <path> elements (no image nodes or bitmaps).

Build, then execute in PowerShell (quoting shown):

    & 'D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeToSVG.exe' 'D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeAEGP.aex' 'D:\Developer\ShapeLayerAE\results\CNL_Vector_Rosette_28.svg' 12 24 1 28

Arguments: provider AEX, SVG output path, time numerator, time denominator, shape kind (0=circle; 1=ellipse), repeat count (1..256).

To validate both the generated SVG and time-dependent geometry:

    python 'D:\Developer\ShapeLayerAE\labs\vector_bridge\verify_svg_vector_art.py'

Validation succeeded on two separate frame times: exactly 28 unique editable paths and 112 cubic commands, no image/foreignObject/raster elements, all finite in bounds, hash differs by time. JSON receipt in AEIG datasets/ae-pica-vector-svg-rosette-geometry-validation-2026.json.

The test SVG is available at:

    D:\Developer\ShapeLayerAE\results\CNL_Vector_Rosette_28.svg

This is an executable **code → cubic vector data → procedural instancing → vector-only SVG** flow and a possible starting point for an explicit **Bake To Native Shape** operation through AE2026 SVG import. The AE import of this exact SVG has **not yet been executed**; path/group/stroke roundtrip fidelity remains a user experiment. The SVG file is NOT a native Effect-owned Contents tree or host VectorArt return value.

Important: Keep running AE untouched. This program is a standalone native PICA client; it does not install a new AEX or execute private BEE/TDB entrypoints.
