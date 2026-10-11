---
status: strongly-supported-static-two-native-binaries
last_verified: 2026-10-12
evidence: E2-L + H
versions: pinned AE2025/2026 TDB.dll and FLT.dll; SDK25.6
---

# F-VECTOR-042 — Effect canonical UILayout construction and class-specific stream population

## What is new

F-VECTOR-039 identified the top-level FLT Parade RTTI gate, and F-VECTOR-040 already proved that existing Effect children pass the inherited `TDB_StreamGroup::CanStore` whitelist. This follow-up independently crosschecks its native vtable/IAT dispatch and, more importantly, traces **how the whitelist's Canonical UILayout is constructed** by the virtual layout population stage and derived effect group classes.

In both native AE2025/2026 releases, the `FLT_FCSeqSpec` vtable for its `TDB_NamedStreamGroup` subobject has `CanStore` at virtual index 56 (+0x1c0). Resolving that actual vtable entry finds an FLT.dll `FF 25` import thunk leading specifically to `TDB.dll!TDB_StreamGroup::CanStore(TDB_MatchName const&)`. This is **not** a guessed shared method based on inheritance names. The relevant FLT stub RVAs are `0x9fe83` (2025) and `0xa242f` (2026), and the native IAT entries resolve to the same decorated TDB symbol.

## The source admission predicate

The exact native `TDB_StreamGroup::CanStore` code (TDB 2025 RVA `0x35e10`, 2026 RVA `0x36880`) reads a shared canonical list through `this+0x210` and `this+0x218`, scans the list, calls the native `TDB_MatchName::operator==` on entries and returns an inequality-derived boolean indicating whether a matching element was found. This is an allowed-child **canonical layout membership predicate**, not the prefix grammar used by the existing Vector Contents group.

Therefore a new string like `CNL Native Independent Group` cannot be made a legitimate child of the effect merely by being registered somewhere in the global TDB creator map. The parent must actually have the new child's canonical stream identity in its allowed list. Conversely, the predicate itself is not hardcoded to a Shape/Mask/Effect-specific list of names.

## Canonical layout construction is virtual and class-specific

`TDB_StreamGroup::SetupCanonicalLayout` in the 2026 TDB binary constructs an owned collection, invokes virtual slot +0x1c8 (`FillInCanonicalUILayout`) on the group, passes the collection to `TDB_StreamFactory::SetupCanonicalLayoutForSeperatedDimensions`, then assigns it via `TDB_StreamGroup::SetUILayout`. Both installed versions have this sequence.

The base concrete `FLT_FCSeqSpec::FillInCanonicalUILayout` is a one-instruction `ret` in both 2025 (`0x659a0`) and 2026 (`0x67a70`). That does **not** mean real effects have no parameters. It means this specific override does not statically fill the Canonical UILayout in the manner that other derived host groups do.

For contrast, `FLT_EffectBuiltInParams::FillInCanonicalUILayout` calls imported `TDB_StreamBase::GetCanonicalStream` **3 times in AE2025 and 4 times in AE2026**; `FLT_CompoundEffect::FillInCanonicalUILayout` calls it twice in each examined version. Those derived classes demonstrably supply real native canonical child streams through a separate code path. How ordinary plugin `PF_ParamDef` definitions are attached and preserved inside `FLT_FCSeqSpec` is a separate unsolved question.

## What this enables and what it DOES NOT prove

The real independent Effect-owned Contents obstacle can now be phrased narrowly: establish a host-recognized, persistent `FLT_FCSeqSpec` object with an authenticated child canonical identity list containing the plugin's vector-group type, then instantiate that child through TDB under valid lifetime, serialization, selection and Undo. The generic `BEE_GetStreamWithSpec` and `BEE_CmdSetStreamFPVPlus` routing studied in F-VECTOR-038 would become relevant only after that attachment exists.

**None of the following is demonstrated:** third-party extension of the canonical UILayout; safe foreign `FLT_FCSeqSpec` subclass; writable host-owned independent vector child; AE Pen vertex editor selection; or direct `BEE_VectorArt` / RG output from an effect. Native owners, cache policies and unload lifetimes remain opaque. The older high-risk `CNLPrivateTDBDisposable.aex` is still not authorized for live testing.

The public SDK `PF_Param_PATH` explicitly references paths/masks/shapes already on the effect's layer (AE_Effect.h), so it is NOT a plugin-owned native Bezier object and does not satisfy the goal. `PF_Param_ARBITRARY_DATA` can own a value with host callbacks but does not provide a native Pen/VectorArt interface by itself.

## Reproduction

No private Adobe function was called. Code and complete native instruction evidence:

- `datasets/ae-flt-fcseqspec-nested-schema-2025-2026.json`
- `datasets/ae-flt-fcseqspec-child-canstore-vtable-2025-2026.json`
- `datasets/ae-flt-fcseqspec-nested-admission-verified-2025-2026.json`
- `experiments/vector-shape/probe-src/tools/audit_flt_fcseqspec_nested_schema.py`
- `experiments/vector-shape/probe-src/tools/audit_flt_fcseqspec_child_canstore_vtable.py`
- `experiments/vector-shape/probe-src/tools/verify_flt_nested_contents_admission.py`

`EXP-SHAPE-043` records the additional cross-version canonical setup evidence. This extends the earlier Effect child whitelist analysis in F-VECTOR-040; related F-VECTOR-039, F-VECTOR-038 and F-VECTOR-017. This remains a Phase A–E study; Phase F CompNodeAE integration and edits are prohibited.
