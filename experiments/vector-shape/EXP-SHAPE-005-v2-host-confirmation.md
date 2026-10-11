---
status: observed-in-host
last_verified: 2026-10-11
evidence: E2-X + E0-H
versions: AE2026, distributed SDK25.6
---
# EXP-SHAPE-005 — Second user-executed read-only stream probe, real host results

The user reinstalled ShapeLayerAE v2 and executed its Animation menu command in the live AE 2026 host (observed PID and plugin hash match). The actual three fresh TSV files were captured from the user's authorized remote Windows TEMP, with the original bytes preserved under `runs/EXP-SHAPE-005/20261011-user-host-v2/`. This report is about a **real executed host experiment**, not a screenshot-only status.

| File | Rows | SHA-256 |
| --- | ---: | --- |
| `ShapeLayerAE_stream_tree.tsv` | 359 | `38243e05de1d447d8b71104c4d73f4ddd01d778b627d6abceaf14db0ff9b5432` |
| `ShapeLayerAE_stream_metadata.tsv` | 359 | `ba1e318ca21c8a893933b14517a92be46b0ae45c65373cea5089495b7a56767d` |
| `ShapeLayerAE_canadd.tsv` | 36 | `8b51d257014bebcfdc9a7ee1ae348d43d863e408244b6bf026d584c61a40fba0` |

- All 359 stream metadata calls had recorded zero AEGP error, SDK stream depths matched recursive traversal depths.
- All 36 CanAdd queries returned error 0, and Shape Contents accepted built-in native Vector Path/Graphic candidate match names while Effect Parade rejected them and accepted Slider Control.
- Session UID query returned output 0 on every stream with API error 0. This is a notable **version/fixture-specific anomaly**, not yet a general API bug. Sentinel-based control in the next compiled probe is pending.
- The selected object included nested Shapes, actual Path, Stroke, Fill, Materials and ordinary Effects; this is a higher-complexity native Shape fixture than EXP-SHAPE-001.

Source capture used a separate archival script and no native host mutation. `analysis.json` records SHA-256, rows, group flags and full admissibility matrix; no external inferred data substituted for logs.

The code only introspected **existing** TDB/AEGP streams. No custom native type or independent shape owner has been created. Therefore E2-X confirms the native group surface/admission contract only.

Falsification follow-ups: use fresh empty Shape Layer and ordinary layer, then unknown prefixed strings (without adding); repeat UID with two nonzero sentinels and isolate whether host updates output or writes literal 0.
