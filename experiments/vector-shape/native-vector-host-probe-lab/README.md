# CNL Native Vector Host Probe (Research AEGP)

This is a compiled Adobe AEGP containing the independent CNLNativeVectorCore object model. It deliberately DOES NOT register an Adobe TDB stream type, BEE vector evaluator, Pen editor or native VectorArt output. This is an **in-host preflight** only, NOT the final new vector plug-in.

## User-invoked action

- Creates an independent hierarchical CNL document inside AE's process, with a native procedural ellipse as four double-precision cubic Bezier segments (not rasterized, not a Mask, not built-in Shape).
- Computes the exact loaded TDB.dll SHA256. Calls a known nonmutating private no-argument getter **only** when SHA matches a pinned AE 2025/2026 binary AND getter opcode fingerprint matches.
- Checks *export presence* for the private native factory Creator, register/unregister and canonical query. It does NOT call those exports.
- Does not create an AE layer, effect, project data or shape, and does not mutate the private registry.
- Writes %TEMP%\CNL_NativeVector_HostPreflight.tsv, then displays a short AE info dialog.

## How to use (user installs; researcher never installs or operates AE GUI)

1. Obtain D:\Developer\ShapeLayerAE\build\native_vector_host_probe\Release\CNLNativeVectorHostProbe.aex.
2. Close After Effects, copy to the AE Plug-ins directory, restart.
3. Select Animation > CNL Native Vector: Host Preflight (Read Only). No layer or comp required.
4. Inspect %TEMP%\CNL_NativeVector_HostPreflight.tsv.
5. Expect CNL_double_bezier_cubic_status=0 and CNL_native_cubic_segment_count=4. Native type registration is deliberately 0.

## Build

    cmake -S "D:\Developer\ShapeLayerAE\labs\native_vector_host_probe" -B "D:\Developer\ShapeLayerAE\build\native_vector_host_probe" -G "Visual Studio 17 2022" -A x64
    cmake --build "D:\Developer\ShapeLayerAE\build\native_vector_host_probe" --config Release

This is a bridge between native CNL geometry and the AE plug-in host process, not proof of true AE-native editing. Type/owner/editor/evaluator/renderer contracts remain unsolved. Use a disposable project for tests.


## v2 (2026-10-12): safe preflight for EMPTY disposable project, no private registration

This recompiled safe AEX adds a read-only public-API project isolation check, shared in host_abi_shared/NativeProjectSafety.h. Its TSV now includes disposable_project_gate_pass, disposable_project_gate_reason, project count, number of non-root project items, Render Queue item count and dirty state. The dialog shows empty-project gate PASS/BLOCKED. A blocked result is EXPECTED if your current project contains footage, a composition, an active non-root item or unsaved changes.

To test v2, the USER must replace the previously installed safe AEX with the newly compiled file while After Effects is closed, restart, open a NEW EMPTY project, and run Animation > CNL Native Vector: Host Preflight (Read Only). Send the updated TSV. This does not mutate Adobe TDB/BEE registries.

The previous v1 was successfully tested by the user on AE2026 (2026-10-12 04:12 JST; archive=373 bytes, cubic=4, native getter nonnull); this v2 project gate has NOT YET been tested inside AE.

This project-status predicate alone is NOT a guarantee that native private API mutation is safe.

## v3 shared empty-project gate (2026-10-12)

The rebuilt read-only AEX now also rejects a saved project, even if its contents and dirty flag are empty/clean. This uses public AEGP_GetProjectPath plus MemorySuite1 lock/unlock/free; errors block the gate. This change does NOT involve private registration. The existing v1 user-verified getter result still stands, but this v3 gate has **NOT** been tested inside After Effects. The v3 AEX was compiled and PE-verified offline only.

## v4 (2026-10-12): actual AE2026 v3 preflight and readable failure reason

The user ran the previous v3 read-only AEX inside AE2026; real TEMP TSV was inspected and archived as AEIG EXP-SHAPE-034. Native independent Bezier creation, four cubic segments, 373-byte archive and non-null private getter all succeeded. The empty-project isolation gate returned BLOCKED specifically because AEGP_ProjectIsDirty returned TRUE (`project_dirty`). The other item and Render Queue queries were not reached; they remain unknown, NOT zero.

This v4 safe AEX shows the **actual fail reason** in its info dialog and fails TDB hashing closed on an OS file read error. Build and PE verification pass. This new v4 binary has NOT been runtime tested. It does not call the private mutating TDB registrar or instantiate any Adobe Shape or Mask. The separate CNLPrivateTDBDisposable AEX remains HIGH RISK and should NOT be installed or run merely because the safe getter succeeded.

## v5 (2026-10-12): better full public read-only inventory without relaxing isolation

The shared NativeProjectSafety.h now defers dirty-project and saved-path **rejection** until AFTER read-only checks of the native root, active project item, non-root project items and Render Queue. This is designed to tell apart empty-but-dirty AE projects from projects containing substantive work. Dirty projects and saved projects STILL FAIL. Earlier SDK errors or actual content still fail closed.

The safe AEX TSV now adds `disposable_project_has_saved_path` and `disposable_active_non_root`. The popup includes the exact stop reason. Existing TSV values `-1` represent fields not reached, not zeros. Rebuilt binaries are statically verified, but the new v5 runtime diagnostics are NOT host tested. Do not reinstall the dangerous AEX to test these changes; the read-only AEX is the only appropriate user preflight.
