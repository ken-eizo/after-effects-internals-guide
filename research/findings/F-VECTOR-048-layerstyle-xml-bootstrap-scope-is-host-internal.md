---
status: cross-version-static-verified-scoped-negative-external-hook
date: 2026-10-12
evidence: E2-L
versions: pinned installed AE2025/26 BEE.dll
---

# F-VECTOR-048 — Layer Style XML parser and temporary type registration are embedded in BEE bootstrap/teardown

## Confirmed source and entry chain

F-VECTOR-043 found a real `DynamicStreamEffectsParser::EndEffect` native Canonical UILayout append. F-VECTOR-045/046 then located Adobe's genuine derived `LayerStyleStreamGroupParser` native group constructor, eleven scoped type registrations, XML parser use and explicit registration removal.

We now traced the **complete direct native wrapper context up to the BEE bootstrap caller**, not merely the parser itself. In AE2025, the XML type initializer is at `0x2FBB60`, startup wrapper `0x28FA80`, containing bootstrap `0x36DD90`, teardown wrapper `0x2959E0`, and teardown bootstrap `0x36DEF0`. AE2026 analogues are `0x304640`, `0x298CB0`, `0x3787B0`, `0x29E630`, `0x378910`.

The setup wrapper copies its incoming `RCX` definition argument into `RDX`, sets `CL=1`, and calls the parser initializer. The BEE initializer's entry saves the definition pointer from `RDX` and later uses that exact incoming value for a local string object that is passed to `dvacore::xml::GetParser`'s returned parser's virtual parse method `+0x18`. Therefore the **definition input is supplied by an upper caller**, not hard-coded as an XML literal in this particular initializer body. Where that upper caller obtains the data and whether it is an external file, resource, or engine-generated definition remain unproved.

The teardown wrapper sets `ECX=0, EDX=0` and tail-jumps into the same initializer, which switches to the explicit unregister route. The BEE bootstrap starts several other native registry subsystems before/after Layer Style setup; shutdown calls the paired deregistration wrappers in the opposite direction. This is strong evidence of a **native initialization/teardown lifecycle**, not a normal PF_Effect plugin parameter callback API.

## Product consequences

Even though this internal parser accepts data from its own caller, that is not proof an external AEX can supply custom XML, subclass `DynamicStreamEffectsParser`, register a plugin-owned compound TDB type, or safely leave a host-owned CNL object alive across factory cleanup and plugin unload. The observed parser handlers visibly cover native effect-like scalar/color/point categories; no new native Bezier/path handler has been proven.

Thus native Layer Style dynamic group creation is a powerful *internal architecture witness* but presently a **closed third-party extension boundary** under examined evidence. Treat that phrase as "no supported externally callable boundary established", **not** as a global proof that no undiscovered mechanism exists.

An executable CNL effect can still use public SDK to own a custom serialized vector document, but that would not itself meet the user-requested *native Contents + AE Pen + BEE_VectorArt* gates. We must not mislabel any such fallback as full completion.

## Reproduction

- `datasets/ae-layerstyle-xml-parser-initializer-xrefs-2025-2026.json`
- `datasets/ae-layerstyle-xml-parser-two-hop-bootstrap-2025-2026.json`
- `datasets/ae-layerstyle-xml-scope-lifecycle-verified-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/trace_layerstyle_xml_parser_entry_callers.py`
- `experiments/vector-shape/probe-src/tools/trace_layerstyle_xml_parser_two_hop_boundary.py`
- `experiments/vector-shape/probe-src/tools/verify_layerstyle_xml_scope_lifecycle.py`

All results are pinned two-version PE evidence, offline. No dangerous `CNLPrivateTDBDisposable.aex` execution, no host GUI, no `CompNodeAE` changes.
