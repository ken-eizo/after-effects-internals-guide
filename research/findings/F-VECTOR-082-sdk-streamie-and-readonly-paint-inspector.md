---
date: 2026-10-14
status: PASS compiled read-only Paint native Timeline inspector; 4/4 CNL native tests; AE host test of new inspector NOT RUN
evidence: E2-L Adobe AE25.6 SDK Streamie source, C++ Release compiled AEX, PE PiPL and import checks; GUI output pending
---
# F-VECTOR-082 — Adobe SDK Streamie confirms legal native Paint-stroke manipulation; CNL real Paint inspector built

## New evidence in supplied SDK

The installed Adobe SDK 25.6 includes `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/AEGP/Streamie/Streamie.cpp` (Adobe sample; do not copy its proprietary source into this repository).

The sample traverses an active ordinary layer:
`AEGP_GetNewStreamRefForLayer` -> `AEGP_StreamGroupName_EFFECT_PARADE` -> the FIRST effect (assumes Paint in its fixture) -> `"ADBE Paint Group"`.

It then uses `AEGP_GetNewStreamRefByIndex` to obtain native paint strokes and publicly supported `AEGP_ReorderStream`, `AEGP_SetStreamName`, `AEGP_DuplicateStream`, `AEGP_DeleteStream`. Thus existing host-registered **Paint Atom** children are accessible as real dynamic AE Timeline Streams through the public SDK. This is an actual Adobe-authored example, not a hypothetical custom UI or CNL-owned mock.

**The sample does NOT register a new `TDB_StreamBase` type.** It edits *existing Adobe host-created* Paint children, so it does not establish a foreign class owner. It also does not imply the user wants to modify Paint/replace its UI; the target is new native types/groups.

## New independent read-only CNL test command

Added `D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype/ChapePaintNativeInspector.cpp` and wired it in the existing prototype AEGP:

`Animation > ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)`

The command, **when separately installed and run by the user in a disposable AE**, chooses the active layer, finds the Effect Parade by public AEGP, enumerates the effects, matches the exact `"ADBE Paint"` (NOT Paint Bucket / Brush Strokes), then recursively enumerates both NAMED and INDEXED groups, printing MatchName, stream name, grouping type, child counts, depth, and AEGP error codes into:

`%TEMP%/ChapeLayer_PaintNativeHierarchy.tsv`

It has bounded depth (8), children per group (120), total nodes (500), uses AEGP_GetNewStreamRefByIndex for both named/indexed groups as explicitly allowed by the current SDK headers, avoids `GetNewStreamRefByMatchname` on INDEXED, guards camera/light, disposes refs, and **never invokes mutation operations**.

Menu registration error reporting was extended in `ChapeLayer_MenuRegistration.tsv` with `paint_get_error` and `paint_insert_error`. Missing Paint reports `paint_found=0` rather than manufacturing a brush stroke.

Native C++ Release build: PASS.
CNL CTest suites: 4/4 PASS.
`verify_native_shape_aex.py`: PASS, x64 / PiPL / AEGP, all CNL ABI exports, zero direct BEE/TDB/FLT imports; AEX SHA256 `9aecd60302622f68087146f52fd305be2cfe476f467e147183cbb8e733cd9192`.
`verify_paint_sdk_and_inspector.py`: PASS inspected SDK source, guarded inspector source and new binary.

## Host validation remains pending

**Do not claim actual Paint hierarchy TSV or visible new menu execution without a real AE host run.** This work did not replace an installed AEX, open a user project or invoke private BEE/TDB. The user may test only after closing AE in a separately chosen disposable installation/project. A binary build is NOT enough to claim any new native Stream registered in Adobe's Timeline.

Practical next target: obtain the actual hierarchy/MatchNames from host and verify whether Paint Strokes is indexed, which child is fixed and which operations are publicly legal. This can confirm what a Paint-like extension can *inspect and manipulate*, but cannot substitute for foreign creator registration.

Cross references F-VECTOR-080 / F-VECTOR-081 for actual host side type registrations and private Paint Suite bridge.
