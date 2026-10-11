---
status: source-index
last_verified: 2026-10-11
---
# Shape-stream identity / native selection bibliography and local artifact index

| Ref | Grade | Observation | Limitation |
| --- | --- | --- | --- |
| S-SHAPE-11 | E0-H | Local SDK25.6 `AE_GeneralPlug.h`: `new Dynamic Streams API for AE6`; dynamic stream suite frozen AE9.0; `StreamSuite6::GetUniqueStreamID` added AE22.5 | Date annotations describe an SDK-era API, not native 2007 Shape object factory availability |
| S-SHAPE-12 | E0-G | https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/ : UniqueStreamID is **session-unique**, as of AE22.5 | Not project-persistent by documented guarantee; no known TDB mapping |
| S-SHAPE-13 | E0-G | https://adobedocs.github.io/after-effects-feature-history/ : AE CS3 8.0 Shape Layers introduced July 2, 2007 | Does not locate internal factory or plugin callback |
| S-SHAPE-14 | E1-A | https://www.provideocoalition.com/shape_layers/ (May 2007 introduction) | End-user shape model not SDK or native ABI |
| S-SHAPE-15 | E2-X | `experiments/vector-shape/runs/EXP-SHAPE-001/20261011-first-success/shape_layer_stream_tree.tsv`, SHA-256 `54061903cac3bae95215b723f2c513a7cbb20b1352f61c8829699090604a240f` | One selected Shape Layer / E2-X public projection |
| S-SHAPE-16 | E2-L | `datasets/ae-vector-origin-identity-2025-2026.json` | Static decorated names |
| S-SHAPE-17 | E2-L | `datasets/ae-vector-selection-origin-xrefs-2025-2026.json` | Direct references only; virtual/indirect targets excluded |
| S-SHAPE-18 | E2-L | `datasets/ae-vector-layer-construction-2025-2026.json` | Bounded x64 disassembly; exact ABI lifecycle unverified |
| S-SHAPE-19 | E0-H | Local SDK25.6 `AE_GeneralPlug.h` + `F-ABI-011`: distributed `AEGP_INTERNAL` / non-distributed `AE_GeneralPlug_Private.h` | Built-in private declarations are **not** permission or safe ABI for a plugin |
