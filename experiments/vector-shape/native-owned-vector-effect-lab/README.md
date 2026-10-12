# CNL Owned Vector Document — isolated public-SDK AE effect

**Status: Release AEX built; executable host-mock and PE/PiPL verification PASS. NOT tested inside After Effects yet.**
**NOT Adobe's native Vector Contents / Pen tool / BEE_VectorArt implementation.**

This experiment is a **real newly compiled Adobe Effect AEX** that owns a native CNL vector document as an independent, per-effect `PF_Param_ARBITRARY_DATA` value. The separate CNL core uses stable 64-bit IDs, arbitrarily nested Group/Path hierarchies, double-precision cubic Bezier data, and a versioned checksum-checked archive. Unlike the earlier visible Vector Effect, it does NOT query an external PICA producer or use any Shape/Mask layer to store geometry.

It also does NOT create a genuine host TDB Contents hierarchy. The hidden arbitrary parameter is a legitimate *Effect parameter*, not a user-visible native Contents child or AE Pen target. Rendering uses the public Effect SDK's **8-bpc CPU PF_World**. AE's native `BEE_VectorArt` or `RenderGraph` is not used.

## Tested concrete capabilities

The compiled `CNLOwnedVectorEffect.aex` registers a hidden archive and standard Stroke Width, Stroke Color and Transparent Input controls. The initial CNL archive has root Contents, a child group and a four-cubic ellipse. The archive is owned by the Effect's arbitrary parameter, so unlike volatile external provider geometry it is supplied to AE's normal parameter serialization callbacks.

Implemented `PF_Arbitrary_*` callbacks: NEW, DISPOSE, COPY, FLAT_SIZE, FLATTEN, UNFLATTEN, INTERP, COMPARE, PRINT_SIZE, PRINT, SCAN. Binary archives are validated by the CNL deserializer before allocation; arbitrary data is size capped at 1 MiB; corrupted and truncated archives are rejected. PRINT/SCAN are reversible uppercase hexadecimal `CNLVEC1:` plus checksum-protected CNL archive. Interpolation is intentionally **step/discrete**, not vector vertex morphing.

Offline host-mock opens the separately compiled AEX, calls actual `EffectMain` selectors, mocks AE host handles, creates an unrelated deeply nested CNL document with two separate ellipses through the AEX-exported C ABI, roundtrips it through UNFLATTEN, checks archive inequality, renders it and asserts a **different raster hash**. Also tests default copy/flatten/unflatten, corrupted bytes, truncated data, PRINT/SCAN equality and malformed text, stroke-width effect on output, source-compositing and handle release with zero outstanding test handles.

See `verify_owned_vector_aex.py` and `OwnedVectorHostMock.cpp`. These are **not** proof of an actual AE project save/reopen or in-host undo; that requires user-run disposable project testing.

## Build on the Windows development machine

Requires Visual Studio 2022 x64, CMake, Python with `pefile`, and the **user's own** Adobe AE SDK 25.6 at `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples` (or configure `AE_SDK_EXAMPLES`). No SDK binaries are redistributed. `build_pipl.py` invokes the locally installed SDK PiPLTool.

```powershell
cmake -S D:\Developer\ShapeLayerAE\labs\native_vector_document_effect -B D:\Developer\ShapeLayerAE\build\native_vector_document_effect -G "Visual Studio 17 2022" -A x64
cmake --build D:\Developer\ShapeLayerAE\build\native_vector_document_effect --config Release --parallel 4
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_vector_document_effect -C Release --output-on-failure
python D:\Developer\ShapeLayerAE\labs\native_vector_document_effect\verify_owned_vector_aex.py
```

**AEX:** `D:\Developer\ShapeLayerAE\build\native_vector_document_effect\Release\CNLOwnedVectorEffect.aex`

To build the standalone archived experiment from AEIG, use `cmake -S <archive-lab-path> -B <archive-lab-path>/build -G ...`, then run `ctest`. The verification script defaults to the local `build/Release` on the standalone archived path; alternatively set `CNL_OWNED_EFFECT_BUILD` to the chosen build directory (without the Release subdirectory).

## Optional host validation — manual only

The agent does **not** install AEX files or operate the AE GUI. If the user chooses to test: use **AE 2026, a disposable unsaved project**; manually install this **public-SDK-only** AEX and restart AE. Add a new composition and Solid Layer, then apply **CNL Research → CNL Owned Vector Document (Research)**. Confirm a centered thin ellipse is drawn over transparency (default), that Stroke Width/Color visibly work, that preserving source works, and that save → close → reopen on this **disposable project** preserves it. Report the About text, appearance and any error/dialog.

Do **NOT** test `CNLPrivateTDBDisposable.aex` (unrelated high-risk private-registry experiment). Never use important projects for first tests. The current Effect does **not** expose its stored CNL geometry for AE-native Pen editing. The initial ellipse geometry is not editable in native Contents, only the public stroke/color controls are UI-editable today.

## Remaining true product gates

1. Safely create an **independently host-owned native TDB Contents parent/child** rather than just an Effect arbitrary blob.
2. Associate authentic `BEE_Layer` + `TDB_StreamIDPath` native selection, transform and Pen vertex editing with **the CNL-owned paths**, not Mask or Shape stand-ins.
3. Connect independent native group geometry to `BEE_VectorArt`, AE RenderGraph and native selection/Undo/snapshot/unload lifetime.
4. Only **AFTER Phase E** evaluate Phase F design with the user. `D:\Developer\CompNodeAE` remains untouched.

This lab is a solid, repeatable data persistence + Effect renderer **foundation**, not a claim that the target AE native Gizmo/Contents/Pen/VectorArt is complete.
