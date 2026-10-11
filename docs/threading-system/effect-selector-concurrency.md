---
status: active
last_verified: 2026-09-23
evidence: MFR selector contracts + sequence-data ownership + dynamic-flag warnings + 13.5 thread/project split
---
# Effect Selector Concurrency

Thread safety in modern AE is a **selector/lifetime/state contract**, not merely "the pixel loop has no globals".

## Selector concurrency classes
### Main-thread serialized lifecycle
`PF_Cmd_GLOBAL_SETUP` and `PF_Cmd_GLOBAL_SETDOWN` are guaranteed on the main thread and are not sent concurrently with other selectors. They are appropriate for process/module-lifetime registration, not per-instance mutable render state.

### Main-thread UI/edit selectors
UI/event selectors execute on the UI thread, but can overlap in time with render-side selectors once an effect participates in threaded rendering. `PF_Cmd_UPDATE_PARAMS_UI` is cosmetic-only; checking out parameters there is explicitly unsafe.

### Potentially concurrent render/sequence selectors
With `PF_OutFlag2_SUPPORTS_THREADED_RENDERING`, Adobe documents that `PF_Cmd_SEQUENCE_SETUP`, `PF_Cmd_SEQUENCE_RESETUP`, `PF_Cmd_SEQUENCE_SETDOWN`, `PF_Cmd_SMART_PRE_RENDER`, `PF_Cmd_RENDER` and `PF_Cmd_SMART_RENDER` may be sent on multiple threads while UI selectors are active.

Therefore setup/resetup/setdown code is not automatically a serialized safe zone.

## State ownership under MFR
Modern render-time `sequence_data` is const and read through `PF_EffectSequenceDataSuite`; direct writable access is disabled by default.

`PF_OutFlag2_MUTABLE_RENDER_SEQUENCE_DATA_SLOWER` restores write access by creating independent per-render-thread copies. Those copies are **not shared state** and their mutations are discarded regularly after render spans.

Use the right storage class:
- immutable configuration -> synchronized sequence/render state;
- shared expensive derived value -> Compute Cache or another explicitly synchronized cache;
- per-thread scratch -> `thread_local` or frame/request-local storage;
- cross-frame evolving simulation -> validated state with explicit temporal identity, not accidental shared sequence mutation.

## Lock-boundary rule
Adobe's MFR guidance warns against calling host services while holding plug-in mutexes when those calls can re-enter or block on AE. The safe default is:
1. acquire plug-in lock;
2. snapshot/update plug-in-owned state;
3. release lock;
4. call host suites/checkouts/render services;
5. reacquire only if needed to publish results.

This reduces lock inversion between plug-in locks and host project/render locks.

## Dynamic-flag race boundary
`PF_Cmd_QUERY_DYNAMIC_FLAGS` may occur independently of the eventual render. Header comments specifically warn that asynchronously changing `PF_OutFlag2_OUTPUT_IS_WATERMARKED` can produce incorrect cached frames if the rendered state does not match the last queried flags.

General invariant:

**Any dynamic flag that changes pixel semantics must be derived from the same versioned state consumed by the corresponding render generation.**

A robust implementation snapshots semantic state, answers Query Dynamic Flags from that snapshot/generation, and renders from the same generation instead of rereading mutable external state later.

A concrete current-time case is `PF_OutFlag_NON_PARAM_VARY`. If an effect sometimes uses AE current time as an input and sometimes does not, declaring this bit unconditionally at global setup is correct but unnecessarily destroys still-frame cache reuse for static instances. The public header explicitly allows this flag to be overridden by `PF_Cmd_QUERY_DYNAMIC_FLAGS`. A stronger design therefore persists the choice of time-dependent input in an ordinary effect parameter/arbitrary-data contract, checks that exact instance state during `QUERY_DYNAMIC_FLAGS`, and sets `NON_PARAM_VARY` only when the current instance actually depends on host time. The render then evaluates `current_time / time_scale` (and, when needed, `time_step / time_scale`) from its own request and mixes the evaluated actual into SmartFX GUID dependencies. This keeps static instances cache-friendly while giving time-dependent instances correct frame identity.

Do not model AE time by hiding it inside a CNL/compiler intrinsic if the computation model is intended to remain host-independent. Prefer an explicit typed entry formal whose physical host binding supplies current time; the semantic program remains portable and the AE adapter owns the temporal contract.

The selector contract permits checking out current-time values of non-Layer parameters while handling `PF_Cmd_QUERY_DYNAMIC_FLAGS`. This makes a persisted arbitrary-data workspace a suitable authority for instance-specific decisions such as `PF_OutFlag_NON_PARAM_VARY`: decode/check the exact current workspace, set the bit only when it binds current-time semantics, and fail conservatively if the workspace cannot be interpreted. Do not infer a dynamic flag from unrelated mutable UI globals.

### Dynamic actuals need two identities
When a workspace can bind host-evaluated values such as current time, do not force one identity to serve both UI isolation and frame caching. The authoring/UI side can reproduce the **binding configuration** (which layer/source is selected, whether a scalar comes from a constant or AE current time, sampler settings, and so on), but it cannot in general reproduce the exact numeric actual that existed inside another render request.

Keep two identities instead:
- a stable configuration identity derived only from persisted/routable host-binding state, suitable for deciding whether a render-side diagnostic or inspection result still belongs to the current instance configuration;
- an evaluated actual identity containing the concrete per-request values, suitable for SmartFX GUID mixing, render/cache identity, and exact execution evidence.

Weakening the actual identity to make UI comparison convenient risks stale-frame/cache aliasing; requiring the UI to recompute render-only host values makes valid inspection results disappear. Separating the identities preserves both contracts.

## UI/render shared-state anti-patterns
Dangerous designs include:
- UI writes a global structure while render reads it without versioning;
- render mutates sequence state expecting UI to see it;
- UI owns a pointer referenced by render copies without publication/lifetime control;
- one mutex protects everything and is held while calling AE;
- static scratch buffers are reused by concurrent frames;
- lazy initialization is race-prone because multiple render selectors enter simultaneously.

## Host-specific divergence
Premiere's `PF_OutFlag2_PPRO_DO_NOT_CLONE_SEQUENCE_DATA_FOR_RENDER` changes host ownership policy. Adobe advises against using it because of historical parameter-UI problems. Host-specific flags should be treated as semantic ownership contracts, not "faster" switches.

Cross-host thread behavior must be tested independently even when the PF ABI is shared.

## Test matrix
A proper concurrency test must vary more than frame count:
1. same effect instance, many frames;
2. multiple instances of same effect;
3. UI parameter drag while frames render;
4. sequence resetup/setdown concurrent with other instances;
5. cancellation/abort during expensive host checkout;
6. project close/effect deletion near async completion;
7. MFR on/off and different worker counts;
8. cache warm/cold to alter callback ordering.

Use deterministic output hashes and race instrumentation. A test that merely "does not crash" is insufficient: stale semantic state and nondeterministic pixels are concurrency failures too.

## Failure signatures
- output differs between MFR on/off -> shared mutable state or non-deterministic dependency;
- rare stale frame after UI edit -> publication/dynamic-flag generation race;
- deadlock under scrub/cancel -> lock inversion with host callback;
- crash during close -> async/request lifetime escapes effect instance;
- performance collapses only with mutable render sequence flag -> per-thread copy/serialization overhead.

## Unknown frontier
Still unresolved for AE internals:
- exact worker pools used by PF render selectors versus BEE/RG task execution;
- which host callbacks can re-enter plug-in selectors on the same or another thread;
- scheduling/fairness between MFR, speculative preview, media decode and GPU queues;
- whether some sequence lifecycle operations are internally serialized per instance even though the public contract requires thread safety.

Related: `docs/threading-system/overview.md`, `docs/mfr/state-ownership.md`, `docs/state-model/snapshots.md`, `docs/render-graph/async-render-requests.md`.
