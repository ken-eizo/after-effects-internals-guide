---
status: research-active
last_verified: 2026-10-12
evidence: E0-S + E0-H + E2-L + compiled-PE + E2-X + H
versions: AE2025/AE2026, SDK25.6
---
# CompNodeAE — Research-to-Product Vector Frontier

## Mission

The primary ambition is **an ordinary After Effects effect that is itself a native editable vector producer**. The user must be able to use AE's normal Pen and Selection tools, see a true structured Timeline Contents hierarchy belonging to that effect, evaluate its Bezier / Group / Fill / Stroke / Filter structure, and have the production AE Shape renderer consume its vector result directly. Do not substitute a separate native Shape Layer, script-populated paths, a Drawbot overlay, a PF_World raster or topic-group parameters as a claim of completion.

The program also has **independent product opportunities** using exposed Adobe-supported interfaces. Research should always answer: which specific new user workflow could a plug-in developer ship, what bridge is still missing, and what explicit test would falsify the feature?

## Opportunity 1 — Vector Geometry Bus for plug-ins (near-term, public SDK substrate)

**What users could do:** Place a procedural CompNodeAE effect that produces mathematically precise Bezier geometry, then let another separately developed CNL-aware effect consume the same control points for deformation, outlining, boolean operations, stroke synthesis, path instancing, motion paths or export. No intermediate image texture is required **between these two aware plug-ins**. This unlocks a developer SDK in which source, operator and consumer extensions exchange geometry instead of repeatedly rasterizing/edge-detecting pixels.

**What we have:** Adobe's distributed Sweetie AEGP and Checkout effect independently demonstrate producer-side AddSuite and consumer-side suite acquisition. We wrote two original, independently compiled AMD64 .aex modules in ShapeLayerAE/labs/vector_bridge: VectorBridgeAEGP exports a procedural double-precision four-cubic path; VectorBridgeConsumer retrieves those native numeric curves. PiPL/exports/build PE validation passed. **The user then installed them in AE2026 and showed `PICA suite: connected`, `Native Bezier segments: 4; first X: 100.00` in the actual Effect About dialog (E2-X).** The original Consumer had version/OutFlags mismatch dialogs and MFR warning; a corrected Consumer was rebuilt, the compiled PiPL metadata was inspected, and a two-AEX standalone mock geometry exchange passed. **A later user screenshot now confirms the corrected Consumer in real AE2026 again displays PICA suite: connected and four native cubic segments.** Hash inspection confirms the installed Consumer is the rebuilt fixed binary. A MFR stress test and renderer graph dependency test remain outstanding. See F-VECTOR-020.

**What is needed for a shippable feature:** Explicit producer identity, project/comp/effect-instance lifetime, time/subframe/quality/coordinate space, data snapshots, client-owned allocation contracts, suite-load order, MFR concurrency, dependency tracking/cache invalidation, inter-process and CPU/GPU readback policy. PICA alone does not register native AE rendering dependencies. Producer and consumer can be jointly implemented inside CompNodeAE to control those contracts before opening them to third parties.

**What this is not:** Not a new AE-native editable Contents type, not Pen-tool targeting and not an Effect SDK vector result channel. It is a new **cross-plug-in contract** on Adobe's supported PICA transport.

## Opportunity 2 — Native-editable path inputs without separate Shape Layers (near-term, limited)

**Potential user workflow:** Apply CompNodeAE to a normal solid or footage layer. Draw ordinary native **mask paths** on that same layer with the AE Pen tool. Use the mask path as the vector input, process it through a procedural non-raster node chain and offer the computed geometry to other CompNode-aware plug-ins over the Vector Geometry Suite.

**Supported basis:** SDK 25.6 AE_Effect.h describes PF_Param_PATH as a way to access the host layer's mask/path/shapes, and PF_PathQuerySuite1 / PF_PathDataSuite1 are provided. This is a host-owned editable path input; it does not make the effect own editable output paths. The eventual normal AE effect composite remains PF_World unless a separate vector handoff is realized.

**Impact:** Creative studios could use built-in Pen handles for data entry while keeping downstream procedural operations in an editable Bezier domain, not silhouettes extracted from rendered masks. This is *not* the user's full native effect-owned Contents objective and must be labeled a constrained input solution.

## Opportunity 3 — Native BEE vector operator plug-ins (high-risk, private ABI)

**If proven:** Independently authored geometric operators could appear inside the regular AE Contents hierarchy and run before the production vector renderer. The user could add advanced boolean, offset, variable-width strokes, nonlinear Bezier warps, path-based particle paths, formula-driven branching, procedural lettering, constructive geometry, topology-preserving morphs and other operators with host-native preview and resolution-independent fidelity.

**Real internal evidence:** AE2025/2026 each register 20 MatchName-keyed polymorphic BEE_VectorStream operators in a **separate** evaluator registry from TDB StreamFactory. Every operator has a known C++ RTTI reference-counted family and a virtual mode dispatcher at vtable+0x18; 9 Group/Shape/Graphic types consume mode 0, 11 Filters use mode 1. TDB registration eagerly creates stream instances. All private registry ABI and destructor/canonical invariants remain unsafe for external registration without an isolated test.

**Limit:** Even if registered, this may work *only under an existing native Shape Layer*. It would be an impressive new product capability but still not the independent ordinary-effect objective.

## Opportunity 4 — True effect-owned native Contents, AE Pen handles and vector output (moonshot)

**The breakthrough users would experience:** A normal Effect Controls/Timeline effect turns into an editable vector authoring and computation surface. Users draw or select points with AE's **own** Pen and Selection tools, edit real Group/Path/Stroke/Fill/Transform children in the native Timeline, and stack arbitrary CompNodeAE nodes that return geometry—not pixels. Downstream compatible effects and the host's own BEE/AGM production renderer would receive true vector geometry. A finished motion design could remain mathematically resolution-independent until final composite. The old distinction "only Shape Layers produce host-native editable vector geometry" would change.

**Verified host constraints:** Generic BEE_Selection::SelectStream operates on BEE_StreamSpec(BEE_Layer*, TDB_StreamIDPath). The native selection-related function bodies actually call IsPathOrChildSelected, FindEditableStream and GetCanonicalStream while reconstructing hierarchical IDs in both versions. The native Repeater evaluation stamps synthetic OriginInfo indices; Path/Rect/Ellipse generators create native CAIMBezierPath/VectorArt and stamp authored StreamIDPath. This establishes important host-internal building blocks.

**Still missing:** An external owning BEE layer/effect with legal TDB indexed Contents, a type creator + renderer evaluator, a public/private stable registration path, editor hit-test and drag-to-authored-stream binding, project serializer, undo, renderer invalidation and host lifecycle. These are separate blockers; none have been solved by an external plug-in. This project is high-risk research, not a promised feature.

**Proof gates:** Independent plugin-defined Contents without a native Shape Layer; user-created children survive Undo + Save/Reopen; AE native Pen tool recognizes the plugin's own path; edits update source geometry; native BEE VectorArt participates in RG/AGM output; coherent cache/MFR behavior across versions. A mock overlay or a duplicate Shape Layer **fails** the gate.

## Opportunity 5 — SVG-to-native-vector bridge (2026, useful fallback only)

**Practical feature:** CompNodeAE could export internally computed Bezier/Fill/Stroke trees to SVG and offer an explicit **Bake to Native Shape** command through AE's supported SVG import/paste workflow. This gives users real editable Shape Layer content quickly, often higher quality than raster intermediates, and may preserve more group semantics in AE26+. It is a conversion/bake feature and does not satisfy the requirement that the effect itself remain a live native vector owner.

**New native lead:** The installed AE2026 BEE_PasteSVGIntoComp(BEE_Layer*, ..., shared_ptr<ScSVGParse>, ...) directly builds a TDB_StreamIDPath from StreamName_ROOT_VECTORS_GROUP, uses BEE_Layer mutation-suppression scopes, and AGM transform ports. Its generic BEE_Layer* parameter suggests an owner experiment but proves **neither** non-Shape-Layer acceptance nor safe private API access.

**Native owner gate now resolved negatively for this command path:** F-VECTOR-022 traces the true BEE_CmdPasteSVGIntoLayer callback. It builds ROOT_VECTORS_GROUP and explicitly calls TDB_StreamGroup::FindStream; if the native root is missing, it branches to cleanup and does NOT invoke BEE_PasteSVGIntoComp. A generic BEE_Layer* formal parameter is therefore NOT a shortcut for bootstrap. The new radical hypothesis is to create a legitimate independent host-owned native Root Vectors tree BEFORE import, and separately prove Timeline/editor/renderer lifecycle.

## Priorities after this session

1. **Host regression**: The corrected AEX hash matches the installed copy, and actual AE2026 screenshot again reports PICA suite: connected and four native Bezier segments. Next test actual concurrent-frame/MFR rendering, teardown/restart, and real per-instance geometry; no automatic host render-dependency is implied.
2. **Product v1**: Add immutable per-instance geometry snapshots and a CompNodeAE-internal typed path API; test under MFR and random-access rendering. Ship only when dependencies and lifetimes are correct.
3. **Private moonshot**: The SVG importer callback is proven to require pre-existing ROOT_VECTORS_GROUP (F-VECTOR-022). Next trace the exact *owner constructor* and canonical TDB lifecycle, find where an AV Layer/Effect owner could legitimately register a nonstandard root without a native VectorLayer, and then trace OriginInfo -> editable hit-test -> FindEditableStream and renderer registration.
4. **High-risk ABI lab**: Version-pinned standalone operator interface and refcount construction in a non-AE mock, then gated reversible registration in an empty throwaway AE instance. Registration can run creators *during registration*, so never use dummy pointers.
5. **Feature shipped as prototype**: A new C++ VectorBridgeToSVG consumer has actually loaded the compiled AEGP, consumed CNL_VectorCubicV1 and generated a 28-path / 112-cubic procedural SVG rosette without pixels. Two frame times were validated. Next import that SVG in AE2026 and compare native path/point/group fidelity, then advance beyond standalone global-service demo into per-instance effect-aware geometry.

## Product-report template for all subsequent vector-research sessions

Each session should explicitly state:
- **Finding and evidence grade** (SDK-confirmed, local binary static, in-AE observed, hypothesis).
- **What a creator can implement today** without a new unsupported private ABI.
- **Large potential user-facing features**, with examples of real creative workflows and the user-visible benefit.
- **Gap to genuine native host parity** and which capabilities are not yet proven.
- **Next runnable experiment and exact success/failure criteria**.
- **AEIG experiment/result paths, plugin source/build state, build/test status and Git commit**.

Related findings: F-VECTOR-013 through F-VECTOR-023. New observed receipt: datasets/ae-pica-vector-bridge-two-plugin-build-receipt-2026.json. Public source references: local Adobe SDK 25.6 Sweetie/Checkout; https://ae-plugins.docsforadobe.dev/effect-details/working-with-paths/ ; https://helpx.adobe.com/after-effects/desktop/import-files/import-svg-files/import-svg-files.html .


## 2026-10-12: first actual native editing adapter, not native Effect Contents (E0-H, compiled)

A new independent AEGP uses the already-confirmed PICA procedural cubic geometry to create a **real editable AE native Mask Path** on the user-selected ordinary AV Layer, with four exact cubic vertices and tangent handles. An opt-in Mask NONE mode permits native Pen edit while leaving layer pixels alone. Another explicit Mask ADD command would engage AE's built-in Mask compositor rather than our own PF_World rasterizer. A third read-only command compares root stream MatchNames, useful for locating the ownership difference between Mask Parade and Root Vectors Group.

**Compiled and static-verified only; not installed/tested in actual AE in this session.** This is an intermediate, host-standard path authoring integration, not independent effect-owned Contents, native Shape evaluator or direct BEE/AGM vector output. See Finding F-VECTOR-024, EXP-SHAPE-022 and the standalone native-editable-path-lab. If user confirmation succeeds, compare selected native Mask/Shape identities, native Pen tools and live mask rendering to design a next research probe for independent TDB owner registration.

User-facing consequence of a successful host test: a CompNodeAE companion AEGP could publish code-generated curves as normal-layer **native editable mask geometry** which users change with familiar Pen handles, native project saving and standard mask compositing. An actual new Shape-like effect remains the moonshot.


## 2026-10-12 — Hard boundary of the research (user clarification)

A true CompNodeAE native vector product cannot delegate essential creation/ownership/editability/renderer contracts back to a built-in Mask or Shape Layer. Such experiments can be useful controls, but success requires a new plugin-controlled native source class and registered host behavior.

The newest native vtable audit establishes a concrete owner-specific render requirement: BEE_AVLayer and BEE_VectorLayer override Rasterize2DGraph in the same virtual slot, whose position changed from +0x758 (AE2025) to +0x770 (AE2026). VectorLayer has distinct native Create allocation/constructor, GetLayerType 4, default type magic 0x05192004, BEE_CompItem/Project command ownership and TDB stream registration. This is **a major architecture finding, not proof of third-party plug-in support**.

**Large future product consequence if solved:** plugins could define wholly new AE-native editable vector types — not a fake Shape Layer, not Mask, not raster — with unique path filters, procedural geometry as persistent native Contents, AE's actual Pen and Selection handles, and production RG/AGM rendering. It would allow visual coding languages to return an authorable vector object rather than only a composited pixel image.

Evidence: [Independent Native Vector Objects](independent-native-vector-owner-research.md), F-VECTOR-025, H-SHAPE-007, EXP-SHAPE-023. Remaining highest-risk gate is a truly registered independent native Stream Creator/owner with a safe, complete, version-pinned ABI and no host process patching.


## Native vector ownership product engineering (2026-10-12)

A first practical future plugin backend exists as a compiled CNLNativeVectorCore DLL with independent typed Contents and cubic geometry, stable 64-bit identities, deterministic CNL archive, clone and C ABI. It avoids Mask/Shape storage and does not materialize PF_World output. Passing native compiled tests and Python ctypes proves the module works externally, not that Adobe recognizes it.

The large potential product breakthrough remains third-party host-owned, AE-native vector objects: new editable path source, native indexed Contents, AE Pen selection, CNL-defined geometry/operators and native BEE_VectorArt/RG output. The current library is a source-side dependency, not the breakthrough. Remaining integrations require a private TDB registrar, Timeline owner, BEE evaluator registry and renderer dispatch with exact version-pinned lifetime. Details F-VECTOR-027/028/029 and EXP-SHAPE-025/026.


## From CNL core to native host registration: staged experimental plugin binaries (2026-10-12)

Two source-only AEIG labs now build AEGP binaries at the user's local ShapeLayerAE tree: the safe CNLNativeVectorHostProbe.aex (read-only version/export check plus procedural geometry already compiled into an AEGP), and a separate **unsafe, never-tested** CNLPrivateTDBDisposable.aex (requires exact version hash and explicit disposable-user ACK, attempts one native new MatchName registration and then best-effort unregister). Neither is a native AE vector result today.

This separation protects ordinary iteration: only the first AEX should be used for initial AE validation. A nominally successful private TDB registration would prove factory acceptance but still require a new independent AE Contents owner, selection/Pen handler, BEE evaluator and native RG output. The huge product vision is wholly new code-defined, AE editable/animatable host-native vector types and operators; that vision is **not yet implemented**.

For the source and objective evidence see F-VECTOR-030..033, EXP-SHAPE-027..030. Do not replace this difficult native-host contract with regular Masks, Shape Layers, Drawbot overlays or a PF_World CPU/GPU raster effect.


## Compile-time exact-TDB ABI evidence and isolated test protection (2026-10-12)

The standard Shape/Mask-free independent CNL vector core is now linked into a real compiled AEGP. An exact ABI code review caught an experimental native Creator std::function mismatch (fifth unsigned int was actually bool). A native-class-typed MSVC COFF symbol now matches the Adobe private Registrar callback template signature byte-for-byte for AE2025 and AE2026. This materially improves the registration experiment's rigor but says nothing yet about safely adding AE native Contents.

The read-only AEX v2 reports a shared public-SDK empty-project predicate; the gated private AEX uses the same predicate before any private calls. Neither revised binary has undergone an in-host AE UI test, and the dangerous AEX has never registered any host type. Full real-world safety cannot be guaranteed with private APIs. The product target remains independently owned, persistent native vector Contents with native Pen and BEE VectorArt output, all NOT yet achieved. See F-VECTOR-034, EXP-SHAPE-031/032.
