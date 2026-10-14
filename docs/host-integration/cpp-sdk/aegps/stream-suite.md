---
status: supported-sdk-guide-companion
last_verified: 2026-10-14
evidence: E0-H + E2-X + E2-L
versions: SDK25.6 AEGP_StreamSuite6; online Guide may cover newer versions
---

# AEGP_StreamSuite6 — Stream References, Values and Expressions

The public `AEGP_StreamSuite6` acquires and inspects host-owned property values. It is not the native C++ factory registration service. The native TDB/BEE model behind these references is described in the [AEIG Stream Object Model](../../../state-model/native-property-system/stream-object-model.md).

Official API page: [AEGP Suites — Stream Suite](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#stream-suite). Primary installed contract: `Examples/Headers/AE_GeneralPlug.h`, lines 1456–1585.

## Availability and version constants

| Definition | Value in SDK25.6 |
| --- | --- |
| C suite type | `AEGP_StreamSuite6` |
| `kAEGPStreamSuite` | `"AEGP Stream Suite"` |
| `kAEGPStreamSuiteVersion6` | `11`; frozen in AE 22.5, per distributed header |

Always acquire the API suite using its declared PICA suite name and version constant. The suffix 6 on `StreamSuite6` is **not** the numeric PICA acquisition version.

## Acquiring and disposing StreamRefH

`AEGP_GetNewLayerStream`, `AEGP_GetNewEffectStreamByIndex` and `AEGP_GetNewMaskStream` create access references to existing host-owned streams. Every returned reference is marked **must be disposed by caller**.

`AEGP_DisposeStream(streamH)` releases that public reference. It does **not** destroy the underlying native property or unregister a native C++ class.

| API | Acquires from | Preconditions |
| --- | --- | --- |
| `AEGP_GetNewLayerStream` | `AEGP_LayerH`, `AEGP_LayerStream` enum | Legal built-in layer stream |
| `AEGP_GetNewEffectStreamByIndex` | `AEGP_EffectRefH`, `PF_ParamIndex` | Index in existing Effect param list |
| `AEGP_GetNewMaskStream` | `AEGP_MaskRefH`, `AEGP_MaskStream` enum | Existing Mask |
| `AEGP_DuplicateStreamRef` | Existing `AEGP_StreamRefH` | Creates another disposable reference |
| `AEGP_DisposeStream` | Previously acquired `AEGP_StreamRefH` | Release promptly; do not reuse afterward |

Structural mutations may invalidate references independently of ordinary disposal. Holding a stream ref across dynamic index modification is unsafe; reacquire using supported owner/path metadata.

## Value typing and type-specific access

`AEGP_GetStreamType(streamH, &type)` returns an `AEGP_StreamType`. For eligible leaf streams, `AEGP_GetNewStreamValue(pluginID, streamH, time_mode, timePT, pre_expressionB, &value)` evaluates an `AEGP_StreamValue2`.

```cpp
// API excerpt, adapted from installed AE_GeneralPlug.h.
// Actual suite invocation requires a valid host plugin ID and acquired StreamRefH.
A_Err (*AEGP_GetNewStreamValue)(
    AEGP_PluginID plugin_id,
    AEGP_StreamRefH streamH,
    AEGP_LTimeMode time_mode,
    const A_Time* timePT,
    A_Boolean pre_expressionB,
    AEGP_StreamValue2* valueP);
```

The returned value must be released via **`AEGP_DisposeStreamValue`**. It is not correct to free the union's backing memory directly. Other read helpers such as `AEGP_GetLayerStreamValue` have a restricted set of supported primitive types.

### NO_DATA is not the absence of a native value

In an actual AE2026 Brush-created Paint effect, the native `ADBE Paint Shape` (Path) leaf returned `AEGP_StreamType_NO_DATA`. The user can still edit the Adobe-native path using internal Paint tools. A third-party StreamSuite client must **not** assume an ordinary `AEGP_StreamValue2` accessor exists for that specialized native type (E2-X F-VECTOR-087).

## Animation state and expression evaluation

| API | What it answers |
| --- | --- |
| `AEGP_CanVaryOverTime` | Does this property class support temporal variation? |
| `AEGP_IsStreamTimevarying` | Is this effective property state time-varying now? Header says **includes expressions** |
| `AEGP_GetValidInterpolations` | What interpolation types are legal here? |
| `AEGP_GetExpressionState` | Is the expression effectively enabled? |
| `AEGP_GetExpression` / `AEGP_SetExpression` | Read or update expression text |
| `AEGP_SetExpressionState` | Change expression execution state |

The SDK header warns that AE may automatically disable expressions during parser/playback failures. For reliable comparisons distinguish authored expression, effective state, pre-expression value, evaluated value and render cache validity.

### AEGP_SetStreamValue restrictions

The installed header states that `AEGP_SetStreamValue` is legal when `AEGP_GetStreamNumKFs == 0` or for `NO_DATA`, with special type-specific restrictions. This is **not** a guarantee that an arbitrary `NO_DATA` Paint path accepts a guessed `AEGP_StreamValue2` payload. Respect the stream's actual documented value/access interface.

## AEGP_GetUniqueStreamID

`AEGP_GetUniqueStreamID(streamH, &outID)` is the notable addition in `StreamSuite6`, frozen in AE 22.5. This numeric identifier is documented as *session unique*, not guaranteed persistent through AEP save/reopen.

One controlled native Shape AE2026 fixture obtained all-zero values for 359 queried IDs despite zero AEGP errors on two sentinel-initialized passes. This unusual observation is **fixture-limited and unexplained**; it must not be generalized to all releases or properties without further tests (F-VECTOR-009).

## Error patterns and ownership

- Do not use `GetNewStreamValue` for a `NO_DATA` stream simply because AE visually animates it.
- Dispose UTF-16 `AEGP_MemHandle` values returned by name/expression APIs with `AEGP_FreeMemHandle`, not `AEGP_DisposeStream`.
- Dispose StreamRef handles with `AEGP_DisposeStream` and StreamValue objects with `AEGP_DisposeStreamValue`.
- A `PF_ParamIndex` in an existing Effect is not a host-native C++ Stream class registration.
- Read AEGP official Guide in the same SDK version as the compiled plugin; the online Guide can document newer suites.

## Related

[DynamicStreamSuite4](dynamic-stream-suite.md), [KeyframeSuite5](keyframe-suite.md), [Property Operations](../../../state-model/native-property-system/property-operations.md), [Adobe AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/).
