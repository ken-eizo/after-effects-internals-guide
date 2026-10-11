---
status: pass-standalone
last_verified: 2026-10-12
evidence: E2-T
versions: Windows x64 CMake VS2022, Adobe SDK25.6 native AEX provider
---
# EXP-SHAPE-021 — Use actual AEGP procedural cubic data for a 28-path vector-only pattern

## Success criterion

Obtain four native numeric cubic Beziers from the **actual compiled AEX** and produce a time-varying, purely vector, externally consumable artifact without PF_World pixels or manually authored source paths.

## Procedure and result

CMake builds VectorBridgeToSVG.exe from a standalone original C++ PICA client. It dynamically loads the compiled AEGP, registers/obtains its PICA geometry suite under a minimal fake host, copies four native cubic segments, transforms the cubics into 28 procedural path instances, and writes the final SVG. The generated sample contains exactly 112 SVG cubic C commands with 28 unique path IDs. XML validation, finite coordinate validation, no bitmap/image node assertions and a two-timepoint geometry-change check PASSED.

Files on host:
- D:/Developer/ShapeLayerAE/results/CNL_Vector_Rosette_28.svg (at t=0.5sec)
- D:/Developer/ShapeLayerAE/results/CNL_Vector_Rosette_28_t0.svg (at t=0sec)
- D:/Developer/ShapeLayerAE/labs/vector_bridge/VectorBridgeToSVG.cpp
- D:/Developer/ShapeLayerAE/labs/vector_bridge/verify_svg_vector_art.py

Reproducibility and SHA256 in datasets/ae-pica-vector-svg-rosette-geometry-validation-2026.json.

## Product conclusion

This is a functioning code-to-vector export pipeline. Independent CompNodeAE-aware consumers could provide path instancing, procedural ornament, geometry warping and vector file output. AE2026 SVG import may then explicitly bake the result into standard editable Shape Contents, pending user host test. It is NOT a native effect-owned vector render output. The public PICA Suite is a transport; a separate native host-provider/owner mechanism is still required.
