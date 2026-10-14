---
status: supported-sdk-guide-companion
last_verified: 2026-10-14
evidence: E0-H + E0-G + E2-X
versions: Installed Adobe SDK25.6 AEGP_KeyframeSuite5; older suite versions are distinct
---

# AEGP_KeyframeSuite5 — Native Keyframe Editing

`AEGP_KeyframeSuite5` is the **supported public suite for authored keyframes** on eligible AE Streams. It is separate from the property Stream Suite and the host's private TDB/BEE animation classes.

Official Guide: [AEGP Suites — Working With Keyframes](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#working-with-keyframes). Installed SDK contract: `AE_GeneralPlug.h` after the Dynamic Stream Suite definition (around line 1797).

## Suite declarations

| Declaration | Installed SDK25.6 |
| --- | --- |
| C suite type | `AEGP_KeyframeSuite5` |
| Suite name macro | `kAEGPKeyframeSuite` = `"AEGP Keyframe Suite"` |
| Version constant | `kAEGPKeyframeSuiteVersion5` = **5**, frozen in 22.5 |
| Key index type | `AEGP_KeyframeIndex` (`A_long`) |
| Special result | `AEGP_NumKF_NO_DATA = -1` |

Use the exact suite version declared by the SDK you compile against. In AE SDK25.6 the current distributed type is **Suite5**, not a hypothetical `AEGP_KeyframeSuite5`.

## Query keyframe and dimensionality state

| Function | Parameters | Effect |
| --- | --- | --- |
| `AEGP_GetStreamNumKFs` | `streamH, num_kfsPL` | Authored keyframe count or `AEGP_NumKF_NO_DATA` |
| `AEGP_GetKeyframeTime` | `streamH, key_index, time_mode, timePT` | Time coordinate |
| `AEGP_GetNewKeyframeValue` | `plugin_id, streamH, key_index, valueP` | Native exposed keyframe value |
| `AEGP_GetStreamValueDimensionality` | `streamH, value_dimPS` | Value component count |
| `AEGP_GetStreamTemporalDimensionality` | `streamH, temporal_dimPS` | Temporal ease dimensions |

`AEGP_GetNewKeyframeValue` returns an `AEGP_StreamValue2` which must be disposed through the **Stream Suite's `AEGP_DisposeStreamValue`**. Some native `NO_DATA` types cannot return a normal StreamValue, even when they participate in internal keyframe or editor processes.

The header explicitly warns that zero keyframes may still correspond to a varying expression. Inspect `AEGP_IsStreamTimevarying` separately.

## Insert, delete and update

```cpp
// Exact API parameter order from SDK25.6, adapted for clarity.
A_Err (*AEGP_InsertKeyframe)(
    AEGP_StreamRefH streamH,
    AEGP_LTimeMode time_mode,
    const A_Time* timePT,
    AEGP_KeyframeIndex* key_indexP);

A_Err (*AEGP_SetKeyframeValue)(
    AEGP_StreamRefH streamH,
    AEGP_KeyframeIndex key_index,
    const AEGP_StreamValue2* valueP);
```

`AEGP_InsertKeyframe`, `AEGP_DeleteKeyframe` and `AEGP_SetKeyframeValue` are documented **UNDOABLE**. Inserting at a time with an existing keyframe leaves the stream unchanged. `SetKeyframeValue` does **not adopt** the passed input value.

A StreamRef may be invalidated by mutation in some contexts; avoid caching references across topology changes. Use the suite's exact const/mutable API declaration where relevant rather than assuming that all keyframe operations have identical ref lifetime behavior.

## Spatial and temporal interpolation

| Function family | What it controls |
| --- | --- |
| `AEGP_GetNewKeyframeSpatialTangents` / `AEGP_SetKeyframeSpatialTangents` | Spatial in/out tangents and their values |
| `AEGP_GetKeyframeTemporalEase` / `AEGP_SetKeyframeTemporalEase` | Temporal ease per temporal dimension |
| `AEGP_GetKeyframeInterpolation` / `AEGP_SetKeyframeInterpolation` | Temporal interpolation mode |
| `AEGP_GetKeyframeFlags` / `AEGP_SetKeyframeFlag` | Temporal/Spatial Continuous, AutoBezier, Roving and related flags |
| `AEGP_GetKeyframeLabelColorIndex` / `AEGP_SetKeyframeLabelColorIndex` | Keyframe label colors; Suite5 addition |

Do not mix **value dimensionality** with **temporal dimensionality**. For a separated-dimensions leader, index-based keyframe operations may require retrieving the follower streams through `AEGP_DynamicStreamSuite4` before editing.

## Batched keyframe authoring

The SDK exposes a batch API:

```text
AEGP_StartAddKeyframes(streamH, &infoH)
 → AEGP_AddKeyframes(infoH, time_mode, timePT, &index)
 → AEGP_SetAddKeyframe(infoH, index, &value)
 → ...
 → AEGP_EndAddKeyframes(addB, infoH)
```

The final operation is undoable. Treat the returned `AEGP_AddKeyframesInfoH` as an API-managed transaction handle and follow documented completion/cancel rules; do not assume ordinary keyframe setter semantics apply to an unfinished batch.

## Host-native Paint Path caveat

An actual AE2026 Paint Path reports `AEGP_StreamType_NO_DATA` through public StreamSuite6. The corresponding keyframe count was **intentionally not queried** in the v2 read-only inspector, because specialized internal values are not ordinary `AEGP_StreamValue2` data. It would be incorrect to report this fixture as having a newly validated editable generic Paint Path keyframe API.

A foreign registered property type would also need native animation, interpolation, Undo and serialization outside the scope of the public suite. See [Native Property Operations](../../../state-model/native-property-system/property-operations.md).

## Related

[StreamSuite6](stream-suite.md), [DynamicStreamSuite4](dynamic-stream-suite.md), [AEIG animation/keyframe semantics](../../../animation-system/keyframe-api-history.md) and [Adobe official AEGP keyframes](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#working-with-keyframes).
