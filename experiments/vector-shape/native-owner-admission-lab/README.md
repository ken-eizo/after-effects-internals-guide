# CNL Native Owner Admission — READ-ONLY research AEGP

This is an independent AE SDK 25.6 AEGP that examines the real host's existing dynamic stream parent/child hierarchy and `AEGP_CanAddStream` rules. It **never creates, modifies or deletes** a native stream, layer, effect, mask, Shape Contents or TDB factory entry.

Compiled binary (Release):
`D:\Developer\ShapeLayerAE\build\native_owner_admission\Release\CNLNativeOwnerAdmission.aex`

Static verifier: `python labs/native_owner_admission/verify_binary.py`

## User-only optional manual host experiment

1. Close AE, install the AEX in AE2026's Plug-ins folder manually, then restart AE. The researcher will not do this.
2. In a disposable AE project, select an **ordinary AV layer** in the Timeline. Open **Animation > CNL Native Owner: Inspect Admission (Read Only)**. Copy `%TEMP%\CNL_NativeOwner_Admission.tsv` to a name identifying this run.
3. Select a **native Shape Layer** (created manually by the user, not by this plug-in). Run the same command and copy the TSV again under a new name.
4. Optionally select an AV layer with an existing ordinary **Effect** applied. Run once more; save the third TSV.
5. Return all saved TSVs. No need to test `CNLPrivateTDBDisposable.aex` (high risk, NOT recommended).

The AEX walks at most 240 stream nodes at most 4 levels below the layer. Per parent it queries candidate types: unknown Vector Shape name, built-in Shape Group, Fill, Trim, Slider Control, independent CNL group. Reports each node's MatchName, grouping kind, child count, type-admissibility boolean and AEGP errors. `CanAddStream` results mean admission only, **not** construction, owner attachment or Pen/render availability. Some groups may respond with an API error; preserve these results.

All data is local to the user's AE process. The output TSV is replaced each run; save before repeating. The binary has **compiled and passed PE/static source checks**, but **has not yet been tested inside AE**. Direct private BEE/TDB imports are absent; that is not a claim of complete absence of host risk.

## Principal hypothesis being tested

`FLT_Parade::CanStore` calls `TDB_StreamBase::GetCanonicalStream`, then `__RTDynamicCast` from `TDB_StreamBase` to `FLT_FCSeqSpec`; native Effect Parade is therefore type-gated, not merely vector MatchName-prefix-gated. Contrasting that with native Shape Contents' prefix-based CanStore is the concrete experiment. The test cannot register a new subtype or measure the non-public creator ABI.
