---
status: evidence-graded-native-runtime-reconstruction
last_verified: 2026-10-15
evidence: E0-H + E0-S + E2-L + E2-X + H
versions: Windows AE2025 / AE2026, SDK 25.6; macOS private startup unverified
---

# Native Property System: Application Startup to Shutdown

This chapter follows the *property subsystem* through AE's lifecycle. It **does not** claim to describe all operating-system, media, GPU, plugin-scanning, licensing or UI startup procedures of the whole application. Its scope starts at the native provider initialization evidence and continues to property operations, ownership, destruction and module teardown.

See [Architecture](../../architecture/system-overview.md), [Stream objects](stream-object-model.md), [Factories](factory-registration-lifetime.md), and [Owner, Editor, Renderer](owner-editor-renderer.md).

## Phase 0 — Native host loads internal modules

**Observed implementation (E2-L).** Native `aelib.dll` uses **35 numbered lifecycle stages** in both installed versions. The actual `InitIterator` advances from lower to higher stages; `TerminateIterator` dispatches the current stage and **decrements** its value. Sorting CALL instructions by address does **not** recover the termination order.

| Stage number | Native module Birth | Native module Death |
| ---: | --- | --- |
| 15 | `TDB_Birth` | `TDB_Death` |
| 25 | `OM_Birth` | `OM_Death` |
| 27 | `FLT_Birth` | `FLT_Death` |
| 29 | `BEE_Birth` | `BEE_Death` |

Thus a complete ordinary initialization visits **TDB → OM → FLT → BEE**, while the corresponding normal reverse shutdown visits **BEE → FLT → OM → TDB**.

| Direct native aelib callsite | AE2025 RVA | AE2026 RVA |
| --- | ---: | ---: |
| `TDB_Birth` | `0x6DEA3` | `0x70283` |
| `OM_Birth` | `0x6E05D` | `0x70444` |
| `FLT_Birth` | `0x6E08B` | `0x70472` |
| `BEE_Birth` | `0x6E272` | `0x70647` |
| `BEE_Death` | `0x6EF56` | `0x712E6` |
| `FLT_Death` | `0x6EF40` | `0x712D0` |
| `OM_Death` | `0x6EF24` | `0x712B4` |
| `TDB_Death` | `0x6EEC0` | `0x71250` |

**The plugin boundary is separate.** Native stage 32 (visited **before BEE's stage 29** when terminating in reverse) calls `MEE_AEGP_Death`, `MEE_AEGP_Terminate` and `SetdownGeneralPlugins` in sequence. A requested general plugin setdown **does not prove its DLL has been physically unloaded**, or that all C++ Stream instances referenced by Undo tasks have been destroyed.

**Interpretation boundary:** these are original static compiled branches, not proof of every process's runtime traversal or error/partial startup paths; no supported foreign Stream-class registrar has been established. See [Native aelib module lifecycle](../../architecture/native-module-startup-shutdown.md), F-VECTOR-073–077 and F-VECTOR-106, and the SHA-pinned datasets.

### An additional BEE → TDB name-search callback

In both installed versions, `BEE_Birth` also constructs a native `std::function` and calls **`TDB_StreamGroup::SetFindStreamByNameNullOKFunction`**. The TDB name-search function later invokes the registered callback or returns null if absent. This is **existing Stream name resolution**, not the `TDB_StreamFactory::RegisterFactoryFunc` mechanism used to register new typed C++ Creators. See [TDB Name Lookup Callback](name-lookup-callback-bridge.md) (F-VECTOR-105).

## Phase 1 — Adobe internal native Stream providers register their types

The host-wide `TDB_StreamFactory` accepts typed C++ creators keyed by `TDB_MatchName`. At least three independent Adobe DLLs participate:

| Module | Example internal registration | Concrete class or family | Evidence |
| --- | --- | --- | --- |
| `OM.dll` | `RegisterFactoryFunc("ADBE Mask Shape", OM_Stream::Create, …)` | Native mask-path `OM_Stream` | F-VECTOR-093/094 |
| `FLT.dll` | `TDB_ScRegisterStreams::Register` | Effect and Mask stream/group classes | F-VECTOR-093 |
| `BEE.dll` | `BEE_Layer/AVLayer/...::RegisterStreams` | Layer, Paint, Text, Vector, etc. | F-VECTOR-054, 073–077, 080 |

In FLT's verified helper, six registrations are observed in AE2025 and seven in AE2026 (the additional `EFFECT_BLENDMODE` name). `OM_Birth` constructs an actual `TDB_MatchName("ADBE Mask Shape")`, retains it in `OM_StreamNamePtr_MASK_SHAPE` and supplies `OM_Stream::Create`. Neither is an arbitrary external plugin registration.

**Paint is a special two-part host implementation.** `Required/Paint.aex` exists and uses the nonpublic `Paint Suite`, whose host entrypoint is in `AfterFXLib.dll`; the rich native Paint Stream classes are independently registered by BEE's `BEE_AVLayer::RegisterStreams`. A Paint AEX file is not proof that an unrelated developer gets these host-internal registration rights.

## Phase 2 — Registration eagerly constructs a canonical instance

Native machine-code paths establish this order on the successful registration path:

```text
TDB_StreamFactory::RegisterFactoryFunc
  → acquire recursive mutex
  → find MatchName in Creator registry; reject duplicate
  → insert Creator callback into registry map (factory +0x28)
  → CreateStream(matchName, ...) [NOW, at registration time]
  → insert canonical prototype into canonical-instance map (factory +0x38)
  → test native IsLeaf / GetAsLeaf / IsSeparationLeader
  → initialize separated dimensions if applicable
  → conditional virtual SetupCanonicalLayout
  → release mutex
```

The Creator uses the private Windows x64 MSVC `std::function` / TDB class ABI. A callback with an incorrect signature or incomplete native object can crash **inside RegisterFactoryFunc**, even before a project layer or a Timeline property exists. Evidence: F-VECTOR-025–031, 095/096.

The private offsets `+0x28` / `+0x38` are **observed only in the two installed 2025/2026 builds**, not a supported struct definition.

## Phase 3 — Canonical group structure is constructed

A leaf inherits `TDB_StreamBase::SetupCanonicalLayout`, whose observed implementation is an empty return. A native group overrides that function:

```text
TDB_StreamGroup::SetupCanonicalLayout
  → virtual FillInCanonicalUILayout (vtable +0x1C8)
  → SetupCanonicalLayoutForSeperatedDimensions
  → TDB_StreamGroup::SetUILayout
```

The Shape Contents native vtable resolves `+0x1C8` to `BEE_VectorStream::VectorsStreamGroup::FillInCanonicalUILayout` in both AE2025 and AE2026. This is a real link between **provider registration** and **property child grammar**; it is not a conjecture based only on class names. Evidence: F-VECTOR-092/095, strict vtable and IAT checks.

This builds *canonical layout*, not a serialized document instance. Parent-specific `CanStore` and factory constructability are separate decisions; a child cannot be declared universally addable from a canonical template alone. See [Group grammar](canonical-groups-admission.md).

## Phase 4 — Document-owned items, layers, effects and streams

**Important subsystem boundary:** a factory-created `TDB_StreamBase` does not automatically become a project-owned native Layer. A host-layer creation/attach transaction also has to assign a `BEE_CompItem` owner, satisfy `BEE_LayerSet` bookkeeping, obtain appropriate identities and Undo/project state, and integrate native editor/render services.

For **a built-in Shape Layer**, recovered internal evidence includes:

```text
Built-in New Shape Layer command
  → native BEE_NewLayerTask<4> / command dispatch
  → BEE_Layer::CreateLayerFromType(4, comp)
  → BEE_CompItem::AttachLayerToCompOnly(...)
  → BEE Vector root groups / Contents instances
```

This is the internal stock type-4 route. The `CreateLayerFromType` switch is built around existing layer families; a generic foreign-layer provider is not demonstrated. A factory-created detached `BEE_VectorLayer` with null parent CompItem is not automatically equivalent to a real attached layer. Evidence: F-VECTOR-037/055–059/067–071.

For built-in Paint / Text property groups, the owner may be an existing AV/Text layer or Effect. A third-party plugin that can **read** an existing stream is not its native type provider.

### How serialized child properties are restored

New strict E2-L evidence traces `TDB_StreamGroup::Read` in both installed versions:

```text
Read child's serialized TDB_MatchName
 → virtual ReadAndStore (Named or Indexed group)
 → TDB_StreamFactory::CreateStream(saved MatchName)
 → Indexed: CanStore → InsertStream → SetParent
 → child's native Read(...)
```

This connection proves a saved child is reconstructed through the **active host class registry**, not simply copied from canonical memory. Native `InsertStream` performs version-sensitive indexed ownership/cache bookkeeping; its public AEGP counterpart does not create new C++ classes. The missing foreign-Creator AEP behavior remains unknown. See [Native instance creation](stream-instance-creation.md), [Indexed insertion](indexed-group-insertion.md), and [StreamGroup Read / Write](document-stream-serialization.md), F-VECTOR-097/098.

## Phase 5 — The host exposes properties to Timeline / AEGP / scripting

Scripting's named/indexed `PropertyGroup` and `Property` hierarchies and AEGP `AEGP_StreamRefH` are *public access coordinates* over host state. They are not guaranteed one-to-one wrappers over particular private object pointers. The host uses internal `MEE`/BEE/TDB bridges to normalize AEGP selection/stream coordinates into `TDB_StreamIDPath`-like addresses (E2-L).

A Timeline tree can exist only when all relevant conditions are satisfied: a document-owned instance, its parent-child grammar and valid class creation, and the host's editor/selection presentation. **No tested supported SDK general foreign Stream class provider exists in SDK 25.6** (scoped audit, F-VECTOR-088).

The user-confirmed AE2026 Paint inspector traversed real native `ADBE Paint Group` and child `ADBE Paint Atom` using **public read-only AEGP**. Host project mutation count remained zero. Evidence: F-VECTOR-083/087.

## Phase 6 — Value changes, animation and expressions

Distinguish operations rigorously:

1. **Structural**: add, remove, duplicate, reorder or rename an existing registered child Stream.
2. **Authored value**: set a keyframe or parameter; current and pre-expression evaluated values need not match.
3. **Derived/evaluated**: expression result, time-sampled value, parent-space transform or render-dependent stream state.
4. **Runtime**: evaluation identity/dirty state/render request generation and cache invalidation.

AEGP reports `CanVaryOverTime` separately from `IsStreamTimevarying`, and `AEGP_StreamType_NO_DATA` can mark a native Paint Path whose *internal* value exists but has no normal public AEGP StreamValue accessor. F-VECTOR-087 host Paint fixture: 6 strokes, 170 native nodes, 109 can-vary leaves, zero currently time-varying leaves and zero nonzero keyframe counts. These fixture facts are **not global Paint behavior**.

See [Property operations](property-operations.md), [Streams and Properties](../streams-properties.md) and [Animation](../../animation-system/keyframe-api-history.md).

## Phase 7 — Undo, save/reopen and evaluation

Three distinct services consume property state:

| Service | Observed bridge | What is not yet proven |
| --- | --- | --- |
| Native editor / Undo | BEE command/task and TDB StreamIDPath evidence; stock new-layer Undo | Extension command table/provider for a foreign Stream |
| Persistence | Native `Read`, `Write`, `CloneStream`; project AEP/AEPX systems | Correct foreign unknown-type roundtrip and version migration |
| Evaluation/render | BEE Stream spec, VectorArt/evaluator registry and RG graph | Arbitrary new BEE vector operator/effect owner producing correct native render |

A renderer can consume evaluated properties without exposing the same mutable document graph. Re-render validity/cache identity is its own plane. Refer to [Owner, editor and renderer](owner-editor-renderer.md) and [AEIG render graph](../../render-graph/render-graph-model.md).

## Phase 8 — Undo history task destruction and factory teardown

A document editing context's history is another potential owner of native objects. The **real BEE_UndoContext destructor** calls the same stack-clear helper for both its Undo and Redo history stacks. The helper reads each list record, conditionally calls the task's virtual deleting destructor with native flag 1, then removes the list range. The generic BEE Undo/Redo commands separately replay tasks and enqueue returned task pointers into the opposite history stack (F-VECTOR-101). **F-VECTOR-102 now verifies a concrete first-party removed-TDB-Stream ownership chain**: the inverse Add task conditionally invokes the owned noncanonical Stream's virtual deleting destructor. **F-VECTOR-103 now verifies that BEE_Project::~BEE_Project directly calls BEE_UndoContext::~BEE_UndoContext** for the same project-held context accessed by native Layer/Item Undo commands. This connects Project destruction to both history-stack destructors and eligible Stream destructor callbacks. Ordering relative to TDB factory/module teardown, arbitrary foreign classes and error branches remains unverified. F-VECTOR-104 additionally identifies a neighboring Project-owned missing-font vector: the Project destroys `TXT_UsedFontData` entries in holder `+0x118` **before** destroying the UndoContext subobject at holder `+0x10`. This is a cross-subsystem teardown order, not evidence that Undo tasks actually access the font records. See [Undo Task Lifecycle](undo-task-lifecycle.md), [Project UndoContext Lifecycle](project-undo-context-lifecycle.md), and [Project Missing-Font Metadata](../../text-system/project-missing-font-data-lifecycle.md).

### Factory unregister and native host teardown

On the traced successful branch, `TDB_StreamFactory::UnregisterFactoryFunc` performs:

```text
TDB_StreamFactory::UnregisterFactoryFunc
  → private UnregisterFactoryFunc_NullOK(false)
    → lock factory mutex
    → find and unlink canonical prototype (factory +0x38)
    → find and unlink Creator callback (factory +0x28)
    → invoke prototype's virtual deleting destructor
    → unlock
```

For `OM_Stream`, `OM_Death` subsequently frees the native MatchName and zeros the exported pointer. The registration entry's own module, callback and vtable **must remain loaded until no live instances can call them**; the success path does not establish that all document-held, Undo-held, cache-held or render-held instances have vanished. Evidence: F-VECTOR-093/094/096.

The complete exception/unwind rollback of `RegisterFactoryFunc` (especially after Creator insertion but before prototype completion) remains **unknown**. No unverified plugin should assume unregister can rescue a crashed partially initialized host.

## Verification checklist for a novel third-party type

A *true* AE-host-native custom type requires separately observed PASS for:

- native third-party loading and host-approved registration;
- a valid C++ Stream creator with compatible ABI and canonical prototype;
- parent named/indexed group admission and native UILayout;
- actual document-owned instance visible/editable in the **standard AE Timeline**;
- animation/Undo/path editing and object identity;
- AEP save, shutdown, reopen, clone and version migration;
- native evaluator/render and correct cache invalidation where relevant;
- live-instance exhaustion and safe unload, Windows and macOS qualification.

As of 2026-10-15 these have **not** been completed for a foreign `CNL:` class. The independent ChapeLayer/CNL C++ runtime and simulated tests are not equivalent.

## Primary evidence / reproduce

- F-VECTOR-073–077: Adobe BEE Birth/Death and native layer stream registration.
- F-VECTOR-080/081, 083/087: Paint AEX bridge and real Paint native UI/AEGP readings.
- F-VECTOR-092–096: strict canonical grammar, OM/FLT native registration, real C++ ABI, register/layout and unregister ownership.
- F-VECTOR-055–059, 067–071: owner/CompItem/Undo/native task boundary.
- F-VECTOR-097–101: native Stream construction, Indexed insertion/removal, archive reload/missing Creator flags, Undo task replay and destroying both TaskStacks.
- Datasets: `ae-native-om-flt-bee-crossmodule-boot-verified-2025-2026.json`, `ae-tdb-eager-canonical-vtable-2025-2026.json`, `ae-tdb-group-to-bee-shape-canonical-dispatch-2025-2026.json`, `ae-tdb-native-creator-canonical-lifetime-2025-2026.json`.

Each datum lives in the repository `datasets/`, with a matching independent verifier under `experiments/vector-shape/probe-src/tools/`. Original installed binaries were read but not modified.
