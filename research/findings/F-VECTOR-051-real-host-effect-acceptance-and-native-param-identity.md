---
date: 2026-10-12
status: real-AE2026-host-observed-owner-bridge-plus-next-readonly-probe-built
evidence: H actual user-run AEGP log + E2-L public SDK and two offline AEX builds
---

# F-VECTOR-051 — AE2026 accepted CNL effect, created five real parameter streams; dynamic native Contents insertion is rejected

## Decisive real-host evidence

The user's After Effects 2026 screenshot shows the public-only `CNL Native Owner Admission` probe reporting `%TEMP%/CNL_NativeOwner_Admission.tsv`. We read the actual freshly written **21,353 byte, 2026-10-12 13:23:48** Windows log from the authorized PC, rather than inferring results from the dialog.

The native AEGP walk of the selected AV layer recorded:

- Root `ADBE AV Layer`, `layer_object_type=0`.
- Its genuine indexed `ADBE Effect Parade` contains **`CNL Owned Vector Document`** (the new project-owned public Effect AEX's MatchName).
- `CNL Owned Vector Document` is a **named stream group**, with **6 children**: five leaf streams `CNL Owned Vector Document-0000` through `-0004`, plus `ADBE Effect Built In Params` as a child group.
- 173 streams visited in the real host; `private_registry_invoked=0` and `stream_created=0`.
- All tested `AEGP_CanAddStream` candidates directly on the CNL Effect named group were **false**: invented CNL Vector Shape/Group, built-in Shape Group/Fill/Trim, `ADBE Slider Control` and `CNL Native Independent Group`.
- The *parent Effect Parade* admits `ADBE Slider Control` in this test, but rejects `CNL Native Independent Group`. This demonstrates admission depends on parent schema. It is NOT proof that attempting to add any candidate would succeed or be safe.
- Other generic layer groups (notably `ADBE Data Group`) can answer true to a broad name test; that does not imply executable or persistent native CNL Vector types.

**Strong result:** the actually compiled plugin has an accepted Effect owner under the genuine Adobe Effect Parade, with five real host-visible parameter stream leaves, without any Shape Layer or Mask creation. This is substantially stronger than the offline-only F-VECTOR-049 claim: the Effect is present in a user-run AE2026 project. The log does not prove it successfully renders, saves/reopens or supports native Pen.

## Closed public API extension boundary

The CNL Effect is a **named group**, not a dynamic indexed Contents parent. `AEGP_AddStream` is documented only for `AEGP_StreamGroupingType_INDEXED_GROUP`; this named Effect group currently rejects every tested vector/CNL type even at the `AEGP_CanAddStream` gate. Therefore naïvely appending an independently named native Bezier Contents stream under an arbitrary Effect parameter container via public AEGP **does not work in this host configuration**.

The SDK `AEGP_StreamSuite6::AEGP_GetStreamType` exposes enum `AEGP_StreamType_ARB`, while `AEGP_EffectSuite5::AEGP_GetEffectParamUnionByIndex` returns `PF_ParamType` (including `PF_Param_ARBITRARY_DATA`) for a parameter index. The header explicitly restricts `AEGP_SetStreamValue` to primitive types and excludes `AEGP_ArbBlockVal`. Thus, even though the native `FLT_ParamArbDataStream` wrapper exists (F-VECTOR-050), generic public AEGP stream setters are not a demonstrated path to writing vertices inside that opaque blob.

## New specialized public-SDK executable

Rather than mutating Adobe's registries, compiled `CNLArchiveIdentity.aex` as a **separate read-only AEGP** (two fresh independent MSVC x64 builds both passed). It scans only the selected layer and finds specifically installed Effect MatchName `CNL Owned Vector Document`, then uses *documented* SDK:

- `AEGP_GetEffectNumParamStreams` and `AEGP_GetNewEffectStreamByIndex` to correlate the real Effect parent with parameter indices.
- `AEGP_GetEffectParamUnionByIndex` for the actual PF parameter type (without reading the union's values).
- `AEGP_GetStreamType` for native type; `AEGP_GetUniqueStreamID` for native stream identity; `AEGP_CanVaryOverTime` for animation capability; `AEGP_GetMatchName` for name. All returned references are disposed.
- Does **not** call `AEGP_GetNewStreamValue` on an Arbitrary payload, nor any stream writer, effect creator, Shape/Mask producer, private TDB/BEE/FLT code.

**Expected but not yet verified by live host:** index 1 of the CNL effect has PF type `PF_Param_ARBITRARY_DATA=11` and AEGP stream type `AEGP_StreamType_ARB=7`; 0 input, 2 stroke, 3 color, 4 clear checkbox. The test is designed to falsify those assumptions and expose true unique IDs.

AEX: `D:/Developer/ShapeLayerAE/build/native_owned_archive_identity/Release/CNLArchiveIdentity.aex`. Manual user-only AE test via Animation → `CNL Effect: Inspect Native Stream Identity (Read Only)`; result `%TEMP%/CNL_OwnedEffect_StreamIdentity.tsv`. **No installation or in-host execution of this new AEX has yet occurred.**

## Artifacts and constraints

- `datasets/ae-cnl-owned-effect-actual-host-admission-sanitized-20261012.json` — selected layer's matched Effect subtree summary, without unrelated project metadata.
- `experiments/vector-shape/probe-src/tools/summarize_cnl_live_owner_trace.py` — reproducible parser of the original user's log.
- `experiments/vector-shape/native-owned-effect-identity-lab/` — standalone source, CMake/PiPL, README, read-only verifier.
- `datasets/ae-cnl-native-effect-id-aex-original-offline-20261012.json`, `datasets/ae-cnl-native-effect-id-aex-independent-offline-20261012.json`.

Never confuse the accepted ordinary Effect with a first-class independent VectorLayer/Contents or Pen/VectorArt bridge. F-VECTOR-025/037/038/039/050 remain relevant blockers; Phase F and CompNodeAE must not be touched.
