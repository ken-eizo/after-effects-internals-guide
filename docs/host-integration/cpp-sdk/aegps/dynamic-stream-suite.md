---
status: supported-sdk-guide-companion
last_verified: 2026-10-14
evidence: E0-H + E0-S + E2-X + E2-L
versions: Adobe SDK 25.6, AEGP_DynamicStreamSuite4
---

# AEGP_DynamicStreamSuite4 — Public Dynamic Stream Operations

The **Dynamic Stream Suite** is Adobe's supported interface for navigating and manipulating host-owned property **groups and children**. The suite works with Tracker, Text, Paint, Shape and other exposed Stream groups. It does **not** register new C++ Stream classes.

Official reference: [AEGP Suites — Dynamic Streams](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#dynamic-streams). Original header: `Examples/Headers/AE_GeneralPlug.h`, lines 1590–1793 in distributed SDK25.6 (E0-H).

## Suite acquisition and version

| Declaration | Installed header value |
| --- | --- |
| `kAEGPDynamicStreamSuite` | `"AEGP Dynamic Stream Suite"` |
| `kAEGPDynamicStreamSuiteVersion4` | `5` (frozen in AE 9.0, per header comment) |
| C typedef | `AEGP_DynamicStreamSuite4` |
| Important refs | `AEGP_StreamRefH`, `AEGP_PluginID`, `AEGP_StreamGroupingType` |

The *C struct revision number* and the *PICA suite acquisition version constant* are not necessarily the same numeric value. Use the distributed macro rather than hardcoding a guessed integer.

## Grouping types

| `AEGP_StreamGroupingType` | Meaning | Child traversal |
| --- | --- | --- |
| `AEGP_StreamGroupingType_LEAF` | Leaf property | No: `AEGP_GetNumStreamsInGroup` is an error |
| `AEGP_StreamGroupingType_NAMED_GROUP` | Semantically named, host-defined children | Index or MatchName lookup |
| `AEGP_StreamGroupingType_INDEXED_GROUP` | Ordered and potentially mutable list | Index traversal; add/reorder under parent policy |

A group with zero children is still a group. Do not infer grouping type from visual appearance or the current number of children.

## Navigation APIs

| Member function | Parameters (semantic) | Result / required disposal |
| --- | --- | --- |
| `AEGP_GetNewStreamRefForLayer` | `pluginID, layerH` | Root stream ref; caller disposes |
| `AEGP_GetNewStreamRefForMask` | `pluginID, maskH` | Mask ref; caller disposes |
| `AEGP_GetStreamDepth` | `streamH` | Depth (layer is depth 0) |
| `AEGP_GetStreamGroupingType` | `streamH` | LEAF/NAMED/INDEXED |
| `AEGP_GetNumStreamsInGroup` | `streamH` | Child count; illegal on leaf |
| `AEGP_GetNewStreamRefByIndex` | `pluginID, parent, index` | New child ref; caller disposes |
| `AEGP_GetNewStreamRefByMatchname` | `pluginID, named parent, name` | New child ref; caller disposes |
| `AEGP_GetMatchName` | `streamH, output char buffer` | UTF-8 MatchName, size `AEGP_MAX_STREAM_MATCH_NAME_SIZE` |
| `AEGP_GetNewParentStreamRef` | `pluginID, streamH` | New parent ref; caller disposes |
| `AEGP_GetStreamIndexInParent` | `streamH` | Valid only under indexed parent |

**Memory contract:** Every `GetNew...Ref` marked in the SDK as caller-owned must be released through `AEGP_DisposeStream`. Do not free with `free()`, retain indefinitely, or confuse with a privately allocated `TDB_StreamBase*`.

## Structural mutation APIs

| Member | Parameters | Constraints and effect |
| --- | --- | --- |
| `AEGP_CanAddStream` | `group_streamH, utf8_match_nameZ, can_addPB` | Preflight **parent admissibility only** |
| `AEGP_AddStream` | `pluginID, indexed_group_streamH, utf8_match_nameZ, streamPH0` | Undoable. Indexed parent only. Dispose returned ref |
| `AEGP_DeleteStream` | `streamH` | Undoable, child of indexed group. Dispose old ref later |
| `AEGP_ReorderStream` | `streamH, new_indexL` | Undoable, child of indexed group; mutates the ref |
| `AEGP_DuplicateStream` | `pluginID, streamH, new_indexPL0` | Undoable, child of indexed group |
| `AEGP_SetStreamName` | `streamH, UTF16 name` | Undoable, child of indexed group |
| `AEGP_SetDynamicStreamFlag` | `streamH, one_flag, undoableB, setB` | Restricted by flag and undoable mode |

The precise signature of `AEGP_CanAddStream` uses a **UTF-8 char pointer** in SDK25.6, not a UTF-16 display name. Likewise the child-type parameter of `AEGP_AddStream` is a UTF-8 MatchName. The set-name argument is instead null-terminated UTF-16.

## Separated dimensions

`AEGP_IsSeparationLeader`, `AEGP_AreDimensionsSeparated`, `AEGP_SetDimensionsSeparated`, `AEGP_GetSeparationFollower`, `AEGP_IsSeparationFollower`, `AEGP_GetSeparationLeader` and `AEGP_GetSeparationDimension` represent one multi-dimensional property and its separated leaf followers.

The official SDK25.6 header explicitly cautions: **do not assume Position is the only separable property forever**. When the leader is separated, direct keyframe-index API operations may need to target individual follower streams, even where higher-level value getters continue to handle the leader.

Internally, the factory registration path also calls `SetupCanonicalLayoutForSeperatedDimensions` where appropriate (E2-L F-VECTOR-095). That private call is not a replacement for supported AEGP APIs.

## Actual native Paint example

On AE2026, the real Brush-tool-generated Paint effect contains `ADBE Paint Group` (INDEXED), a registered `ADBE Paint Atom` child and nested Properties/Transform named groups. A read-only inspector traversed 170 nodes from six strokes with no API errors (E2-X F-VECTOR-087).

The *same* parent returned `AEGP_CanAddStream("ADBE Paint Atom") = TRUE`, but `AEGP_CanAddStream("CNL:PaintAtom") = FALSE`. This difference comes from native parent grammar, not simply a missing UI flag.

**A native type cannot be invented with `AEGP_AddStream`.** The host first has to know its C++ class and admit its MatchName. For the real internal background, see [Canonical Groups](../../../state-model/native-property-system/canonical-groups-admission.md).

## Failure modes

- Call group-only API on leaf; assume zero children means a leaf.
- Add a MatchName from an external plugin that has no host Creator.
- Assume `AEGP_CanAddStream == TRUE` establishes constructability/persistence.
- Retain an old StreamRef after add/delete/duplicate/reorder.
- Assume a MatchName or child index is a stable instance identity.
- Pass a UTF-16 display string where an SDK parameter requires UTF-8.
- Perform destructive tests on irreplaceable AE projects.

## Related Guide pages

[AEGP StreamSuite6](stream-suite.md), [Keyframes](keyframe-suite.md), [AEIG Native Property System](../../../state-model/native-property-system/index.md), [Official AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/), Adobe `Examples/AEGP/Streamie/Streamie.cpp`. Verified by E0-H/E0-S; live Paint by E2-X; internal explanation by F-VECTOR-084/095.
