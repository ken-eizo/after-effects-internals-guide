---
status: compiled-not-host-tested
last_verified: 2026-10-11
evidence: E0-H + E0-S + build artifact; no E2-X host result
versions: Windows x64; local SDK 25.6; Visual Studio 2022
---
# EXP-SHAPE-001 — Read-only Stream Tree Probe Build Receipt

## Artifact

`D:\Developer\ShapeLayerAE\build\Release\ShapeLayerAE.aex`

SHA-256: `8764f538d554bc46dd0b65a7741841ea5026cc90fed27542037d71962133555c`.

Built using CMake Visual Studio 17 2022 x64 and local Adobe SDK 25.6 headers/utility sources/PiPLTool. The build completed with exit code 0. The generated PiPL is an AEGP resource, and `dumpbin /exports` confirms `EntryPointFunc` exported. Build emitted MSB8029 warnings about intermediate/output temporary-directory placement, not compiler/linker failures.

## Probe

Adds an Animation-menu command, acquires the active layer's public AEGP root stream, recursively enumerates public child refs via `AEGP_DynamicStreamSuite2`, and records grouping type, index, match name, display name, child count, API error. It releases all acquired stream handles. No adding/deleting/renaming native streams and no use of private BEE/TDB symbols.

## Result classification

**Compiled only**. Compilation and export/PiPL presence do **not** establish host compatibility, command visibility, stream enumeration correctness, factory registration, native tool interoperability, native vector rendering, or safe operation on every layer type. AE host test and raw logs remain **pending**.

## AEIG procedure for host test

Use a disposable project and closed AE installation during deployment. Verify the plug-in loads, choose a Shape Layer then a normal layer with an effect, run the menu command and archive output `%TEMP%\ShapeLayerAE_stream_tree.tsv` under unique capture names, together with host build/version, SHA-256, failures and screenshots if necessary. Do not promote EXP-SHAPE-001 to observed without captured host output. See `experiments/observatory/manifests/EXP-SHAPE-001.json`.

## Correction build (2026-10-11)

After user-reported `GetNumStreamsInGroup` leaf assertion, ShapeLayerAE's recursion now guards **both** `AEGP_StreamGroupingType_NAMED_GROUP` and `AEGP_StreamGroupingType_INDEXED_GROUP` and never queries children from LEAF. MSVC/SDK 25.6 rebuilt `D:\Developer\ShapeLayerAE\build\Release\ShapeLayerAE.aex` successfully; SHA-256 `E572BA538E5DAE6889F789AA6090BEDA61EF713731BBEC198894604B7394B272`. The MediaCore-installed old AEX still had SHA-256 `8764F538D554BC46DD0B65A7741841EA5026CC90FED27542037D71962133555C` at last check. AE was running, so automatic replacement/restart was deliberately not performed. No post-fix AE-host test has been claimed. The corrected source and reproducibility tooling are snapshotted (without Adobe SDK binaries) to `experiments/vector-shape/probe-src/` with `SOURCE_SNAPSHOT.json` SHA-256 manifest.
