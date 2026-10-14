# Independent Native ChapeLayer — Host Admission Contract and Completion Gates

**Status (2026-10-14): BLOCKED for a truly new Adobe-host-owned `BEE_Layer` class.** Offline evidence and native CNL runtime tests pass; positive host-native layer registration/creation has **not been demonstrated**.

This is an engineering qualification, not a universal theorem that no undocumented interface exists. It is important not to call independent CNL timelines, Effects, built-in Shape Layer wrappers, mocks or ASTs a complete new AE native layer family.

## 1. Product requirement

ChapeLayer must be a **separate AE-native Layer family** with:
- an independent visible Layer type, not a built-in Shape/Text/AV carrier;
- a fully host-owned Timeline property hierarchy analogous to Shape Contents or Text Animators, with plugin-defined native groups/types;
- keyframe/animation support, parenting, order, native UI expansion, selection and undo;
- editable paths/gizmos/tool interaction as appropriate, with true Adobe owner/selection identities;
- native rendering/evaluation and save/reopen persistence, plus clone/duplicate/import;
- versioned cross-platform lifecycle without stale code pointers after plugin unload.

The previously compiled CNL typed Timeline, archive, visitor C ABI and runtime tests remain useful internal components, but they do not fulfill host-admitted native type registration.

## 2. Evidence so far

| Gate | Observed result | What it proves |
| --- | --- | --- |
| Native CNL Timeline and AEX build | PASS in current Windows x64 lab | Compiled CNL runtime/exports, not Adobe-owned class |
| CNL CTest (4/4) | PASS | CNL data model consistency, archive and C ABI tests |
| Public SDK 25.6 AEGP register suite | Checked | No arbitrary `BEE_Layer` subclass registration callback |
| Published C++ SDK guide 26.5 | Checked documentation | Added existing parametric mesh Layer creation; does not document custom Layer-class provider |
| Existing `BEE_Layer::CreateLayerFromType` | Eight-way native dispatcher verified for 2025/2026 | This built-in factory does not dispatch an unregistered new integer kind |
| Built-in BEE native registrar lifecycle | 9 family startup + 9 teardown edges verified, two native versions | BEE module startup/shutdown registration, not third-party BEE Layer admission |
| `BEE_Birth` byte map | Native arguments traced for 2025/2026 | Data-map initialization is separate from built-in Layer Stream bootstrap |
| `PluginSupport` module registrar | ML GUID + `UIPluginModuleFactory` | A separate plugin loader, not an evidenced BEE Layer factory |
| `BEE_Layer::CloneAndAttach` + Comp attachment | RTTI and version-specific fields/vtable proven | More native layout and lifetime obligations, not foreign class acceptance |
| New `ChapeLayer` in unmodified AE | **NOT PROVEN** | The required positive acceptance test is missing |
| Mac ARM64/x64 host-native admission | **NOT TESTED** | Cannot claim cross-platform support |

Full data and offline verifiers: F-VECTOR-037, 066–079 and EXP-SHAPE-037, 066–079, where available. Machine gate: `experiments/vector-shape/probe-src/tools/verify_chapelayer_native_host_readiness.py`. Run artifacts: `datasets/chapelayer-native-host-admission-readiness.json`.

Documentary references (not substitutes for local binary evidence):
- https://ae-plugins.docsforadobe.dev/intro/whats-new/
- https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/
- https://ae-plugins.docsforadobe.dev/aegps/overview/

The 26.5 guide documents `AEGP_CompSuite13::AEGP_CreateParametricMeshLayerInComp` and `AEGP_StreamSuite7`, but neither is a creator/registrar for a foreign native `BEE_Layer` class.

## 3. Required *host-provided* native owner extension ABI (hypothetical, NOT an Adobe API)

A viable, supported capability would need to provide all of the following **as one coherent host contract**, rather than patched native functions:

1. **Type registration**: Stable plugin-owned Layer-type identifier, MatchName, versioned registration and discoverability before project load.
2. **Host allocation and ownership**: Host controls object construction, object identity, foreign-class lifetime, clone, deletion, module pinning, CompItem insertion and rebuild after project load.
3. **Editable property grammar**: Host accepts plugin-defined Indexed/Named native stream groups, typed keyframed properties and explicit parent-admission rules in actual Timeline, without a carrier.
4. **Native editor identity**: Host selection/IDPath, Undo/Redo, drag/point/curve gizmos, Pen tool and hit testing work on newly defined native objects.
5. **Rendering**: Registered native geometry/evaluation contract compatible with the actual BEE RenderGraph, VectorArt/AGM, color/precision and multi-frame renderer behavior.
6. **Persistence**: Versioned .aep archive encoding, clone/import/duplicate, migration and unknown/unavailable-plugin behavior.
7. **Lifecycle**: Thread safety; deterministic per-project disposal, global teardown, owner-aware unregistration and no dangling virtual method pointers on module unload.
8. **Compatibility**: Officially specified Windows x64 and macOS ARM64 ABI or a C ABI shim, per-host-version negotiation, opt-out on ABI mismatch, documented errors.

A *proposed* vendor-facing API might conceptually supply `RegisterNativeLayerProvider`, `RegisterNativeStreamSchema`, `RegisterNativeVectorEvaluator`, `RegisterNativeEditorProvider` and `UnregisterNativeLayerProvider`; **none of those function names is claimed to exist in AE**.

It is unsafe to invent such exports, cast arbitrary `BEE_Layer*` pointers into private native ABI, patch the eight-way constructor switch, or call `TDB_ScRegisterStreams` with unverified `std::function` / RTTI objects.

## 4. Acceptance gates before declaring product complete

**Gate A — true host-type registration.** On a disposable AE installation and empty test project, a plugin-defined new Layer kind can be constructed and recognized by the actual host, with no built-in Shape/AV/Text owner used as a carrier.

**Gate B — native Timeline.** Two distinct plugin-defined Layer families have multiple custom groups/types, reordered children, editing, keyframes, expressions and Undo/Redo visible as ordinary host-native properties.

**Gate C — rendering and tools.** The host renders correctly over time in native pipeline, and provides native selection/drag/path operations across project and viewer context.

**Gate D — persistence.** Save `.aep`, close, reopen, duplicate, undo, migrate and recover missing-plugin references without corrupting native owner state.

**Gate E — stability.** Validate teardown/unload, version migration and memory safety, including working-project protection. Avoid touching installed user plugins or projects during unknown private ABI experiments.

**Gate F — cross-platform.** Repeat host tests on Windows x64 and macOS ARM64; ensure pinned version-specific native layouts and ABI, no blind pointer offsets.

Until **all** relevant gates pass, the honest shipping status is `NOT_DEMONSTRATED_HOST_NATIVE_LAYER_ADMISSION`. There is no approved “partially native” interpretation that satisfies the original independent-layer requirement.

## 5. Highest-value route forward

1. Ask Adobe's After Effects SDK/developer team for a **documented native Layer provider or TDB/BEE owner extension ABI** with exact lifecycle guarantees; request whether such an API is available via partner/internal SDK.
2. If a provider interface is obtained, implement a guarded CNL adapter using the already implemented typed Timeline runtime, then run Gates A–F.
3. If no provider exists, state that the requested product cannot be honestly completed as an ordinary supported AE plugin under the current constraint. A separate Effect/Shape-carrier design is a different product and must never be represented as completion of this one.

No private Adobe host calls, in-process ABI patching, unsafe AEX installation or CompNodeAE edits were authorized by this document.
