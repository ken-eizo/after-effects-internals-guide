---
status: strong-static-cross-version-with-host-corroboration
last_verified: 2026-10-12
evidence: E2-L + E2-X supporting tree
versions: installed AE2025/2026 BEE.dll; real AE2026 AEGP read-only scan
---

# F-VECTOR-045 — Native dynamic parser has a real derived group creator: LayerStyleStreamGroupParser

## Breakthrough beyond a null base creator

F-VECTOR-043 found `DynamicStreamEffectsParser::EndEffect` appending native child UILayout streams, but its exported BASE `CreateEffectGroup` merely returned nullptr (`xor eax,eax; ret`). We have now recovered the actual MSVC x64 RTTI inheritance path in BOTH BEE versions, including non-first BaseClassArray entries, to locate the concrete derived parser `LayerStyleStreamGroupParser`. Its vtable `CreateEffectGroup` slot **22 (+0xB0)** points to a nontrivial **real object constructor**, not the null base method.

| Host | base creator RVA | derived creator RVA | derived group allocation |
| --- | --- | --- | --- |
| AE2025 | 0xE3960 | 0x2F6300 | 0x2A0 bytes |
| AE2026 | 0xE9D20 | 0x2FEF50 | 0x270 bytes |

The derived creator calls `U_MemTrackedObject::operator new` and the native `TDB_NamedStreamGroup` constructor with actual `TDB_MatchName` and global factory. It then assigns the **`BEE_LayerStyleStream::IndLayerStyleStreamGroup` class vtable** (AE2025 RVA 0xEE88E0; AE2026 RVA 0xF41EB8), constructs two native string members (offsets +0x260/+0x280 in 2025 and +0x230/+0x250 in 2026), calls `ShowActiveSwitch(true)`, `SetActive(false)`, and returns the allocated group (nullptr only on allocation failure). Class layout and allocation differ across releases and are not stable ABI.

In the exact compiled `EndEffect` caller, slot +0x98 is `AllowMultipleEffects`. Its result gates the call to slot +0xB0; the returned group pointer is immediately forwarded as an argument to `TDB_StreamFactory::RegisterCanonicalInstance`. Thus an actual native construction hook flows directly into a canonical registration path. The slot +0xA0 is consulted after registration for additional hidden-state handling.

The RTTI scan found two verified vtables inheriting this base in the examined BEE binaries: the native base itself and `LayerStyleStreamGroupParser`. This is scoped to the BEE binary's native RTTI representation; it does NOT exclude subclasses defined in other DLLs or created through undocumented loaders. Two real .text RIP-relative references per version instantiate or initialize the derived vtable. The large caller is tied to native canonical registration and XML parser setup (F-VECTOR-046).

## Host corroboration and product meaning

AE2026 `CNLNativeOwnerAdmission` observed `ADBE Layer Styles` and genuine subgroups named `dropShadow/enabled`, `innerShadow/enabled`, etc. That live owner hierarchy is consistent with the native Layer Style constructor and parser route, though it does not prove every existing item passed through this precise creation call during the observed launch.

**Critical distinction:** This proves that Adobe uses a legitimate derived native group parser to construct real nested `TDB_NamedStreamGroup` objects. It does NOT show that a third-party Effect can register a new parser subclass, that the group is a CNL editable Bezier owner, that its streams are independently writable through native Pen, or that it provides VectorArt/RenderGraph output. Do not substitute Layer Style or Shape/Mask carriers for the final CNL goal.

## Evidence

- `datasets/ae-bee-derived-layer-style-parser-rtti-2025-2026.json`
- `datasets/ae-bee-dynamic-effect-group-creation-chain-2025-2026.json`
- `datasets/ae-bee-layer-style-parser-real-group-2025-2026.json`
- `datasets/ae-bee-layer-style-parser-creation-callers-2025-2026.json`

Scripts are copied to `experiments/vector-shape/probe-src/tools/` including `trace_dynamic_parser_derived_rtti.py`, `verify_layer_style_parser_real_group.py` and `verify_bee_dynamic_effect_group_creation_chain.py`. All tests purely static; no private Adobe code called by the research tools.
