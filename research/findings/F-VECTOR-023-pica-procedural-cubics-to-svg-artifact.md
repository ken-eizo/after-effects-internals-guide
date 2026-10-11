---
status: confirmed-standalone-binary
last_verified: 2026-10-12
evidence: E2-T + E2-X (prior actual AE PICA connection)
versions: installed SDK 25.6, x64 Windows compiled AEX
---
# F-VECTOR-023 — Executable PICA Geometry Producer → 112 authored SVG Bézier segments, no raster stage

## Real compiled pipeline

New original program D:/Developer/ShapeLayerAE/labs/vector_bridge/VectorBridgeToSVG.cpp loads the independently built real VectorBridgeAEGP.aex module with LoadLibrary, invokes its exported AEGP EntryPointFunc in a **standalone mock SPBasic/PICA transport**, acquires the registered versioned CNL_VectorBridgeSuite1, calls DescribePath, then CopyCubicPath at a requested rational time.

The returned **four cubic Bezier segments** are directly used for procedural geometry operations: affine rotate/scale/translate in C++ to create 28 separate paths; each path consists of exactly four cubic segments and supports line/fill style at SVG output. The program explicitly creates XML SVG path records rather than a pixel image or intermediate PF_World.

Built with CMake/Visual Studio 2022, no changes to user-installed running After Effects or existing VectorBridge AEX binaries. Live demo output:

- D:/Developer/ShapeLayerAE/results/CNL_Vector_Rosette_28.svg
- D:/Developer/ShapeLayerAE/results/CNL_Vector_Rosette_28_t0.svg
- 28 unique SVG path IDs; 4 exact cubic C commands per path; **112 total cubic segments**; each path has M/C/Z structure.
- No SVG image elements, foreignObject, bitmap payload, Canvas API or raster input.
- Two deterministic samples at time 0/24 and 12/24 have distinct valid finite geometry coordinates. The verifier runs the real compiled provider AEX at both times, and confirms SHA256 hashes differ.

Machine-readable receipt: datasets/ae-pica-vector-svg-rosette-geometry-validation-2026.json. C++ source + verifier + one user-owned generated SVG sample are preserved under experiments/vector-shape/vector-bridge-lab/ in AEIG. No Adobe executable/library binary is checked into AEIG.

## Product possibility unlocked

**A native-procedural vector coding toolchain with interoperable outputs**: an independent plugin can publish time-varying double-precision cubic curves, and a different consumer can apply geometry transforms and generate editable vector artwork. Examples: particle/motion-path outlines without thresholded raster images; instanced floral motifs; parametric title ornaments; mathematically generated paths; rule-based typography and logo animation shapes. Extensible to Shape operators as immutable geometry snapshots, driven by CompNodeAE node program.

**Important qualification:** AEGP→Effect PICA numeric geometry handoff succeeded in actual AE2026 in prior F-VECTOR-020. This new ToSVG program is **a separate standalone executable**, not a live in-AE effect-to-native-renderer interface. Importing the generated SVG as a standard AE Shape Layer is a **bake/conversion workflow** and its exact fidelity still requires a user AE import round trip test. Native plugin-owned Timeline Contents and BEE_VectorArt output are unproven and must not be described as achieved.

## Known next engineering gates

- Expose *per-effect-instance* geometry, not global procedure sample, with explicit identity, versioned snapshots, time, coordinate-space and deterministic evaluation.
- Enforce correct AE MFR/render dependencies and cache invalidation across effects. PICA alone is not a render dependency.
- Geometry operator results must preserve topology, winding, holes, fill rules, variable-width stroke semantics and animation keys.
- Test native SVG import (AE2026), compare imported native paths and group count to original SVG, round trip points and styles.
- Separately continue F-VECTOR-021/022 research for truly effect-owned host-native indexed Contents/AGM path.

## Reproducibility

Run under the authorized developer PC:
  cmake --build D:/Developer/ShapeLayerAE/build/vector_bridge --config Release
  python D:/Developer/ShapeLayerAE/labs/vector_bridge/verify_svg_vector_art.py

The verifier executes the compiled C++ consumer/provider and validates the resulting SVGs with Python xml.etree.ElementTree; neither test launches Adobe After Effects.
