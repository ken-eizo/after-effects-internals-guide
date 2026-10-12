# CNL Native Effect Stream Identity — read-only AEGP

**Status:** v1 executed in real AE2026 and produced internal param_index=0 verification errors; v2 patched to NEVER query index 0. v2 compiled and passed offline static PE/source checks; v2 not yet executed in AE2026.

**v2 correction:** user-run TSV showed `target_effect=5`. Index 0 yielded A_Err=3 for both GetEffectParamUnionByIndex and GetNewEffectStreamByIndex, producing two host assertion dialogs even though SDK docs describe input index 0. Values 1..4 succeeded, including PF_Param_ARBITRARY_DATA=11 and AEGP_StreamType_ARB=7 at index 1. The v2 code emits `param_skipped 0` and iterates only indices 1..N-1. Stream unique IDs returned 0 for every supported param in the v1 capture; do NOT claim these are per-param unique IDs.

This new independent AEGP exists because the real user's `CNL_NativeOwner_Admission.tsv` **positively confirms `CNL Owned Vector Document` under a native `ADBE Effect Parade`** with exactly five effect-leaf parameters, while its direct `CanAddStream` tests for arbitrary CNL Contents return false.

This inspector uses Adobe's **public SDK only** to find that exact effect by installed MatchName and ask the host for its actual `PF_ParamType`, `AEGP_StreamType`, unique stream ID, keyframe-eligibility, and MatchName for each official param index. The v1 real-host TSV **confirmed** index 1 is `PF_Param_ARBITRARY_DATA` (numeric 11) / `AEGP_StreamType_ARB` (numeric 7); v2 is intended to confirm the same without any index-0 calls. The five indices should map input=0, document=1, stroke=2, color=3, clear=4.

### No mutations or opaque memory dereference

The inspection does not call `AEGP_SetStreamValue`, `AEGP_AddStream`, `AEGP_DeleteStream`, `AEGP_ApplyEffect`, or any `AEGP_GetNewStreamValue` on the opaque arbitrary payload. It never invokes BEE/FLT/TDB private registration. It only reads metadata and disposes the transient public AEGP effect/stream references. Its own menu-command registration is a normal public AEGP initialization operation.

### Optional manually controlled AE2026 test

1. On a **disposable** composition, keep `CNL Owned Vector Document` installed and applied on a selected Timeline layer.
2. Close AE; manually install ONLY `CNLArchiveIdentity.aex` from `D:\Developer\ShapeLayerAE\build\native_owned_archive_identity\Release\CNLArchiveIdentity.aex` in the AE plug-ins folder.
3. Restart AE2026. Select the same Timeline layer.
4. Run **Animation 竊・CNL Effect: Inspect Native Stream Identity (Read Only)**.
5. The new report is `%TEMP%\CNL_OwnedEffect_StreamIdentity_v2.tsv`. Share its **whole text**. It contains effect match names, param types and IDs, not pixel contents or project data.
6. For persistence testing, *on a disposable project only*, separately try saving/closing/reopening and run the inspector again; preserve the first TSV before running a second time. Record whether the CNL effect still draws a Bezier ellipse after reopening, and whether Stroke Width / Stroke Color still work.

**Never run the unrelated `CNLPrivateTDBDisposable.aex`.** The agent never operates AE itself or installs plugins. This is not the final native Pen/TDB Contents/BEE renderer.

### Offline build

Requires VS2022 x64, CMake, local AE SDK 25.6 and local SDK PiPLTool, plus Python and `pefile`.

```powershell
cmake -S D:\Developer\ShapeLayerAE\labs\native_owned_archive_identity -B D:\Developer\ShapeLayerAE\build\native_owned_archive_identity -G "Visual Studio 17 2022" -A x64
cmake --build D:\Developer\ShapeLayerAE\build\native_owned_archive_identity --config Release --parallel 4
python D:\Developer\ShapeLayerAE\labs\native_owned_archive_identity\verify_readonly.py
```

From the independently archived source in AEIG, use the archive directory as `-S`, a separate build directory as `-B`, and set `CNL_EFFECT_IDENTITY_AEX` and `CNL_EFFECT_IDENTITY_RECEIPT` for the verification script.
