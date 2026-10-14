---
status: architecture-reference
last_verified: 2026-10-14
evidence: E0-H + E2-L + E2-X
versions: AE2025 / AE2026 Windows; SDK 25.6
---

# Canonical Groups, Child Types and Native UILayout

Native property groups do not become extensible simply because a child class is registered in the host factory. The **parent's accepted child grammar** and its canonical layout are independent of the child's Creator.

## Two independent admission gates

| Gate | Native operation | Question | Failure symptom |
| --- | --- | --- | --- |
| **A: Type construction** | `TDB_StreamFactory::CreateStream(matchName,...)` | Does a C++ Creator exist and construct a valid native type? | Factory cannot build the child |
| **B: Structural permission** | `TDB_StreamGroup::CanStore` or specialized override | Does this parent permit this child's MatchName? | `AEGP_CanAddStream` returns false |

A third stage is **document ownership and editor integration**. Even a parent that returns TRUE from CanAdd may not accept an actual insertion without a Creator, correct host bookkeeping and UI support. Neither gate alone demonstrates a functioning custom property.

## Group initialization: actual virtual dispatch

```text
TDB_StreamFactory::RegisterFactoryFunc
  -> canonical prototype
     -> virtual SetupCanonicalLayout  [vtable +0x150]
        -> TDB_StreamBase (default: empty return)
        -> TDB_StreamGroup (real group implementation)
           -> virtual FillInCanonicalUILayout [vtable +0x1C8]
              -> GetCanonicalStream(...) for built-in child types
              -> append native child stream definitions to group schema
           -> SetupCanonicalLayoutForSeperatedDimensions(...)
           -> SetUILayout(...)
```

Both versions' installed native TDB groups use this callsite structure (F-VECTOR-095). In AE2026 the TDB Group method starts at RVA `0x40520`; its virtual `FillInCanonicalUILayout` callsite is `0x405AE`, followed by separated-dimension configuration and `SetUILayout`. The analogous AE2025 code is RVA `0x3FAC0` with virtual callsite `0x3FB59`.

The same virtual slot `+0x1C8` in the actual BEE Shape Contents group points to `BEE_VectorStream::VectorsStreamGroup::FillInCanonicalUILayout`. **This is the real bridge between type registration and the host-native Contents schema.**

## Three different parent policies

### Native Paint Strokes — strict child schema

A genuine Brush-created Paint effect has `ADBE Paint Group` as an **indexed group**. `BEE_PaintStrokesGroup` inherits the common `TDB_StreamGroup::CanStore` method and defines its accepted type through `BEE_StrokesGroupBase::FillInCanonicalUILayout`. The canonical child is `ADBE Paint Atom`.

AE2026 in-host AEGP inspection returned:

| Proposed child | `AEGP_CanAddStream` | Error |
| --- | --- | --- |
| `ADBE Paint Atom` | **TRUE** | 0 |
| `ADBE Paint Nibbler Atom` | FALSE | 0 |
| `ADBE Paint Shape` | FALSE | 0 |
| `ADBE Vector Group` | FALSE | 0 |
| `CNL:PaintAtom` | FALSE | 0 |
| `ADBE Paint Atom - CNLProbe` | FALSE | 0 |

This is **E2-X observed** in a real AE2026 Paint fixture (F-VECTOR-083/087), not a guessed native class hierarchy.

### Text Animator and Selector groups — canonical indexed children

The real `BEE_TextAnimatorStreamGroup`, `BEE_TextSelectorsStreamGroup` and `BEE_TextAnimatorPropertiesStreamGroup` use the common `TDB_StreamGroup::CanStore` implementation with **different class-specific `FillInCanonicalUILayout` lists** (F-VECTOR-084).

Examples:

| Parent | Canonical child categories |
| --- | --- |
| Text Animator | Text Selectors, Text Animator Properties |
| Text Selectors | Range, Wiggly, Expressible / related Selector kinds |
| Text Animator Properties | Position, Scale, Opacity and additional text transforms |
| Paint Strokes | Paint Atom |

A parent with this schema does **not** automatically accept a new arbitrary `CNL:` MatchName. Each needs a compatible native canonical child grammar and its own class registration.

### Shape Contents — one exact MatchName plus three prefixes

Unlike the common Paint/Text rule, `BEE_VectorStream::VectorsStreamGroup::CanStore` has a reconstructed built-in predicate:

```text
CanStore(name) =
    name == "ADBE Vector Group"
    OR name starts with "ADBE Vector Shape -"
    OR name starts with "ADBE Vector Graphic -"
    OR name starts with "ADBE Vector Filter -"
```

This exact rule is validated in AE2025 and AE2026 against original BEE code: the equality compares an actual initialized `ADBE Vector Group` `TDB_MatchName`, and prefix checks use CRT string search plus begin-pointer comparison (F-VECTOR-063/065). AE2026's real `AEGP_CanAddStream` accepted synthetic Shape/Graphic/Filter-prefixed strings in **preflight only**. No foreign CNL Stream was instantiated, serialized or rendered.

## Canonical child grammar recovered from binary references

In F-VECTOR-092 the strict extractor recognized four native MatchName export families and verified each `LEA RDX, [RIP+name]` feeding the actual `TDB_StreamBase::GetCanonicalStream` import.

| Metric | AE2025 | AE2026 |
| --- | ---: | ---: |
| `FillInCanonicalUILayout` implementations | 102 | 104 |
| `GetCanonicalStream` import calls | 692 | 701 |
| Child identities proven by direct RDX dataflow | **685** | **694** |
| Calls without a proven association | 7 | 7 |
| Canonical Shape Contents child kinds in root list | 20 | 20 |

The 20 native Shape Contents entries include Group, Path, Polystar, Rectangle, Ellipse, Fill, Gradient Fill, Stroke, Gradient Stroke, Trim Paths, Offset Paths, Pucker & Bloat, Repeater, Reveal Paths, Merge Paths, Roughen Paths, Zig Zag, Round Corners, Twist, and Wiggle Paths.

The census is of **native reference callsites**, not unique instantiated nodes or permission to create every class in every parent. Data: `datasets/ae-bee-canonical-grammar-strict-rdx-2025-2026.json`; F-VECTOR-092.

## Public AEGP operation and its limits

`AEGP_DynamicStreamSuite4` exposes `AEGP_CanAddStream`, `AEGP_AddStream`, `AEGP_ReorderStream`, `AEGP_DeleteStream`, `AEGP_DuplicateStream`, `AEGP_GetStreamGroupingType` and other supported operations **on host-created streams**. The installed Adobe Streamie sample demonstrates known-native Paint Strokes manipulation.

`AEGP_AddStream` is **undoable** but its documented precondition is an **indexed parent group** and an admitted, registered child type. It does not register a new native C++ Stream class or replace parent `CanStore`.

## Native custom-group requirements

A third-party host-native group would require all of: native C++ group inheritance and compatible vtable, own canonical `FillInCanonicalUILayout`, registered valid child Creators, `CanStore` / accepted names, host-owned document instance, correct Timeline editor and property ID path, clone/save/keyframe/Undo, evaluator where appropriate and stable teardown. **No supported SDK25.6 provider for this combination was found**, and the ChapeLayer foreign group remains unimplemented.

See [Paint, Text and Shape hierarchies](paint-text-shape-hierarchies.md), [Factory lifetime](factory-registration-lifetime.md), and [API Atlas](api-atlas.md). Verified sources: F-VECTOR-063/065/083/084/092/095.
