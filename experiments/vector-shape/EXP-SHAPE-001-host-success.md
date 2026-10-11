---
status: observed-in-host
last_verified: 2026-10-11
evidence: E2-X user-triggered, exact raw TSV capture + E0-H header
versions: AE 2026 installed at D:/Adobe/Adobe After Effects 2026/Support Files/AfterFX.exe; ShapeLayerAE SDK 25.6
---

# EXP-SHAPE-001 — Native Shape Layer AEGP stream topology, observed in After Effects

## Procedure and provenance

The user installed the repaired ShapeLayerAE AEGP on AE 2026, selected a Shape Layer with a Rectangle Path and Fill, then invoked `Animation > ShapeLayerAE: Dump Stream Tree`. Host displayed the confirmation `AEGP Plugin ShapeLayerAE: ShapeLayerAE: Stream tree written to TEMP\\ShapeLayerAE_stream_tree.tsv` (shown in user-supplied screenshot). The original TSV was read directly from `C:\Users\kenta\AppData\Local\Temp\ShapeLayerAE_stream_tree.tsv` at 17:46:29 local on 2026-10-11. AE process start observed at 17:44:42 local. Plugin supports only read-only traversal.

Raw file archived unmodified at `experiments/vector-shape/runs/EXP-SHAPE-001/20261011-first-success/shape_layer_stream_tree.tsv`. SHA-256 `54061903cac3bae95215b723f2c513a7cbb20b1352f61c8829699090604a240f`. Machine-generated derived summary: `.../summary.json`, with exact original path/date and parsing summary. The selected Shape Layer also contained Point Control and Color Control in its Effect Parade, and was therefore not an empty-layer control.

## Measurements

- 180 TSV stream rows; 184 physical lines including comments/header.
- 150 leaf streams (`grouping=0`), 24 named groups (`grouping=1`), six indexed groups (`grouping=2`).
- 10 direct children of the `ADBE Vector Layer` root.
- maximum AEGP tree depth 4 in the sample.
- 180 out of 180 captured per-stream final AEGP error fields were `0`; the prior invalid GetNumStreamsInGroup-on-leaf assertion was absent.
- `ADBE Root Vectors Group` identified as indexed group with two children: `ADBE Vector Shape - Rect` (named group, four children) and `ADBE Vector Graphic - Fill` (named group, five children).
- `ADBE Effect Parade` also indexed, containing `ADBE Point Control` and `ADBE Color Control` named groups. `ADBE Mask Parade` and `ADBE Layer Sets` appear as indexed groups in the root, even when empty.

## What follows — and what does not

This is **host-confirmed** that the native Shape Contents and host Effect Parade are exposed through the same AEGP recursive stream-reference **interface**. It is not proof that the corresponding internals share a type registry, allocation routine, generic custom Contents creation mechanism, or vector output contract. AEGP's object projection may normalize otherwise different host implementations.

A fresh probe is being prepared to inspect stream unique IDs, stream types and per-indexed-group `AEGP_CanAddStream` as **read-only** properties of the real host. The new probe must be compiled, manually deployed after AE is closed, and *separately* host-tested. Its build alone must not be described as a successful host experiment.

## Falsification/next controls

1. Repeat on footage/solid with effect parameters only; on empty Shape Layer; on Shape Layer containing a nested Vector Group, Path, Repeater and Transform.
2. Compare stream unique IDs before/after a native UI reordering of two Contents children, selecting path via AE Pen tool, Undo and project save/reopen. Avoid confusing transient stream refs with stable identity.
3. Compare public AEGP identities to the private `TDB_StreamIDPath`/OriginInfo only after proving an actual value mapping; string/name similarity is insufficient.
