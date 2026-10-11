---
status: research-active
last_verified: 2026-10-12
evidence: E2-L + E2-X-context + H
versions: AE2025 and AE2026 installed binaries; Adobe SDK25.6
---

# Independent Native Vector Objects: Type, Owner, Editor and Renderer

## What this project is *actually* trying to invent

The flagship goal is an effect or a new third-party host object type which owns its own editable vector hierarchy and produces vector geometry that After Effects handles *natively*. It must not be dependent upon Shape Layer creation, mask paths or native scripting as an implementation shortcut.

A host-native vector must solve five separate real contracts:

1. **Type**: third-party native TDB Stream class, stable MatchName, creator, canonical stream, constructor/destructor, cloning and serialization.
2. **Owner**: legitimate host-recognized TDB indexed tree attached to a persistent independent plugin object, with source path IDs and Timeline ownership.
3. **Native editor**: AE Pen/Selection/Move/Transform UI recognizes the plugin's native paths, forwards edits back to owning streams, and preserves Undo.
4. **Vector evaluation**: own TDB source enters actual BEE Vector evaluator registry, emits BEE_VectorArt with appropriate OriginInfo and time/cache semantics.
5. **Native render**: host RG and AGM evaluate and rasterize the native VectorArt, not a plugin PF_World or Drawbot overlay.

Satisfying one does **not** imply the others. Never report a Mask, script-created Shape Layer, extra effect parameter topic, PICA transport, SVG file or custom CPU renderer as proof of native plugin-owned Contents.

## Newly proven internal class and render ABI (2026-10-12)

The native renderer is a **virtual Layer-owned operation**. Real exported BEE_AVLayer and BEE_VectorLayer vtables both have a Rasterize2DGraph entry at index 235 (+0x758) in 2025 and at index 238 (+0x770) in 2026; their targets differ by class. Both expose GetLayerType at slot 80; AV is type 0, native Vector Layer is type 4.

The separate native creator callback BEE_VectorLayer::Create performs U.dll allocation then constructs a full C++ Vector Layer with TDB factory, BEE_CompItem owner and type identity. Class sizes change: 2025 AV=0x2810, Vector=0x2820; 2026 AV=0x27d8, Vector=0x2830. The vector type magic 0x05192004 stayed identical in these two versions. Object ownership and ABI versions therefore matter.

Native Shape Layer creation also uses the BEE project Undo/command dispatcher and an internal class-specific command adapter; command identifier changed 0x65 to 0x6a from 2025 to 2026. This is not the GetLayerType value.

The key implication is that **registering a procedural vector evaluator is not enough**. Unless an independent owner has the proper Layer/render override or a host-supported vector-output channel, an ordinary Effect will still output a pixel PF_World. No Effect SDK public selector yet demonstrates a vector result contract.

## Two genuine ambitious product directions

**A. Effect-owned native vector value** — CompNodeAE stays an Effect but a new native vector value/Contents property is attached to the effect or another host-recognized owner, editing and rendering integrated through the host render graph. This would enable arbitrary node-generated native paths, custom operator chains and direct AE Pen control on the same ordinary layer. Unknown if an Effect can ever be a first-class BEE VectorArt output source.

**B. New native vector Layer type** — register a new plugin-controlled Layer/Stream class, its indexed Contents tree, native editor binding and raster graph virtual implementation. Users create a new third-party vector layer akin to (but not actually) the built-in Shape Layer, entirely owned by the plugin. Unlike current Effect plugin type, this may require BEE/TDB private registry and host command integration. No external Layer subclass is currently proven.

Neither direction is achieved by the work to date. Direction B has newly identified native class/creation/render junctions, but no verified plug-in extension contract.

## What Adobe's own implementation demonstrably registers

AE uses two different registrations, both found in exact AE2025 and 2026 installed BEE/TDB binaries:

- TDB_StreamFactory::RegisterFactoryFunc — MatchName-to-native StreamBase creator (eager prototype/canonical creation during registration).
- BEE_VectorStream evaluator registry — MatchName-to-reference-counted polymorphic Operator, 20 built-in vector operators, mode 0 for geometry/graphics and mode 1 for filters.

A third-party must bridge **both** and acquire legal owner identity, native Pen editing and virtual render handoff. The existence of these registries does not prove the host accepts registrations after plugin load, foreign C++ object layouts or owners.

## Native-owner research gates and falsification

| Phase | Required observation | Status |
| --- | --- | --- |
| R0 | Locate both registries and native VectorArt code/evaluator | Done: host binary static |
| R1 | Understand native Layer allocator, GetLayerType, vtables, actual raster override and command dispatch | Done: F-VECTOR-025, static both years |
| R2 | Prove complete third-party TDB type Creator lifecycle safely and reversibly | Not yet achieved; creator ABI incomplete |
| R3 | Attach truly independent indexed Contents without native Shape or Mask ownership | Not yet achieved |
| R4 | AE Pen/Selection edits the plugin-owned TDB path, with real Undo/serialization | Not yet achieved |
| R5 | Native BEE_VectorArt and RG render from the new owner, no PF_World intermediate | Not yet achieved |
| R6 | Retest in two pinned host binaries with cache/frame random access and safe unload | Not yet achieved |

A candidate new operator that only works inside standard Shape Contents is worth recording separately as a partial extension, but it does NOT pass R3 or R5 for an independent owner.

## What research must do next (not build another mask demo)

1. From actual TDB::RegisterFactoryFunc and BEE evaluator registrar code, reconstruct full creator/destructor/refcount ABI, callback module lifetime, constructor-time checks and canonical stream metadata. Record exact matchname/creation registry signatures and negative paths.
2. Trace native VectorLayer Creation -> BEE_CompItem/BEE_Project attachment -> Timeline stream-root registration to find which registration is host-owned versus dynamically extensible. Verify any creator receives a BEE_CompItem pointer under a valid host context.
3. Trace AE Pen source-identity/edit callbacks from BEE_StreamSpec and FindEditableStream to the exact vector path control vertex writing functions, distinguishing generic shared tools from owner-specific path tools.
4. Trace native BEE_VectorLayer::Rasterize2DGraph to actual BEE_VectorArt and RG registration as separate branch from the ordinary AVLayer render method. Search for a generic reusable vector-provider output interface rather than assuming it exists.
5. When the contract is sufficiently complete, prepare a **version-pinned, gated experimental native creator** for the user's own disposable AE host test. It must not mutate an active production AE; no dummy callbacks; no hardcoded cross-version vtables. Abort clearly on unrecognized binary hashes.

Every session must report findings vs hypotheses, exact data and version, reproducible source, product-facing consequence, and the remaining missing contracts. Do not claim full Shape-like plugin capability from partial host API access.

## Evidence links

- F-VECTOR-008: TDB factory; F-VECTOR-014/015: second evaluator registry and operator vtable ABI.
- F-VECTOR-017: selected path -> editable source stream resolution.
- F-VECTOR-021/022: shared indexed stream commands and native SVG root owner precondition.
- F-VECTOR-025: actual AV vs Vector Layer renderer vtables, concrete Create callbacks and command IDs.
- EXP-SHAPE-023: reproducible read-only native layer render/creator analysis.
- H-SHAPE-007: falsifiable independent native vector owner hypothesis.
- datasets/ae-native-vector-owner-contract-summary-2025-2026.json: compact verified per-version facts.

The earlier Mask experiment F-VECTOR-024 is retained as an independent side branch for evidence preservation, but it is **explicitly NOT a milestone** toward registering a new native path type or plugin-owned Contents.


## 2026-10-12 — Creator callback, automatic initialization and lifetime are now partially decoded

Finding F-VECTOR-026 and EXP-SHAPE-024 extend the native typed-stream registry ABI evidence: factory registration retains/clones an MSVC std::function-erased creator, calls its CreateStream synchronously during type registration, and demands a real TDB_StreamBase with working IsLeaf, GetAsLeaf, SetupCanonicalLayout and (on native leaf) IsSeparationLeader virtual methods. Concrete TDB.dll native vftables in AE2025/2026 map these names to offsets 0x58, 0x80, 0x150 and leaf 0x298, respectively.

Crucial destructor caveat: TDB_ScRegisterStreams::~ only frees its own vector; explicit UnregisterAll performs reverse-order registration removal; UnregisterFactoryFunc deletes canonical/creator entries and destroys a native stream instance. An external plugin cannot count on implicit RAII cleanup of its native factory callback after unload.

No external Stream Creator, native Timeline owner, tool binding or BEE VectorArt evaluator was registered. This lowers research uncertainty about the first private ABI gate but does not move the user-visible S1-S3 success milestone. Next inspect cloning/serialization, registry startup/init order, project object survival and independent native owner adoption. Scripts/results in AEIG F-VECTOR-026, EXP-SHAPE-024 and 2025/2026 concise verifier data.


## 2026-10-12 — Native persistence ABI and a real independent CNL vector core

F-VECTOR-027 reconstructs native TDB Stream cloning, group/leaf serialization, unique stream identities, canonical stream lookup and host parent notification from both installed AE2025/AE2026 binaries. F-VECTOR-028 confirms additional BEE MatchName evaluator registry lifetime/lookup requirements. These native ABI observations do NOT establish third-party registration.

A genuine C++ component is now compiled: CNLNativeVectorCore.dll (F-VECTOR-029, EXP-SHAPE-026). It owns its own double-precision Bezier path tree, 64-bit stable object IDs, indexed nested Group/Path hierarchy, real path-control handles, procedural 4-cubic ellipse generation, deep clone and deterministic checksummed archive. CMake native tests, 2048 nested levels, Python ctypes loading the DLL and 20 PE exports all passed. This is a plugin-owned geometry-value source and future host adapter target, NOT AE-native TDB, not a Shape/Mask and not an AEX.

The missing, NON-NEGOTIABLE native host gates remain: (1) safe independent TDB type registration, (2) host-owned Timeline root for plugin Contents, (3) AE Pen/Selection binding with stream IDs, (4) BEE native evaluator registration and managed unload, (5) genuine host BEE_VectorArt/RG/AGM rendering instead of PF_World. A CNL archive must never be misreported as AEP/SLU-native persistence.

Next experiment should be a version-pinned, staged TDB type-registration host adapter design relying on native MSVC class/layout evidence. One candidate for offline assessment is a registration thunk using an existing correctly constructed TDB class under a new MatchName, to test factory admission without guessing a complete subclass; however even that is an UNPROVEN, potentially crashing private API that must not be executed in a working AE session. Investigate constructor/class invariants and reversible unregister/refcounts before any live test.
