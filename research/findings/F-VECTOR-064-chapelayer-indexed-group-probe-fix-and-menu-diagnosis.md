---
date: 2026-10-13
status: fixed and offline PASS; updated AE2026 host run PENDING
evidence: E2-X user's AE error screenshots and TEMP read-only TSV; E2-L Adobe AEGP SDK and compiled AEX
---
# F-VECTOR-064 — Native Indexed Contents is ADBE Root Vectors Group, not a Named Group; Layer New menu visibility vs registration split

## Root cause confirmed by the actual user-host data

When running the ChapeLayer read-only probe in After Effects 2026, AE raised its internal verification error:

    GetNewStreamRefByMatchname only works on named groups

The read-only AE2026 TSV generated in the same run recorded:
- Selected actual native ADBE Vector Layer kind = 4, root stream MatchName = ADBE Vector Layer and grouping type NAMED_GROUP (1).
- ADBE Root Vectors Group = grouping type INDEXED_GROUP (2); on this particular fixture it had zero child streams, but the host allowed appropriate native vector child names.
- Unknown ADBE-prefix Shape/Graphic/Filter children returned CanAdd=true; CNL namespace MatchNames CanAdd=false.

The code attempted GetNewStreamRefByMatchname(parent=ADBE Root Vectors Group, target=ADBE Vectors Group), incorrectly assuming the root Contents is named. In fact **ADBE Root Vectors Group is the indexed top-level Contents itself**. The error is caused by the probe, not evidence that TDB private registration succeeded or the host native tree is corrupt.

## Fixed implementation (actual ShapeLayerAE source)

- Before using GetNewStreamRefByMatchname, check grouping type is NAMED_GROUP.
- Set Shape Contents reference directly to the already acquired Root Vectors stream.
- Enumerate children with GetNewStreamRefByIndex, and only access 'ADBE Vectors Group' inside a NAMED_GROUP representing a native child Group.
- Do not dispose the aliased top-level indexed Contents twice.
- Continue read-only CanAdd/child-index/geometry grammar trace report.
- Stronger static verifier checks this invariant; MSVC Release AEX rebuilt, native CTest 2/2 PASS, PE verifier PASS.

## ChapeLayer Layer > New UI placement diagnosis

The user's new AE2026 screenshot showed a fully populated Layer > New menu but no ChapeLayer command, even though the same AEX's Animation probe was loaded and executed.

The Adobe SDK exposes AEGP_Menu_NEW as the official Layer > New insertion destination. The old plug-in inserted AT_BOTTOM and no menu registration results were logged. Consequently **the reason for its absence is NOT yet known**; do not claim that the enum necessarily works in this AE build.

The updated plug-in:
- tries AEGP_Menu_NEW at AT_TOP;
- independently inserts a test 'ChapeLayer: Native Type Status (Fallback)' in the top level Layer menu, to distinguish insertion vs rendering;
- writes TEMP/ChapeLayer_MenuRegistration.tsv during AEGP initialization with get/insert results for all menu commands plus callback hook registration results;
- keeps both click paths fail-closed: it does not silently make an Adobe Shape Layer or mutate the project.

A zero InsertMenuCommand return only means the public SDK call succeeded, not that AE rendered that menu entry. Updated AEX has **not** yet been run by the user. The actual visual result and TSV are needed to close this UI issue.

## Next manually performed host experiment

1. Close AE, back up the installed old CNLNativeShapeLayer.aex, replace only that binary with the newly built file from D:/Developer/ShapeLayerAE/build/native_shape_layer_prototype/Release.
2. Relaunch disposable AE2026 session. Check Layer > New top, and separately Layer top for fallback.
3. Inspect %TEMP%/ChapeLayer_MenuRegistration.tsv after startup.
4. Create a **stock Shape Layer with a real Group and Path** in a disposable project, select that layer, and run Animation > ChapeLayer: Inspect Native Contents Admission (Read Only).
5. Inspect TEMP/ChapeLayer_HostAdmission_ReadOnly.tsv. It should now contain non-empty Shape Contents and the native indexed_children rows without any internal verification failure.
6. Do not run CNLPrivateTDBDisposable.aex; do not use AddStream with invented MatchNames.

No AE GUI was launched or controlled in this analysis; host verification must be performed by the user. No project or CompNodeAE modified. Private Shape type registration, independent BEE Layer owner, native Pen, Undo and VectorArt remain not implemented.
