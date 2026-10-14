# EXP-SHAPE-080 — Paint.aex versus host-owned Paint native Streams

Status: **PASS static evidence in AE2025 and AE2026; external class admission remains UNPROVEN.**

## Hypothesis

Adobe's Paint Effect is shipped as AEX, but its timeline Strokes and PaintAtom hierarchy is instantiated using native BEE/TDB stream class registrations authored by Adobe's host startup, not ordinary end-user effect `PF_ParamDef` lists.

## Inputs and tools

- AE2025 and AE2026 `Required/Paint.aex`, `BEE.dll`, `TDB.dll` (read-only; SHA in dataset).
- SDK 25.6 `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers`.
- `dumpbin /exports`, `pefile`, `capstone`; direct call instruction boundaries and PE import IAT resolved without executing any private AE functions.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_native_registration.py"
```

Expected: two versions, five `BEE_Paint*::Create` -> `TDB_ScRegisterStreams::Register` calls per version, `PASS 2 versions`.

The Paint.aex itself imports neither BEE nor TDB directly and exports EffectMainExtra, EffectMainExtra2 and PluginDataEntryFunction. Its callback references a private-looking `Paint Suite` name not declared by that exact name in the 25.6 public SDK headers; this is not proof the suite is inaccessible through any other means.

## Acceptance distinctions

- **PASS:** Paint exists as AEX and Adobe already constructs native named/indexed Stream children for Paint under the existing layer/effect architecture.
- **PASS:** Both releases place Paint native Create registrations in BEE_AVLayer::RegisterStreams' built-in path, and the registration target is confirmed by IAT as TDB.dll's TDB_ScRegisterStreams::Register.
- **NOT DEMONSTRATED:** a third-party AEX obtains permission to register and own equivalent new Stream C++ classes.
- **NOT DEMONSTRATED:** a foreign group can be inserted, UI-edited, animated, saved, restored and safely unloaded under an AE Effect Parade member.
- **SEPARATE PRODUCT REQUIREMENT:** a truly new AE-native Layer family also needs BEE_Layer creator/comp attachment; Paint alone does not provide it.

No private functions executed, no production AE modifications, no project writes. Further runtime Paint hierarchy inspection must use public read-only AEGP APIs first.

Details: `research/findings/F-VECTOR-080-adobe-paint-aex-native-tdb-registration.md`.
