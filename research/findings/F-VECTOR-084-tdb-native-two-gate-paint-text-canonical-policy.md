---
date: 2026-10-14
status: PASS 2/2 AE2025/AE2026 BEE/TDB native two-gate child grammar; PASS TextAnimator/TextSelectors common mechanism
evidence: E2-L original SHA-pinned BEE/TDB binaries, complete dumpbin exports, Capstone exact vtable, IAT thunks and RIP references; E3 host Paint receipt F-VECTOR-083
---
# F-VECTOR-084 — Native Paint and Text Animator property hierarchy: two mandatory gates

## Main result

**Discovered and verified a generic structural prerequisite that explains the observed rejection of unknown native Stream MatchNames.**

After Effects distinguishes **registering a Stream class** from **allowing that class as a child of a particular parent group**. In Adobe's built-in Paint, Text Animator, Text Selector and Text Animator Properties groups, these are implemented by separate TDB paths.

### Gate A: Stream creator registration

```text
BEE_AVLayer::RegisterStreams
  -> TDB_ScRegisterStreams::Register(matchname, factory, ...)
  -> TDB_StreamFactory::RegisterFactoryFunc(...)
  -> [under the registered factory path] CreateStream / RegisterSeparatedDimensions
```

This native type registry already contains Adobe's `BEE_PaintAtom::Create` and its derived `TDB_MatchName`, proved in F-VECTOR-080. Both TDB versions also have `TDB_ScRegisterStreams::IsRegistered` using `TDB_StreamFactory::GetCanonicalInstance`, and `UnregisterAll` iterating `UnregisterFactoryFunc`.

### Gate B: parent group's canonical child grammar

**The class's own vtable matters.** `BEE_PaintStrokesGroup` does **not** override `CanStore`. Its vtable slot #56 points to an imported thunk for `TDB.dll!TDB_StreamGroup::CanStore`. Its slot #57 resolves to `BEE_StrokesGroupBase::FillInCanonicalUILayout`.

In AE2026:
```text
BEE_PaintStrokesGroup vtable RVA 0xF2F260
  slot #56 -> BEE.dll+0xC53006
               -> IAT -> TDB.dll!TDB_StreamGroup::CanStore
  slot #57 -> BEE.dll+0x0F0CD0
               BEE_StrokesGroupBase::FillInCanonicalUILayout
                 -> TDB_StreamBase::GetCanonicalStream(
                      BEE_StreamGroupName_PAINT_ATOM)
                 -> append this canonical Paint Atom to the layout

TDB.dll!TDB_StreamGroup::SetupCanonicalLayout (RVA 0x40520)
  -> call [virtual table + 0x1C8] (slot #57 = FillInCanonicalUILayout)
  -> TDB_StreamGroup::SetUILayout

TDB.dll!TDB_StreamGroup::CanStore (RVA 0x36880)
  -> iterate allowable name list in group state
  -> TDB_MatchName::operator== candidate
  -> return bool
```

Verified corresponding AE2025 topology:
- `BEE_PaintStrokesGroup` vtable `0xED5CB0`; slot #56 thunk `0xC2A91E`, slot #57 `0xEAF00`
- `TDB_StreamGroup::SetupCanonicalLayout` `0x3FAC0`; `TDB_StreamGroup::CanStore` `0x35E10`
- `TDB_StreamFactory::RegisterFactoryFunc` `0x27400` (2026 `0x285D0`)

This accounts for AE2026's actual six `AEGP_CanAddStream` results: Paint's `ADBE Paint Group` accepted the registered `ADBE Paint Atom` and rejected `CNL:PaintAtom`, its spoofed Paint suffix and three other tested built-in types (F-VECTOR-083). The native source does **not** simply recognize a permissive `ADBE Paint *` prefix.

### Text Animator uses the SAME mechanism, not a Paint-only exception

Verified vtable slots #56 and #57 in AE2025 and AE2026 for four distinct classes:

| Native class | CanStore slot #56 | FillInCanonicalUILayout slot #57 | Selected canonical children |
| --- | --- | --- | --- |
| `BEE_PaintStrokesGroup` | `TDB_StreamGroup::CanStore` | `BEE_StrokesGroupBase::FillInCanonicalUILayout` | `BEE_StreamGroupName_PAINT_ATOM` |
| `BEE_TextAnimatorStreamGroup` | same TDB CanStore | `BEE_TextAnimatorStreamGroup::FillInCanonicalUILayout` | TEXT_SELECTORS, TEXT_ANIMATOR_PROPERTIES |
| `BEE_TextSelectorsStreamGroup` | same TDB CanStore | `BEE_TextSelectorsStreamGroup::FillInCanonicalUILayout` | TEXT_SELECTOR, TEXT_WIGGLY_SELECTOR, TEXT_LEVELS_SELECTOR, TEXT_EXPRESSIBLE_SELECTOR |
| `BEE_TextAnimatorPropertiesStreamGroup` | same TDB CanStore | `BEE_TextAnimatorPropertiesStreamGroup::FillInCanonicalUILayout` | TEXT_POSITION, TEXT_SCALE, TEXT_OPACITY plus many other canonical properties |

Example AE2026 `BEE_TextAnimatorStreamGroup::FillInCanonicalUILayout` RVA `0x5D5180` independently imports `TDB_StreamBase::GetCanonicalStream` for `TEXT_SELECTORS` and `TEXT_ANIMATOR_PROPERTIES`. `BEE_TextSelectorsStreamGroup::FillInCanonicalUILayout` RVA `0x5D57A0` registers four selector classes. These are the **same** common class-policy and canonical-layout scheme as Paint.

Note that `FillInCanonicalUILayout`'s list drives standard child structure and admission for these observed classes; this finding does not claim all native AE parent classes use precisely the same strategy. `BEE_VectorStream::VectorsStreamGroup` overrides CanStore, unlike Paint/Text classes.

## Engineering significance for a foreign ChapeLayer native type

A third-party AEX would have to solve **both** creation/registration of a foreign valid `TDB_StreamBase` and host-owned parent admission of its MatchName. Registration alone cannot force an existing Paint/Text indexed group to accept the foreign type; the current parent uses Adobe's pre-established canonical child grammar.

Additional separate acceptance gates remain:
- third-party registrar recognized within AE startup/teardown and valid cross-DLL C++ ABI;
- host-tracked keyframes/expression/evaluation, UI layout, edit/selection;
- serialized AEP load/save, stable identities and Undo/Redo;
- renderer/tools integration, safe unload, Windows/macOS compatibility.

No public SDK external stream-class/parent-layout provider has been found. These functions are **private native C++ exports**, not promised third-party SDK APIs. The investigations made **no private in-host function calls**, altered **no Adobe DLLs**, and did **not** register a new custom Stream. A successful offline disassembly does not constitute an AE plugin that displays new native group types.

## Reproducible source and evidence

Scripts:
- `experiments/vector-shape/probe-src/tools/verify_paint_two_gate_canonical_policy.py`
- `experiments/vector-shape/probe-src/tools/verify_paint_text_common_grammar.py`

Datasets:
- `datasets/ae-paint-tdb-two-gate-canonical-policy-2025-2026.json`
- `datasets/ae-paint-text-shared-canonical-grammar-2025-2026.json`

Each verifier uses full `dumpbin /exports` data (not truncated PE exports), PE vtable pointers, IAT identity and Capstone disassembly to verify exact native calls across both installed AE versions, with SHA checks on BEE/TDB originals. PASS 2/2 for each verifier. F-VECTOR-083 is the direct in-host parent admission record.
