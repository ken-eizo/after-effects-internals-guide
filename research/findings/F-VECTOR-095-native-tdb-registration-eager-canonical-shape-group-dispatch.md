---
date: 2026-10-14
status: PASS static x64 crossversion register-to-canonical-layout dispatch; not yet a foreign AE-owned native Stream
evidence: E2-L exact installed AE2025/AE2026 TDB.dll, BEE.dll, OM.dll PE exports, bytes, vtable pointers, imported C++ thunks and native CALL sites; strict independently rerunnable scripts
---
# F-VECTOR-095 — Full TDB native type registration → eager canonical object → virtual group layout → BEE Shape Contents child grammar

## Breakthrough

The previous investigations proved separate truths: Adobe modules can register native TDB concrete C++ classes (F-VECTOR-093/094) and Shape Contents has a built-in canonical child grammar (F-VECTOR-054/092). This study recovers **the actual C++ virtual call chain that connects them in the host**.

In both installed AE2025 and AE2026 x64, `TDB_StreamFactory::RegisterFactoryFunc` does **not** simply store a key and return. It checks for an existing MatchName, inserts a creator, **eagerly calls `TDB_StreamFactory::CreateStream`** to construct a canonical prototype, records it, makes conditional virtual calls on the prototype, and (when the registration flag permits) invokes **virtual `SetupCanonicalLayout()`**.

For real native group types, that virtual call reaches `TDB_StreamGroup::SetupCanonicalLayout`, which **calls virtual `FillInCanonicalUILayout()` at vtable offset `+0x1C8`**, processes separated dimensions and calls **`TDB_StreamGroup::SetUILayout`**. Actual BEE Shape Contents and Root Vectors groups override `FillInCanonicalUILayout()` in their vtables. Hence the concrete chain is:

```text
Adobe native OM_Birth / FLT_Birth / BEE_Birth
  └─ TDB_StreamFactory::RegisterFactoryFunc(matchName, creator, bool)
       ├─ guarded MatchName duplicate search
       ├─ register callback in internal map
       ├─ TDB_StreamFactory::CreateStream(..., flags)
       │    └─ invoke registered native C++ Creator → TDB_StreamBase*
       ├─ retain canonical object
       ├─ virtual IsLeaf() [vtable +0x58]
       │    └─ virtual GetAsLeaf() [+0x80], IsSeparationLeader() [+0x298]
       │         └─ potentially RegisterSeparatedDimensions()
       └─ (conditional bool flag) virtual SetupCanonicalLayout() [+0x150]
            ├─ TDB_StreamBase: empty base stub; NO CHILDREN
            └─ TDB_StreamGroup override: real hierarchy creation
                 ├─ virtual FillInCanonicalUILayout(vector<TDB_StreamBase const*>*)
                 │     [vtable +0x1C8]
                 │     └─ e.g. BEE_VectorStream::VectorsStreamGroup
                 │           → canonical Shape Contents child definitions
                 ├─ TDB_StreamFactory::SetupCanonicalLayoutForSeperatedDimensions()
                 └─ TDB_StreamGroup::SetUILayout(shared_ptr<vector<...>>)
```

**Careful distinction:** executing a registered creator and configuring its canonical UI object does not guarantee an inserted project Stream, a Timeline UI control, a registered BEE evaluator or editor, .aep serialization, or foreign plugin lifecycle.

## Machine-code proof in two releases

| Evidence | AE2025 | AE2026 |
| --- | --- | --- |
| `TDB_StreamFactory::RegisterFactoryFunc` RVA | `0x27400` | `0x285D0` |
| Eager direct `CreateStream` CALL site | `0x2757F` | `0x2874B` |
| `IsLeaf` virtual `+0x58` CALL | `0x275BA` | `0x28786` |
| `GetAsLeaf` virtual `+0x80` CALLs | `0x275C7, 0x275E3` | `0x28793, 0x287AF` |
| `IsSeparationLeader` virtual `+0x298` CALL | `0x275D3` | `0x2879F` |
| `SetupCanonicalLayout` virtual `+0x150` CALL | `0x275FF` | `0x287CB` |
| `TDB_StreamGroup::SetupCanonicalLayout` | `0x3FAC0` | `0x40520` |
| Group `FillInCanonicalUILayout` virtual `+0x1C8` CALL | `0x3FB59` | `0x405AE` |
| `BEE_VectorStream::VectorsStreamGroup::FillInCanonicalUILayout` | `0x702DB0` | `0x7258C0` |
| `BEE_VectorStream::VectorStreamGroup::FillInCanonicalUILayout` | `0x702CB0` | `0x725820` |

Additional proof is in the machine-readable datasets: exact vtable addresses, byte-exact `TDB_StreamBase::SetupCanonicalLayout` empty stub (`C2 00 00` = `ret 0`), `TDB_StreamGroup` override slot, native `SetupCanonicalLayoutForSeperatedDimensions` direct CALL and `SetUILayout` direct CALL in correct chronological instruction order.

The virtual method names are **not inferred from slot offsets**: we resolve those offsets in the *real* `TDB_ParamPathStream` native vtable to exact exported C++ methods `IsLeaf`, `GetAsLeaf`, `IsSeparationLeader`, and `SetupCanonicalLayout`, checking both DLL builds. Separately, the Shape Group vtable's `+0x1C8` pointer resolves **exactly** to the exported BEE `FillInCanonicalUILayout` override in each release, and the native TDB group initializer actually calls this slot.

**OM cross-DLL virtual ABI corroboration:** the native `OM_Stream` vtable has the same named slots. OM's `+0x58`, `+0x80`, and `+0x150` entries are PE `JMP [IAT]` forwarding thunks to the corresponding TDB.dll implementations, while `+0x298` is OM's own `IsSeparationLeader` override. This independently demonstrates that a native Stream **implemented in OM.dll uses TDB.dll virtual methods through cross-module linking**, rather than just sharing similarly named C++ exports.

## A critical implementation trap and product consequence

- The `TDB_StreamBase::SetupCanonicalLayout` default is a no-op. A foreign leaf Stream with a novel MatchName therefore does NOT invent a native Contents Group merely by successfully registering.
- Adobe's actual Shape Group derives from an appropriate group hierarchy and overrides `FillInCanonicalUILayout` (and uses host-native canonical child vectors). A future foreign *group* would have to provide ABI-compatible C++ inheritance, virtual table, native factory allocation, child Stream classes, canonical linkage, serializer/clone and lifetime.
- `RegisterFactoryFunc` eagerly constructs the prototype and calls its virtual functions **during registration**. A broken, non-constructible, or wrong ABI foreign callback can corrupt AE or crash *inside the registration call*, before a plugin ever attempts to add a Timeline child. This explains why the disposable high-risk AEX cannot be treated as a safe simple name-test.
- The existing experimental `CNLPrivateTDBDisposable.aex` borrows **Adobe's built-in TDB_ParamPathStream::Create**, so even a hypothetical PASS would test private registry MatchName acceptance with a **leaf**, not custom CNL group creation.
- `BEE_VectorStream::VectorsStreamGroup::CanStore` has the exact `ADBE Vector Group`/Shape/Graphic/Filter prefix predicate documented in F-VECTOR-065. A new stream creator with an arbitrary `CNL:` MatchName **would not satisfy that built-in parent predicate**; spoofing an accepted prefix does not guarantee a native evaluator or editing mode.
- Registering while AE is running also raises host initialization-order and unload concerns not resolved by this static study. Internal BEE/OM/FLT registrar calls run under host-controlled startup/teardown (F-VECTOR-093), unlike normal AEX SDK startup.

## Reproduction (all read-only)

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_eager_canonical_vtable_dispatch.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_group_bee_contents_canonical_dispatch.py"
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_om_native_vtable_tdb_dispatch_bridge.py"
```

Strict datasets:
- `datasets/ae-tdb-eager-canonical-vtable-2025-2026.json`
- `datasets/ae-tdb-group-to-bee-shape-canonical-dispatch-2025-2026.json`
- `datasets/ae-om-native-vtable-to-tdb-dispatch-2025-2026.json`

The scripts parse original installed TDB/BEE/OM PE images, validate the virtual-table slot offsets and native imported JMP trampolines and reproduce the exact crossrelease native instruction RVAs; no code is injected into Adobe.

## Remaining actual product gates

Still **NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM**: No third-party custom CNL-derived class has been registered into AE's host registry, no genuinely new Contents group has been added to the standard Timeline, no native property widget or editing/Undo/archive/rendering pathway is demonstrated for a foreign C++ group, no macOS private equivalent is validated. The user has temporarily postponed Windows VM construction; no unsafe in-host API call performed. Existing AE projects, Adobe install and CompNodeAE untouched.
