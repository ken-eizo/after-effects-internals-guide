---
status: compiled-not-host-tested
last_verified: 2026-10-11
evidence: E0-H + build artifact; no E2-X on v2
versions: Windows x64 / SDK 25.6 / target AE2026
---

# EXP-SHAPE-005 — Read-only identity/capability probe build receipt

**Source:** `D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp`

**Output:** `D:\Developer\ShapeLayerAE\build\Release\ShapeLayerAE.aex`

**SHA-256:** `86620A4592331CF484CD30472C3F40EFB3E2FDB86ABD34B28A5D9C1E708A5599`

CMake/MSVC Release x64 succeeded using Adobe SDK 25.6. The only warnings observed were existing MSB8029 intermediate-directory warnings. No new fatal compiler/linker error occurred.

### Read-only additions

- `AEGP_StreamSuite6::AEGP_GetUniqueStreamID`: session-unique numeric stream identity; never equate with persistent `TDB_StreamIDPath`.
- `AEGP_GetStreamDepth`, `AEGP_GetDynamicStreamFlags`, `AEGP_GetStreamIsModified`; record API errors.
- `AEGP_GetStreamType` **LEAF only**.
- `AEGP_CanAddStream` **INDEXED_GROUP only**, against six known native match names; never invoke `AEGP_AddStream`, `AEGP_DeleteStream`, `AEGP_ReorderStream` or `AEGP_SetStreamValue`.
- Writes `%TEMP%\ShapeLayerAE_stream_metadata.tsv` and `%TEMP%\ShapeLayerAE_canadd.tsv` in addition to the original stream-tree TSV.

Build-only status. The current AE 2026 running process was deliberately not restarted or hot-patched. Installed AEX is still earlier v1 unless manually replaced with AE closed. No host successful v2 result can be claimed. Refer to `EXP-SHAPE-005-native-stream-identity-capability-probe.md`.

Source code and verification tools are also snapshotted to `experiments/vector-shape/probe-src` without copying Adobe headers, SDK executables or AE DLLs.
