---
date: 2026-10-14
status: PASS offline static registration proof, AE2025 and AE2026; foreign Paint-style stream provider NOT demonstrated
evidence: E2-L SHA-pinned original installed AEX/BEE DLLs, complete dumpbin export list, Capstone native instructions, PE import IAT identity
---
# F-VECTOR-080 — Adobe Paint.aex and its actual BEE/TDB native Timeline stream registration

## Critical discovery and corrected model

The built-in **Paint** effect (with editable Strokes/Brush paths and nested timeline properties) is delivered as an actual Adobe AEX module:

- AE2025: `C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\Required\Paint.aex` (42,504 bytes, SHA256 `50ddd78f6e7d5352ed4e156267d971f70a32e44bb62b02956f2916ce5272aef4`)
- AE2026: `D:\Adobe\Adobe After Effects 2026\Support Files\Required\Paint.aex` (41,480 bytes, SHA256 `b1190b667f27521540f640bf18f81468b7549a660115209b5312e791087fa62e`)

This **is** a real effect AEX, with exported `EffectMainExtra`, `EffectMainExtra2`, `PluginDataEntryFunction`. Do NOT mistake the unrelated Stylize `Plug-ins\Effects\Brush_Strokes.aex` for the native Paint tool effect.

However, Paint's full native Timeline Stream grammar is **not defined solely in that AEX**. In both versions, its direct PE imports have **no BEE.dll or TDB.dll**. The Paint AEX contains and uses a literal `Paint Suite`; its shared EffectMain callback references that string, but the ABI and suite ownership are not in the published AE25.6 SDK headers. The SDK provides public Paint Palette color accessors; that is NOT a custom Paint Stream registrar.

## Positive native evidence: the real owner is wired into BEE_AVLayer::RegisterStreams

In both installed `BEE.dll` binaries, the public export `BEE_AVLayer::RegisterStreams` calls a native helper that forms a `std::function` for each built-in Paint Stream creator and invokes the imported `TDB_ScRegisterStreams::Register` with its derived MatchName:

| Object, exact export | 2025 factory creator RVA / Register CALL | 2026 factory creator RVA / Register CALL |
| --- | --- | --- |
| `BEE_PaintAtom::Create` | `0x47C40` / `0x25CF98` | `0x47520` / `0x267B7A` |
| `BEE_PaintStrokesGroup::Create` | `0x48390` / `0x25D02E` | `0x47C00` / `0x267C10` |
| `BEE_PaintEffect::Create` | `0x47FF0` / `0x25D060` | `0x47880` / `0x267C42` |
| `BEE_PaintProperties::Create` | `0x48270` / `0x25CED0` | `0x47AF0` / `0x267AB2` |
| `BEE_PaintTransform::Create` | `0x484A0` / `0x25CBB0` | `0x47D00` / `0x267792` |

Actual call chain:
- 2025: `BEE_AVLayer::RegisterStreams` RVA `0x28FA80` -> helper `0x25C5E0` -> above Paint calls through `TDB.dll!TDB_ScRegisterStreams::Register`.
- 2026: `BEE_AVLayer::RegisterStreams` RVA `0x298CB0` -> helper `0x267190` -> same named Paint registration through `TDB.dll!TDB_ScRegisterStreams::Register`.

Exact 2026 machine edge for Paint Atom:
- `BEE.dll+0x267B52`: RIP-relative LEA resolves `BEE_PaintAtom::Create` at `0x47520`.
- `BEE.dll+0x267B6C`: RIP-relative LEA resolves `BEE_StreamGroupName_PAINT_ATOM` at `0x1661818`.
- `BEE.dll+0x267B7A`: call via IAT entry `0xF178C8`, explicitly imported from `TDB.dll` as `TDB_ScRegisterStreams::Register`.

Additional verified Paint exports include `FillInCanonicalUILayout`, `Read`, `Write`, `CloneStream`, `GetStrokesGroup` and several TDB-derived Float/Color/path/transform stream traits. This is a genuine TDB-native property owner and built-in Paint registration, not a UI-only fake group or ordinary `PF_ADD_TOPIC`.

**Proven:** Adobe internally registers sophisticated, editable, dynamic nested effect property classes at BEE/AV-layer initialization, before/independently of arbitrary customer AEX Stream registration.

**Not proven:** a third-party AEX may safely join BEE's startup registration, supply a compatible `TDB_StreamBase` class, choose a valid existing owner and parent, or guarantee save/reopen, animation, UI, undo and unloading. An exported C++ `Register` is not a supported external registration API. ABI expects `std::function`, private TDB layout and owning stream factory. NEVER invoke it from a live user AE installation as an exploratory probe.

This narrows the actual target significantly: for a **Paint-like custom effect Contents**, identify a supported and lifecycle-safe stream provider for the existing BEE Effect owner. This is still a different objective from an independent new native `BEE_Layer` class; the latter additionally needs a new Layer type factory/ownership contract (F-VECTOR-037/071/079).

## Offline reproducibility and limits

Script: `experiments/vector-shape/probe-src/tools/verify_paint_native_registration.py`

Data: `datasets/ae-paint-native-stream-registration-2025-2026.json`

Source lab: `D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit`.

The verifier reads both original AEX and BEE PE files, enumerates **all** BEE exports using `dumpbin /exports`, disassembles actual unwind-bounded functions using Capstone, identifies both Creator and MatchName RIP references, and resolves the following call through PE IAT to **TDB.dll!TDB_ScRegisterStreams::Register**. It checks all five Paint class creators and both host versions. PASS 2/2 on 2026-10-14.

The result is static PE evidence, **not** execution or dynamic UI admission of a new foreign Stream. No Adobe files modified; no private host API executed; no experimental AEX installed; no CompNodeAE changes.

## Next experimental gate (do not skip)

A meaningful next positive test would need a safe host-provided external registrar and canonical owner contract (or explicit Adobe SDK team confirmation of its availability). A read-only AEGP traversal of an existing Paint effect can additionally establish its visible native grouping and exact MatchNames, but cannot prove foreign Stream creation. Calling `AEGP_CanAddStream` with an unknown prefixed name also does not prove a matching creator exists.
