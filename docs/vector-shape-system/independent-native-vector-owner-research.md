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


## 2026-10-12 — Concrete host plugins prepared; prove registry permission before declaring victory

F-VECTOR-031 confirms exact AE2025/2026 MatchName private constructor stores a 16-byte GUID obtained from TDBp_MatchNamePool::GuidFromName, and Adobe's complete ParamPathStream::Create allocates a 0x468-byte native TDB object. This suggests a cleaner FIRST external-registry admissibility test: register that complete built-in Creator under a NEW name, rather than guessing a foreign TDB_StreamBase layout. A ParamPathStream is, however, an effect/parameter path class, not a native Shape VectorArt owner. Registry acceptance, if achieved, cannot satisfy editable independent Contents.

The new safe CNLNativeVectorHostProbe AEX (F-VECTOR-032) actually embeds CNL-owned procedural cubic geometry into an AEGP, with user-invoked read-only private export/version preflight. It compiled and passed x64 PE checks; no AE installation or host test was performed. This is now the preferred next user-validation artifact.

Offline cross-module MSVC std::function Creator ABI/lifetime and reverse explicit cleanup model passed (EXP-SHAPE-029), BUT it is a model of the native callable pattern, not Adobe's actual C++ Stream class, allocator, host project lifetime or unmanaged private factory.

A separate guarded, HIGH RISK CNLPrivateTDBDisposable.aex was compiled for a manually authorized disposable AE host only (F-VECTOR-033, EXP-SHAPE-030). Its private mutation code is **NOT tested in AE**, and its automatic unregister remains best-effort, not assured rollback. Never recommend this AEX for regular project use, automatic startup or before the safe AEX is host-tested. Installation and AE GUI checks belong to the user.

Current research gates unchanged in the host: independent new TDB type (NOT PROVEN), non-Shape native indexed Contents owner (NOT PROVEN), AE-native Pen editing (NOT PROVEN), BEE evaluator insertion (NOT PROVEN), native VectorArt/RG from custom owner (NOT PROVEN). The compile success is a genuine engineering milestone, not a host-native feature claim.


## Latest safety-and-ABI milestone (2026-10-12): rebuilt native type experiments

F-VECTOR-034 pinpoints and fixes the HIGH-RISK registration test's mismatched native callback fifth argument (bool rather than unsigned int). A new MSVC2022 C++ object compiles the exact native TDB_StreamBase*(TDB_MatchName const&, TDB_StreamFactory*, bool, unsigned int, bool) std::function signature, whose decorated function parameter suffix exactly matches Adobe's RegisterFactoryFunc exports in both installed AE2025 and AE2026 binaries. This establishes symbol-level ABI agreement, not permitted external plugin registration or full C++ object lifetime compatibility.

A new public SDK project-state isolation gate is SHARED by both CNL AEGP builds: requires one non-dirty empty project, no non-root active/project items, no Render Queue items and all host queries available. The dangerous manual-only AEX checks this before consuming user acknowledgments and before touching private registration. Creator invocation count uses static storage rather than capturing a local stack reference into potentially host-retained callback.

CNLNativeVectorHostProbe safe v1 already ran in AE2026 and produced genuine CNL cubic vectors (4), factory getter non-null and exact host version fingerprint, while showing native registration count 0. The NEW safe v2 adds public-project gate data to the TSV and dialog; it has only been COMPILED, not yet tried in AE. Future user test should replace the old safe probe and verify v2's new report. The dangerous AEX is still NEVER run and CANNOT be certified safe.

Native independent owner, Adobe Timeline/Pen controls, BEE evaluator insertion and VectorArt rendering are unsolved and must not be represented by the standalone CNL core or a successful type-registry function call.

## 2026-10-12 — Two new product-level constraints: closed Layer kind, generic editable Stream value/Undo

F-VECTOR-037 (EXP-SHAPE-036) reconstructs the exact native `BEE_Layer::CreateLayerFromType` eight-case dispatch table in both installed AE2025/2026 BEE.dlls. It is integer-bounded to 0..7 and routes to seven hardcoded native C++ constructors (type 6 shares AVLayer; type 4 is VectorLayer). External TDB Stream Creator registration cannot **by itself** create an eighth native Layer kind through this specific factory. This is a substantive narrowing of the new-Layer product route, but does not exclude unstudied extension dispatchers elsewhere.

F-VECTOR-038 (EXP-SHAPE-037) establishes the positive counterpart: native Mask and Vector Shape *reset* operations invoke a single common native helper in each version, which calls `BEE_CmdSetStreamFPVPlus`, `BEE_DoCommand` and host Undo grouping. The generic writer takes `BEE_Layer*` and `TDB_StreamIDPath`, resolves the stream via `BEE_GetStreamWithSpec`, writes using `BEE_SetStreamFPV`, and brackets a native Undo transaction. This is not native Pen drag integration but establishes a usable shared internal writer contract **conditional on obtaining a legal independent editable TDB owner**.

The two findings together change engineering priority. Instead of building a speculative foreign VectorLayer subclass based only on TDB registration, prioritize (1) discovering/creating a real plugin-attached **non-Shape/non-Mask native Contents owner**, (2) proving its `BEE_StreamSpec` resolves to a writable, serialized TDB Stream, (3) tracing AE Pen/Selection to that exact IDPath and its editing callbacks, and (4) locating a native `BEE_VectorArt`/RG source interface that doesn't require `BEE_VectorLayer`. Each is a separate falsifiable experimental gate. The existing CNLNativeVectorCore remains independent typed geometry and can serve as the authored data source once those gates are met, but no native host vector output has yet been created.

EXP-SHAPE-038 records actual user AE2026 read-only probe: Bezier and private factory getter succeeded while the conservative gate refused `active_item_not_root`; the project was also dirty. This has no bearing on the native ownership/render research. No mutating AEX was installed or executed by the researcher. Phase F and the CompNodeAE repository remain entirely out of scope.

## 2026-10-12 — Native derived group creation mechanism recovered (F-VECTOR-044/045/046)

The user-run AE2026 `CNLNativeOwnerAdmission.aex` successfully traversed 186 host streams in 33 groups and performed 198 read-only candidate admission checks. Standard vector/Effect candidates were admitted only at appropriate parent groups; the unregistered CNL independent group was refused in each of 33 tested groups. The user project tree is **not** published; only a sanitized aggregate was saved to AEIG.

The first independently proven *non-null* native dynamic group `CreateEffectGroup` override is `LayerStyleStreamGroupParser`, derived from `BEE::ae::DynamicStreamEffectsParser` by validated x64 MSVC RTTI. Both installed host versions use virtual slot +0xB0 for the creator. The concrete override allocates and constructs a real `BEE_LayerStyleStream::IndLayerStyleStreamGroup` from `TDB_NamedStreamGroup`, supplies two strings and activation metadata, and returns it to the host's `TDB_StreamFactory::RegisterCanonicalInstance` route. Live native Layer Style children in the user host tree provide supporting evidence. Crucially, this is an Adobe *Layer Style* owner, **not** the required independent CNL native vector effect.

The derived parser's actual native startup routine calls `TDB_ScRegisterStreams::Register` 11 times, `TDB_StreamGroup::AddStreamToUILayout` twice, `dvacore::xml::GetParser` once and `TDB_ScRegisterStreams::UnregisterAll` once. TDB.dll confirms `Register` and `UnregisterAll` delegate to the underlying type factory registration/unregistration. Automatic destructor rollback and unload safety are **not proven**. The dangerous disposable AEX remains blocked from in-host execution.

### Next concrete implementation gate

Find an Adobe-supported or fully reconstructed and proven safe **external** equivalent for all four operations: register a plugin-owned compound canonical TDB class; create it under a real non-Shape/non-Mask parent; persist it and resolve its StreamIDPath through BEE; and finally connect native Pen/Undo plus BEE_VectorArt/RenderGraph. These are distinct requirements. The new internal Layer Style implementation is an architectural witness, not permission to call Adobe's private ABI from third-party code.

All experimental work stays in `ShapeLayerAE`; `CompNodeAE` and Phase F integration remain untouched until the user chooses the integration design.

## 2026-10-12 — Layer Style temporary Creator split and BEE bootstrap XML boundary (F-VECTOR-047/048)

A reproducible 2025/2026 code audit resolves the eleven temporarily registered `TDB_ScRegisterStreams` callback objects to their real constructors: **eight `TDB_Stream` leaf-value creators and three concrete native group creators** (`AdvancedBlendingStreamGroup`, `BlendingOptionsStreamGroup`, and `RootLayerStyleStreamGroup`). The separately proven `LayerStyleStreamGroupParser::CreateEffectGroup` constructs dynamic `IndLayerStyleStreamGroup` children. Thus the host's schema build requires multiple distinct native creator contracts.

A two-hop x64 code trace from BEE XML definition initializer to startup and shutdown wrappers establishes that the definition input originates from a **BEE native bootstrap caller** and is forwarded into `dvacore::xml` parsing, while a paired teardown wrapper goes through the unregister branch. This is an internal system initialization route, not yet a usable external AEX plug-in registration interface. No direct third-party Canonical Contents creator, native Pen binding, or BEE_VectorArt renderer was achieved; no private registration was run. Existing experiments and sanitized evidence are recorded in F-VECTOR-047/048 and EXP-SHAPE-047/048. The user's strict Phase F pause and `CompNodeAE` no-edit constraint remain in force.

## 2026-10-12 — Actually compiled effect-owned native CNL document and renderer: F-VECTOR-049 / EXP-SHAPE-049

Major product-path implementation progress, distinct from the proprietary TDB decoder work: `labs/native_vector_document_effect/CNLOwnedVectorEffect.aex` is a freshly compiled 64-bit public Adobe Effect SDK plug-in built directly from standalone CNLNativeVectorCore. It no longer depends on a PICA provider or a native Mask/Shape Layer to own curves. A hidden, real `PF_Param_ARBITRARY_DATA` parameter contains the **independent CNL Group/Path hierarchy archive**. The AEX supports full host storage callback set, including binary FLATTEN/UNFLATTEN and reversible checksum-validated PRINT/SCAN, discrete keyframe interpolation, and an 8bpc antialiased PF_World renderer driven from its own serialized cubics.

Two independently built Windows x64 AEXs, the second from source archived under `experiments/vector-shape/native-owned-vector-effect-lab/`, pass actual compiled effect-entry host mock and PE/PiPL checks, including arbitrary handles and nested two-ellipse rendering from changed documents. Versioned archive is size bounded and rejects corruption; simulated host handle count returns to zero. Actual AE2026 project persistence, in-host rendering and undo still need **user-controlled disposable project validation**.

**DO NOT CONFUSE THIS STAGING FOUNDATION with the final objective:** the stored effect parameter is NOT a native `TDB_NamedStreamGroup` Contents entry; Adobe's own Pen/Selection cannot edit CNL vertices; renderer is CPU PF_World, not BEE_VectorArt/RenderGraph. Phase C true host-native Contents, D native Pen and E native renderer remain open. Private TDB registration still not authorized for runtime. `CompNodeAE` and Phase F remain unmodified. See full F-VECTOR-049, EXP-SHAPE-049 and build receipts.

## 2026-10-12 — Public Effect arbitrary data is already a real FLT/TDB native leaf (F-VECTOR-050)

A two-build FLT.dll machine-code audit located `FLT_ParamArbDataStream`, a real `TDB_DerivedStream<FLT_ParamArbDataStreamTraits>` native host class that backs `PF_Param_ARBITRARY_DATA`. Its native Creator/Clone allocates `0x470` bytes, its DeleteArbDataItem inspects actual `PF_ParamDef`/ValueDesc, and PRINT/SIZE/SCAN handlers recover the parent `FLT_FCSeqSpec`. `FLT_SeqInqParamStream` provides the parent effect parameter-index to native TDB stream lookup. This is a *real interface boundary* between the newly compiled CNL-owned archive AEX and Adobe's native TDB property/parameter backend: CNL no longer has to hypothesize how the host saves an arbitrary Effect value.

However, **the backing FLT stream is a leaf representing the whole opaque archive**, not a new per-CNL-Group/Path TDB Contents subtree and not an AE Pen/Composition Viewer target. F-VECTOR-017/038/039 and 050 therefore leave native vertex editing and BEE_VectorArt output as separate unsolved gates. No private host call, injection or GUI interaction occurred; compnodeae untouched.
