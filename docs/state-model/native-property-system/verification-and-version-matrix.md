---
status: scope-and-verification-reference
last_verified: 2026-10-15
evidence: E0-G + E0-H + E0-S + E2-L + E2-X + H
versions: Installed Windows AE2025 / AE2026, SDK25.6; other releases unqualified
---

# Native Property Verification, Version Lineage and Unknowns

This page is the **evidence boundary** for the technical chapters. It is not a chronology of experiments. Historical findings and raw receipts are located separately in the research corpus.

## Evidence and current coverage

| Domain | Evidence and extent | Verified outcome | Unknown boundary |
| --- | --- | --- | --- |
| Built-in native module startup | E2-L TDB/BEE/OM/FLT/aelib x64, 2025+2026 | Cross-DLL Birth calls and registrars | Exact runtime branch behavior, third-party startup |
| Concrete C++ native Stream | E2-L `OM_Stream` 2025+2026 | Creator, allocator, constructor, vtable, value methods, explicit teardown | Complete private ABI and macOS |
| Factory registry | E2-L strict machine code 2025+2026 | Eager Creator, canonical prototype, successful unlink/deletion | Exception rollback and surviving document instances |
| Instance generation | E2-L strict x64 original TDB 2025+2026 | Creator callback after mutex unlock; default key and optional decanonicalization paths | Exact per-flag behavior and plugin unload concurrency |
| Parent indexed insertion | E2-L strict TDB vtable 2025+2026 | CanStore before insertion, reverse index/capsule cache/SetParent updates | Complete error rollback and all option meanings |
| Document reconstruction | E2-L native StreamGroup Read/Write 2025+2026 | Child MatchName → CreateStream → InsertStream/Read | Missing foreign Creator AEP behavior and arbitrary roundtrip |
| Indexed child removal | E2-L SHA-pinned TDB x64 AE2025+2026 | Return same detached child, parent +0x20 cleared, indexed vector/reverse map updated | Undo ownership, destruction and reuse |
| Structural Undo routing | E2-L cross-DLL TDB+BEE AE2025+2026 | Add/Remove/Duplicate/Reorder begin/dispatch/end BEE Undo grouping | Inverse task lifetimes and arbitrary external type enrollment |
| Missing-Creator reporting | E2-L Win64 TDB AE2025+2026 | Named loader flag 0, Indexed loader flag 1; report branch in CreateStream | Real host error/dialog/recovery and data preservation |
| Canonical group layout | E2-L TDB/BEE vtable 2025+2026 | `FillInCanonicalUILayout`, separated dimensions, UILayout | All variant branches/editor binding |
| Paint/Text admissibility | E2-L+E2-X built-ins, AE2026 Paint fixture | Named/indexed grammar, strict Paint child policy | Arbitrary external parent provider |
| Shape Contents admissibility | E2-L+E2-X AE2026 preflight | Exact Group plus three prefixes | Create/Add/Serialize arbitrary prefixed Stream |
| Child layout census | E2-L 102/104 functions | 685/694 exact child MatchName refs | 7 unresolved calls each release |
| AEGP Stream metadata | E0-H+E2-X AE2026 fixture | Brush Paint v2: 170 nodes, no errors | Session UID anomaly in separate Shape capture |
| New external class | Build/mock only + bounded negative SDK25.6 | **Not demonstrated in real AE** | Approved registrar, lifecycle, support |
| New foreign Layer family | E2-L native built-in Layer path + CNL mock | **Not demonstrated in AE** | Owner/CompItem/Undo, render/editor |
| macOS native property private ABI | No matching native image evidence | **Unverified** | Itanium/Clang ABI and Adobe load contract |

The `E2-L` PE images are original installed Adobe assets and stored only on the authorized Windows machine. Reproducible **scripts and metadata**, not Adobe proprietary binaries, are in the repository.

## Exact useful reproducibility entries

| Topic | Report | Reproducible artifact |
| --- | --- | --- |
| Paint AEX / BEE TDB Creator | F-VECTOR-080/081 | `verify_paint_native_registration.py`, `verify_paint_suite_host_bridge.py` |
| Paint real AEGP hierarchy | F-VECTOR-083/087 | `ae-paint-native-hierarchy-host-v2-2026-20261014.tsv` + verifier |
| Text and Paint parent policy | F-VECTOR-084 | `verify_paint_text_common_grammar.py` |
| All canonical schema class refs | F-VECTOR-092 | `verify_strict_canonical_dataflow.py` |
| Native cross-DLL registration | F-VECTOR-093 | `verify_om_flt_bee_crossmodule_native_registration.py` |
| OM C++ allocator/vtable | F-VECTOR-094 | `audit_om_native_stream_abi_and_teardown.py` |
| Eager canonical/layout vtables | F-VECTOR-095 | `verify_tdb_eager_canonical_vtable_dispatch.py`, `verify_tdb_group_bee_contents_canonical_dispatch.py` |
| Creator/prototype destructor | F-VECTOR-096 | `verify_tdb_native_creator_canonical_lifetime.py` |
| Indexed child detach + command undo | F-VECTOR-099 | `verify_tdb_native_detach_bee_indexed_undo.py` |
| Native archive missing-Creator report policy | F-VECTOR-100 | `verify_tdb_archive_missing_creator_error_policy.py` |
| Supported AEGP SDK coverage | F-VECTOR-088 | `verify_public_sdk_native_provider_gap.py` |

Script location: `experiments/vector-shape/probe-src/tools/`. Raw JSON location: `datasets/`. Full research files: `research/findings/` (not the normal feature-based user guide).

## Operational statuses (do not merge)

- **Observed native class in Adobe**: actual `OM_Stream`, FLT Effect native classes, BEE Paint/Text/Vector classes in shipped DLLs.
- **Observed from third-party AEGP**: read-only traversal and metadata of **existing** Paint/Shape Streams.
- **Offline compiled independent implementation**: ChapeLayer/CNL own hierarchy and ABI, not an Adobe Timeline integration.
- **Not observed in real AE**: arbitrary new `CNL:...` host-native Group/Property or independent Layer kind.
- **Not a supported external API**: `TDB_StreamFactory`, `OM_Birth`, `BEE_Birth`, canonical layout internals.

This distinction avoids the common error of interpreting a successful mock, a non-null native function pointer or an accepted `CanAddStream` prefix as a full custom host-owned property.

## Version drift

Cross-version private differences include:
- `aelib.dll` native Birth/Death callsite RVAs;
- `BEE.dll` additional canonical property definitions in AE2026, including Text Variable Font Spacing and select 3D Mesh options;
- `FLT.dll` seventh native effect registration, `EFFECT_BLENDMODE`, in AE2026;
- changed internal Layer field and vtable offsets even when some TDB factory offsets remained equal.

**No private symbol/offset from 2025/2026 is a version-independent third-party ABI.** SHA-pinned tests fail when the original source DLL digest changes.

## Falsification and next acceptance experiment

The outstanding product claim is:

> A third-party AEX can register an independently implemented native Stream subclass, attach a new type/group under an AE-host-owned parent, edit it in Adobe's standard Timeline, save/reopen and unload safely.

It remains **H: unproven**. A meaningful positive test needs a permitted host registration entry and, at minimum, evidence of created instance + editor + persistence + teardown. A read-only preflight cannot close the claim. Experiments with private native C++ ABIs must be confined to a **disposable isolated AE installation with crash capture and rollback**, never a production session. The Windows VM-only test kit remains blocked by lack of an isolated guest. See F-VECTOR-090/091 and [Native property owner gate](../../vector-shape-system/independent-native-layer-provider-admission.md).

## Reproducibility metadata format

A new investigation should record: original module/version/SHA; source import/export/RVA; type and method signature provenance; executable host vs static analysis; exact input project and operation; error/return value; memory/prototype lifetime observation; supported SDK boundary; platform; falsifying result; and links to raw receipt. Keep reproducible findings in `research/` or `experiments/` and promote only the verified architecture into feature pages.

Read [Evidence Model](../../foundations/evidence-model.md), [Version Model](../../foundations/version-model.md) and [Native Property API Atlas](api-atlas.md).
