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

## 2026-10-11 — v3 research commands (build-only until manually tested)

The latest `build/Release/ShapeLayerAE.aex` has **three** Animation menu commands:

1. `ShapeLayerAE: Dump Stream Tree` — existing public, read-only tree/metadata/capability capture, now adds two independent UID calls with different nonzero sentinels (`uid_second_call`, `second_uid_error`) to investigate 359 all-zero IDs in the AE2026 v2 host capture.
2. `ShapeLayerAE: Probe Unknown Shape Names (Experimental)` — explicitly opt-in. Calls **only** `AEGP_CanAddStream` for invented Shape/Graphic/Filter-prefixed names on existing Indexed Groups; `%TEMP%/ShapeLayerAE_canadd_unknown.tsv`. **Never calls AddStream** for a made-up type. This tests whether native vector Contents admission operates on known type IDs vs prefix grammar, not whether a stream can be constructed.
3. `ShapeLayerAE: Probe Private TDB Getter (Read Only)` — explicitly opt-in **unsupported private ABI**. Uses GetModuleHandle/GetProcAddress and verifies the AE2025/2026 code fingerprint of `Get_AE_StreamFactory()` before making a single no-argument read-only call. Records only four booleans at `%TEMP%/ShapeLayerAE_private_factory_probe.tsv`. It neither dereferences the returned pointer nor registers, creates, modifies or deletes any native stream. This is a research-only experimental command that may be unsafe or incompatible in other builds; run only in disposable AE sessions with no unsaved work.

**Important:** AE is currently running with the older installed v2 AEX in MediaCore. The v3 build has NOT been deployed or tested in host; do not replace an in-use loaded plug-in. Close AE normally, back up any project first, replace with the newly built AEX, restart, and only then invoke an experimental menu item if willing to test unsupported ABI. Archive all generated TSVs with precise AE/TDB build hashes.

The major new nonpublic finding is the host-internal TDB stream registration machinery: BEE_Layer::RegisterStreams -> Get_AE_StreamFactory -> TDB_ScRegisterStreams::Register -> TDB_StreamFactory::RegisterFactoryFunc -> CreateStream/Canonical handling. This is **not** a supported third-party registration API. See AEIG `docs/vector-shape-system/native-stream-factory-and-schema.md` and `research/findings/F-VECTOR-008-tdb-native-factory-registration.md`.

## 2026-10-11 evening: confirmed v3 host results

v3 **was installed and executed in AE2026**. The experimental no-argument private TDB getter returned a non-null pointer with all four guard statuses true. Its pointer was **never dereferenced** and no private registration/mutation method was called. The separate unknown name CanAdd test accepted unregistered `ADBE Vector Shape - ...`, `Graphic - ...`, and `Filter - ...` names in native Shape Contents, not elsewhere; **CanAdd is not Create**. All 359 public unique stream IDs returned zero on both sentinel-initialized queries with error code zero (cause unresolved). Original TSVs, hashes, and reproducible observations are in AEIG `experiments/vector-shape/EXP-SHAPE-009-010-v3-host-confirmation.md`.

The offline internal type registration study separately established native vector `Create` function references and TDB `Register` CALLs for actual Adobe implementations in both 2025 and 2026. This does NOT yet create any CompNodeAE-owned native vector tree or effect-owned geometry result. The active installed binary and Release build retain SHA-256 `6a20aaa59100a68aaa5e8aa4af126756a9dd8dd6cf50951dce8cf1bf6ec6dbf1`; no replacement required for these completed v3 results.

## 2026-10-11 second native evaluator registry forensic breakthrough

Offline AE2025/AE2026 binary comparisons prove that built-in native vector kinds are dispatched through **two separate registries**, neither exposed as a supported Effect SDK extension:

- **TDB StreamFactory**: matchname-to-creator registration. `RegisterFactoryFunc` eagerly invokes `CreateStream` and may set up canonical/separated dimensions while the host registration is in progress. Creator stubs and unknown-object pointers are NOT safe to test.
- **BEE evaluator registry**: distinct MatchName-to-polymorphic-operator mapping; 20 native names and concrete `BEE_VectorStream::*Operator` RTTI classes in both versions. Both normal `PopulateVectorArt` and `BEE_VectorArt::StreamBasedFilter::DoFilter` use its lookup and virtual evaluation slot, with distinct mode arguments. The registry's initialization, duplicate detection and destruction are accounted for in the static evidence.

Research source scripts live under `tools/` and are snapshotted source-only into AEIG `experiments/vector-shape/probe-src/tools`. The new AEIG page is `docs/vector-shape-system/native-vector-evaluator-registry.md`. Findings `F-VECTOR-013` and `F-VECTOR-014`, Hypothesis `H-SHAPE-006`, and experiments `EXP-SHAPE-013/014` contain reproducible data.

**No new AEX was deployed or changed**. The active v3 `ShapeLayerAE.aex` remains unchanged. No private registration, host memory patching, or native Shape-layer/project mutation was performed. Built-in type registration is not evidence that CompNodeAE can already emit native host-owned vector geometry.
