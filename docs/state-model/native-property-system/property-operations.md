---
status: architecture-reference
last_verified: 2026-10-15
evidence: E0-G + E0-H + E0-S + E2-L + E2-X + H
versions: SDK25.6 and Windows AE2025/2026
---

# Native Property Operations: Inspect, Mutate, Animate and Persist

An AE-native property operation takes place on a **host-owned Stream in an existing Layer or Effect**. AEGP, scripting, Expressions and internal TDB/BEE are different access planes with different calling conventions, lifetime and support. This chapter describes user-visible operations in a use-case order; API-specific details are in [API Atlas](api-atlas.md).

## Acquire a property safely

1. Identify the active owning composition, layer and effect using supported AEGP or Scripting APIs.
2. Resolve the corresponding StreamRef by enumerating its parent and MatchName.
3. Retrieve grouping type **before** enumerating group children. A leaf is not a group.
4. Use current stream type and temporal metadata to select legal value operations.
5. Dispose public StreamRef/Value handles using the matching documented suite and **reacquire** after structural edits.

An `AEGP_StreamRefH` is not a persistent property identifier or an owning pointer to TDB/BEE internals. Holding one across add/reorder/delete/keyframe changes can invalidate it. Scripting `PropertyGroup.property(index)` references may also change after indexed-group mutation.

## Enumerate the group hierarchy

`AEGP_DynamicStreamSuite4` exposes grouping types **LEAF, NAMED_GROUP and INDEXED_GROUP** and parent/child APIs. Scripting uses `Property`, `PropertyGroup`, `propertyIndex`, `matchName` and `propertyGroup()`. These are related but not guaranteed identical representations of every private class.

| Operation | Supported public concept | Constraint |
| --- | --- | --- |
| Identify match name | `AEGP_GetMatchName` | Semantic type, not instance ID |
| Query grouping type | `AEGP_GetStreamGroupingType` | Do this before group-only enumeration |
| Enumerate children | `AEGP_GetNumStreamsInGroup`, `AEGP_GetNewStreamRefByIndex` | Group-only operation |
| Check insertion | `AEGP_CanAddStream` | Preflight parent policy; not a Creator probe |
| Add built-in child | `AEGP_AddStream` | Requires indexed parent and registered acceptable child |
| Reorder / duplicate / delete | `AEGP_ReorderStream`, `AEGP_DuplicateStream`, `AEGP_DeleteStream` | May invalidate existing refs |
| Get native session UID | `AEGP_GetUniqueStreamID` | Session-scoped only; do not treat as serialized identity |

The exact SDK header is `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers/AE_GeneralPlug.h` (E0-H). Adobe's `Examples/AEGP/Streamie` demonstrates real built-in Paint operations (E0-S).

## Value type, animation, and expressions

A leaf's `AEGP_StreamType` guides whether a value can be retrieved through normal AEGP StreamValue APIs. **Four different properties must remain distinct:**

- `AEGP_CanVaryOverTime`: the class may support keyframing/time variation.
- `AEGP_IsStreamTimevarying`: current effective state varies over time (keyframes/expression).
- `AEGP_GetStreamNumKFs`: number of currently authored keyframes.
- `AEGP_GetNewStreamValue`: evaluated value at a requested time (with an option controlling pre/post-expression evaluation).

`AEGP_StreamType_NO_DATA` is a legitimate result for a specialized internally editable native leaf such as `ADBE Paint Shape`; it is **not** permission to invent an arbitrary binary payload or force `GetNewStreamValue`.

### Keyframe operations

`AEGP_KeyframeSuite5` provides specific supported keyframe operations on eligible streams. For batch changes, prefer documented transactional APIs over repeated invalidating child-structural operations. Spatial animation and roving/time interpolation have additional coordinate conventions; see [Keyframe history](../../animation-system/keyframe-api-history.md) and [Spatial interpolation](../../animation-system/spatial-interpolation.md).

Scripting properties expose keys/expressions through their own object model. Do not infer one API's handle validity rules from the other.

### Expressions

Authoring an expression and enabling it is not identical to the expression's **effective runtime state**. Parsing/runtime errors can alter evaluation behavior or automatically disable execution. Pre-expression and post-expression values are different evaluation requests.

## Structural changes and Undo

`AEGP_AddStream` is an undoable operation only on an **indexed** group that can admit the registered MatchName. Existing native Stream authoring may involve host command tables, BEE selection and current native editor context. Calling a private `BEE_Cmd...` or TDB method directly is not equivalent to starting a host Undo transaction via a supported API.

In the native internal Shape creation path, a stock command builds a `BEE_NewLayerTask<4>` and ultimately creates and attaches a layer through `BEE_CompItem`. This native task is **not a supported command-provider SDK for a foreign new Layer kind** (F-VECTOR-058/071).

## Native group insertion and deserialization

For indexed native groups, \`TDB_IndexedStreamGroup::InsertStream\` checks **virtual CanStore before mutation**, updates reverse indices and cached capsule paths, then calls \`TDB_StreamBase::SetParent\`. The private vtable position of \`InsertStream\` changes between AE2025 and AE2026: see [Indexed child insertion](indexed-group-insertion.md).

Loading a saved Group also has an explicit per-child pipeline: \`TDB_MatchName::Read → virtual ReadAndStore → TDB_StreamFactory::CreateStream → InsertStream → child Read\`. This is not the public API's \`AEGP_StreamRefH\` lifetime or a documented opaque preservation rule. The full method/callsite reference is [TDB_StreamGroup Read / Write](document-stream-serialization.md) (F-VECTOR-098).

## Save, reopen, clone and version upgrade

- A standard built-in Stream participates in Adobe's own AEP serialization format; its private `Read`/`Write` implementations are not public C++ serializer contracts.
- Serialized values are not necessarily identical to the in-memory `AEGP_StreamValue` union or a private C++ object layout.
- Native `TDB_Stream::CloneStream` is distinct from copying a StreamRef handle.
- Loading project files can reconstruct built-in Layer kinds through a fixed `BEE_Layer::CreateLayerFromType` switch. A foreign Stream class also requires its type Creator to be available at the appropriate load phase.
- Save/reopen, duplicate, Undo/Redo and migration to another AE version must each be separately qualified before claiming a new third-party native class works.

For the file format boundary, see [AEP persistence](../../persistence/aep-binary-model.md) and [State snapshots](../snapshots.md).

## Rendering, invalidation and cache

A property edit changes authored state. Its effects on evaluated values, dependency GUIDs, asynchronous render requests and cache invalidation depend on the respective BEE/RG path. A static Stream identity does **not** itself establish correct rendering of a novel custom type. For vector graphics, the BEE VectorArt evaluator is a separate registry from the TDB factory.

The product-valid completion matrix is in [Owner/editor/renderer](owner-editor-renderer.md). Actual Paint metadata: F-VECTOR-083/087. Public SDK: E0-H, E0-S. Private path statements: F-VECTOR-055/058/062/071/084/095.
