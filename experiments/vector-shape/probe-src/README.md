# ShapeLayerAE — native shape system research probe

**Purpose:** Experimental companion to AEIG's `vector-shape-system/native-extensibility-boundaries.md`. It is intentionally separate from `CompNodeAE` and does not modify an AE project on first use.

## Research success criterion

Our target is **independent** registration/ownership of AE-native mutable Contents, native Pen/Selection tool editing, and feeding geometry to AE's **production** vector renderer. Reading an existing Shape Layer, faking a Timeline by parameter topics, drawing Drawbot handles or returning raster pixels is **not** a successful native replacement.

## Current probe: EXP-SHAPE-001

This plugin is **read-only**. It adds **Animation > ShapeLayerAE: Dump Stream Tree**. Select a layer and invoke the command. A TSV is written to `%TEMP%\ShapeLayerAE_stream_tree.tsv` with the AEGP stream grouping, child index, match name, display name and error codes. Selecting another layer overwrites the TSV; copy the results to separately named capture files before the next test. It uses **only public AEGP suites** and does not attempt private BEE/TDB calls.

For comparisons, first dump a native Shape Layer with a nested Group/Path/Fill/Stroke/Repeater, then dump a normal layer containing an effect with grouped parameters. Record AE build/version. This is evidence of the **public tree projection**, not proof of the host's internal creation/registration scheme.

## Build (Windows x64, SDK 25.6)

Prerequisites: locally installed Adobe AE SDK 25.6 Examples, Visual Studio C++ / Windows SDK, CMake, Python 3, and SDK PiPLtool. SDK is referenced on the local device and not copied into this project.

```powershell
cd D:\Developer\ShapeLayerAE
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DAE_SDK_EXAMPLES="E:/ae25.6_61.64bit.AfterEffectsSDK/Examples"
cmake --build build --config Release
```

Output: `build/Release/ShapeLayerAE.aex`. Deploy manually to AE's Plug-ins directory only while AE is closed, preferably in a disposable test environment, then restart AE. No automatic deployment to application folders occurs.

## Static audit: EXP-SHAPE-003

Run `python tools/audit_symbols.py` to produce `results/static_symbol_audit.json`. This reads the AEIG export inventory. For bounded *offline* disassembly of locally installed AE 2025 `BEE.dll`, run `python tools/audit_bee_disasm.py` (requires local `pefile` and `capstone`); it produces `results/bee_private_surface_probe.json`. Both results are archived with SHA-256 and E2-L interpretation under `AEIG/experiments/vector-shape/runs/EXP-SHAPE-003/`. The tools **never execute, patch, load into a process or call** AE private symbols.

## Evidence discipline

- E0-G/H/S: supported public contract, headers and Adobe samples.
- E2-L: executable/module export/import or distribution artifact; **not a supported ABI**.
- E2-X: only after a real, reproducible AE host run with logs/version/hashes.
- H: explicit unconfirmed prediction with falsification test.

**2026-10-11 correction:** The first installed AEX is unsafe for recursive traversal: it calls `AEGP_GetNumStreamsInGroup` on LEAF and triggered a user-reported `{GetNumStreamsInGroup only works on groups}` assertion. This is fixed in the current built output (SHA-256 `E572BA538E5DAE6889F789AA6090BEDA61EF713731BBEC198894604B7394B272`). The older AEX in `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\ShapeLayerAE.aex` has the former SHA-256 (`8764F5...`); **quit AE before replacing it**, restart AE and rerun. The source/repair and evidence are recorded in AEIG `experiments/vector-shape/EXP-SHAPE-001-host-failure.md`.

No post-repair AE-host run, native factory registration or built-in rasterizer redirection has been verified yet.

## 2026-10-11 — Read-only identity + CanAdd probe (v2)

The current **built but not installed/tested in-host** binary extends the original `Animation > ShapeLayerAE: Dump Stream Tree` command and writes three outputs to `%TEMP%`:

- `ShapeLayerAE_stream_tree.tsv` — original public tree projection.
- `ShapeLayerAE_stream_metadata.tsv` — per-node public `AEGP_GetUniqueStreamID` (available from AE 22.5; **session-unique only**), SDK depth, dynamic flags, change status, LEAF type and error columns.
- `ShapeLayerAE_canadd.tsv` — `AEGP_CanAddStream` on **indexed groups only**, against known Adobe-native Vector/Fill/Stroke/Slider Control match names; **does not add anything**.

For repeated trials, copy each TSV to a named capture file before running the command again: each run overwrites the three `%TEMP%` output files. Compare in-session UIDs across native child reordering and Undo; do not equate these UIDs with private `TDB_StreamIDPath` or assume persistence after restart.

**Deployment:** The user has AE 2026 running. Do not overwrite the currently loaded `C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\ShapeLayerAE.aex` while AE is running. Exit AE normally, replace that AEX with `D:\Developer\ShapeLayerAE\build\Release\ShapeLayerAE.aex` (admin permission may be necessary), then restart AE and use the Animation menu command. Preserve your existing project separately for testing. Build success is not host runtime verification.

Supporting source-only snapshot and experiment records are in AEIG `experiments/vector-shape/probe-src/` and `experiments/vector-shape/EXP-SHAPE-005-native-stream-identity-capability-probe.md`.
