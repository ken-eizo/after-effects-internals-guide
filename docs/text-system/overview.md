---
status: active
last_verified: 2026-09-15
---
# Text System

AEIG treats text as its own subsystem rather than only a layer type.

## Questions
- How are source text, paragraph/box geometry, font identity, variable-font axes and style runs represented in persistent/project state?
- Where is text shaping performed, and which state participates in render/cache identity?
- How do Text Animators map onto the Property/Stream tree and evaluation dependencies?
- What changes when expressions mutate `TextStyle` values?
- Which parts of glyph layout are time-invariant and which invalidate rendered frames?
- How do font substitution and missing fonts affect determinism across machines?

## Evidence surfaces
Scripting `TextDocument`/style APIs; AEGP stream hierarchy; AEP/AEPX differential files; expression style API; fixed-issue history; font/module inventory; pixel and cache-invalidation experiments.

A 26.5 fixed issue explicitly ties expression-driven text-style changes to frame-cache invalidation, making text a useful bridge between expression evaluation, typography state and render identity.

## Runtime identity evidence
AE 2025 `TXT.dll` exposes a document-level render GUID lifecycle (`GetRenderGuid`, seed GUID, explicit invalidation and mix-in), while `TXT_Font` contributes to a Murmur3-based GUID mixer. BEE/TDB independently expose time-cache validation for text-document and variable-font-axis streams and a text-layer document render GUID path.

This supports a layered model in which text layout/font semantics are normalized inside the TXT subsystem and then participate in the broader BEE render identity. It is stronger than treating Source Text as one opaque property blob.

See `F-TEXT-002-text-render-guid-and-font-identity.md`. The native [Project Missing-Font Metadata Lifecycle](project-missing-font-data-lifecycle.md) chapter documents `BEE_Project::AddMissingFont`, the `TXT_UsedFontData` vector and its destruction order relative to Project Undo history (F-VECTOR-104).

## Public object model is only a projection of the text document
Scripting exposes `TextDocument`, but many convenience properties such as `fontSize`, `fontStyle` and font-path/object access report only the first character's state. Setting some of them applies the value to all characters.

Therefore a heterogeneous text layer cannot be faithfully modeled as one flat style record. Style runs, paragraph state, font runs, box/path geometry and animator/expression state are separate dimensions even when scripting presents convenience accessors.

`TextDocument.fontObject` became available in AE 24.0, giving a stronger font object boundary than a PostScript-name string alone, but it still does not expose every internal font/glyph resource represented in `TXT.dll`.

## Render identity and invalidation
Local `TXT_Doc` render-GUID surfaces plus BEE text stream traits support a model where text identity is mixed from normalized document/style/font/layout state before entering broader layer render identity.

Adobe's 26.3 fixed issues provide independent product evidence: changes made through the expression style object previously failed to invalidate existing cached frames correctly and were fixed. That bug class is exactly what a missing text/expression dependency edge would look like at the observable level, though AEIG does not claim the private root cause.

Variable-font behavior is also version-sensitive. 26.0 fixed a case where expressions creating variable-font animations slowed performance and created extra font-style menu entries, showing that font-axis/style materialization can affect both evaluation cost and UI/runtime state.

## Text Animator and expression boundary
Text Animators are property/stream structures layered over the document; expressions can additionally synthesize `TextStyle`/Source Text values. A correct dependency model must therefore include both authored text-document state and evaluated expression/animator state at time `t`.

Do not key text caches solely by source string or font name. Two identical strings can differ by font resource, style runs, variable axes, paragraph/layout geometry, animator state, language/shaping context or substitution state.

## Failure patterns
- read only first-character scripting properties and assume uniform styling;
- serialize only font PostScript name and lose variable-axis/substitution identity;
- change expression-driven style without invalidating text-render identity -> stale cached frame;
- compare text output across machines without recording exact font file/version/substitution state;
- treat `sourceRectAtTime()` bounds as a pure string metric while ignoring animators, paragraph box and glyph layout;
- assume UI font-menu entries map 1:1 to stable render resources.

## Controlled text corpus
Use a small matrix containing mixed fonts, ligatures, combining marks, RTL text, variable-font axes, paragraph/point text, missing-font substitution, text-on-path and expression-driven `TextStyle` changes.

For each mutation record TextDocument/script-visible state, TXT/BEE render GUID traces where available, bounds, glyph/output hashes, cache reuse and save/reopen behavior.

A particularly valuable test keeps the final rendered glyphs visually identical while changing font resource or style history; this distinguishes semantic identity from accidental pixel equality.

## Unknown frontier
Still unresolved: exact shaping library/ownership boundaries inside current TXT runtime, glyph-run cache key composition, relationship between TXT document render GUID and BEE text-layer GUID, persistence format of variable-font design vectors, and which language/font environment dimensions participate in deterministic identity.

Related: `docs/state-model/streams-properties.md`, `docs/expression-engine/architecture.md`, `docs/evaluation/dirty-invalidation.md`, `F-TEXT-002`.
