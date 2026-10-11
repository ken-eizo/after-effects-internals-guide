---
status: research-active
last_verified: 2026-10-11
evidence: E0-S + E0-H + E2-L + compiled-PE + E2-X + H
versions: AE2025/AE2026, SDK25.6
---
# CompNodeAE — Research-to-Product Vector Frontier

## Mission

The primary ambition is **an ordinary After Effects effect that is itself a native editable vector producer**. The user must be able to use AE's normal Pen and Selection tools, see a true structured Timeline Contents hierarchy belonging to that effect, evaluate its Bezier / Group / Fill / Stroke / Filter structure, and have the production AE Shape renderer consume its vector result directly. Do not substitute a separate native Shape Layer, script-populated paths, a Drawbot overlay, a PF_World raster or topic-group parameters as a claim of completion.

The program also has **independent product opportunities** using exposed Adobe-supported interfaces. Research should always answer: which specific new user workflow could a plug-in developer ship, what bridge is still missing, and what explicit test would falsify the feature?

## Opportunity 1 — Vector Geometry Bus for plug-ins (near-term, public SDK substrate)

**What users could do:** Place a procedural CompNodeAE effect that produces mathematically precise Bezier geometry, then let another separately developed CNL-aware effect consume the same control points for deformation, outlining, boolean operations, stroke synthesis, path instancing, motion paths or export. No intermediate image texture is required **between these two aware plug-ins**. This unlocks a developer SDK in which source, operator and consumer extensions exchange geometry instead of repeatedly rasterizing/edge-detecting pixels.

**What we have:** Adobe's distributed Sweetie AEGP and Checkout effect independently demonstrate producer-side AddSuite and consumer-side suite acquisition. We wrote two original, independently compiled AMD64 .aex modules in ShapeLayerAE/labs/vector_bridge: VectorBridgeAEGP exports a procedural double-precision four-cubic path; VectorBridgeConsumer retrieves those native numeric curves. PiPL/exports/build PE validation passed. **The user then installed them in AE2026 and showed `PICA suite: connected`, `Native Bezier segments: 4; first X: 100.00` in the actual Effect About dialog (E2-X).** The original Consumer had version/OutFlags mismatch dialogs and MFR warning; a corrected Consumer was rebuilt, the compiled PiPL metadata was inspected, and a two-AEX standalone mock geometry exchange passed. **The corrected Consumer has not yet been retested in AE.** See F-VECTOR-020.

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

**The more radical hypothesis:** Discover whether the SVG importer can attach an authentic Root Vectors tree to an independently owned object that is not a native Shape Layer. This would address one owner/serialization boundary but still needs editor and renderer proofs.

## Priorities after this session

1. **Next high-confidence test**: The original pair **did connect in AE2026**; replace only the Consumer with the corrected, PiPL-aligned build after closing AE. Confirm the old 25::16 mismatch dialogs and the MFR performance notice do not appear; the Effect About must still report `PICA suite: connected` and four cubic Beziers. Then test frame-time geometry and teardown/MFR. Do not hot-replace DLLs in a running host.
2. **Product v1**: Add immutable per-instance geometry snapshots and a CompNodeAE-internal typed path API; test under MFR and random-access rendering. Ship only when dependencies and lifetimes are correct.
3. **Private moonshot**: Reconstruct the caller/owner preconditions of BEE_PasteSVGIntoComp and the exact BEE_VectorLayer/Effect stream-owner acceptance policy. Trace OriginInfo -> native hit-test -> FindEditableStream dataflow.
4. **High-risk ABI lab**: Version-pinned standalone operator interface and refcount construction in a non-AE mock, then gated reversible registration in an empty throwaway AE instance. Registration can run creators *during registration*, so never use dummy pointers.
5. **Feature exploration**: Build a concrete vector-node demonstration (boolean/instancer/path morph) consuming CNL_VectorCubicV1 **without** pixels; implement real consumer data semantics before native editor parity.

## Product-report template for all subsequent vector-research sessions

Each session should explicitly state:
- **Finding and evidence grade** (SDK-confirmed, local binary static, in-AE observed, hypothesis).
- **What a creator can implement today** without a new unsupported private ABI.
- **Large potential user-facing features**, with examples of real creative workflows and the user-visible benefit.
- **Gap to genuine native host parity** and which capabilities are not yet proven.
- **Next runnable experiment and exact success/failure criteria**.
- **AEIG experiment/result paths, plugin source/build state, build/test status and Git commit**.

Related findings: F-VECTOR-013 through F-VECTOR-020. New observed receipt: datasets/ae-pica-vector-bridge-two-plugin-build-receipt-2026.json. Public source references: local Adobe SDK 25.6 Sweetie/Checkout; https://ae-plugins.docsforadobe.dev/effect-details/working-with-paths/ ; https://helpx.adobe.com/after-effects/desktop/import-files/import-svg-files/import-svg-files.html .
