---
status: compiled-not-host-tested
last_verified: 2026-10-11
evidence: E0-H + E0-G + E2-L; host E2-X pending
versions: SDK25.6, target AE2026
---
# EXP-SHAPE-005 — Session UID, native stream flags and child-type admissibility

The updated **read-only** `ShapeLayerAE` probe was compiled with SDK25.6/Visual Studio 2022. It adds two files in `%TEMP%` alongside the existing `ShapeLayerAE_stream_tree.tsv`: `ShapeLayerAE_stream_metadata.tsv`, and `ShapeLayerAE_canadd.tsv`. It does not add, delete, rename, reorder or animate any host stream.

For each visited stream the observer records `AEGP_GetUniqueStreamID`, `AEGP_GetStreamDepth`, `AEGP_GetDynamicStreamFlags`, `AEGP_GetStreamIsModified`, and on LEAF only `AEGP_GetStreamType`, capturing individual API error numbers. On **INDEXED_GROUP** only it invokes `AEGP_CanAddStream` with six predefined, known Adobe match names (Vector Group, Path Group, Rectangle, Fill, Stroke, Slider Control), recording allowed/error without actually adding them.

**Precautions:** GetNumStreamsInGroup must never be called on LEAF. `AEGP_GetUniqueStreamID` is supported in StreamSuite6 on AE22.5+, and is **session-unique**, not promised project-persistent. Refs remain scoped to the current traversal. A CanAdd result is a capability oracle for existing host groups and known types; it is NOT proof a plug-in can register novel native factory types.

Host test pending: replace the installed AEX only after quitting AE, restart, run on four controlled layer fixtures, archive all three TSV outputs and host info, then compare per-node UIDs across in-session native reorder/Undo/selection. Independently confirm every error field and no AE alerts. The current source is `D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp`; source snapshot is in `experiments/vector-shape/probe-src`. Neither an AEX build nor a source snapshot counts as an E2-X host test.
