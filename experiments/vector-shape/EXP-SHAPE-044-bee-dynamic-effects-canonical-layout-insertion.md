---
status: pass-static-two-native-binaries
last_verified: 2026-10-12
evidence: E2-L
---

# EXP-SHAPE-044 — Native DynamicStreamEffectsParser directly inserts Canonical UI children

## Research question

Does Adobe's BEE dynamic effects parser merely reference the native FLT/TDB layout API, or does the parser actually issue instructions to insert children into a host-owned TDB canonical group?

## Reproduction

1. Read the AE2026 top-level Support Files DLL/EXE import tables; inventory the FLT/TDB AddStreamToUILayout routines and record **scope** (443 files, zero parse failures). Imported symbol presence alone is not sufficient proof of a call.
2. Read pinned installed AE2025/AE2026 BEE.dll and FRP.dll images. Decode executable `FF15` and `FF25` relative memory operands and match the resolved IAT RVAs against genuine named imports. Map each callsite to a .pdata bounded caller and annotate local register setup.
3. Assert precisely two **CALL** instructions to `TDB_StreamGroup::AddStreamToUILayout` from `BEE::ae::DynamicStreamEffectsParser::EndEffect` per version. Assert `RCX/RDX/R8D` argument setup and distinguish all `JMP` import thunks in FRP/BEE. Compare both installed binaries.
4. Do not load Adobe DLLs in any process, call private ABI, patch code, create a host vector stream, or operate the AE GUI.

## Results

PASS. Real parser end-of-definition native TDB Append CALLs:

| Version | Parser function RVA | Calls |
| --- | --- | --- |
| AE2025 | `0x2f6800` | `0x2f6cbf`, `0x2f6d1a` |
| AE2026 | `0x2ff440` | `0x2ff8d9`, `0x2ff92a` |

The inspected `FRP.dll` `FLT_FCSeqSpec::AddStreamToUILayout` import occurrences are JMP thunks rather than actual known method callers. Other two BEE parser-independent native functions perform additional direct TDB layout insertion; see the full dataset and F-VECTOR-043.

## Limitations and consequence

The parser's actual recognized parameter-type set and any external registration boundary remain unproven. It has not been established that custom native vector path groups can be created or managed through this runtime parser, that new Type MatchNames can be safely registered, or that native editing/rendering can be attached. This is an actual **native UILayout producer** to investigate further, rather than a completed third-party plugin interface.

Artifacts: `research/findings/F-VECTOR-043-native-dynamic-effect-parser-canonical-layout-insertion.md`; 3 datasets and 3 tools named in the finding. No AE host installation/test performed in this experiment.

## Separate base-group creator check

AE2025/2026 `DynamicStreamEffectsParser::CreateEffectGroup` base implementation is an immediate null return (`xor eax,eax; ret`). That is an E2-L proof about this one class body only, not evidence that no derived parser/group creator exists anywhere. No independent native vector group was created in this experiment.
