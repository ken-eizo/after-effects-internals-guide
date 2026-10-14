# EXP-SHAPE-087 — Read actual AE2026 Paint Stream value kinds and host keyframe metadata

**PASS in host, public AEGP read-only experiment.**

User executed built CNL Paint inspector v2 in AE2026; original %TEMP% TSV was copied byte-for-byte and verified SHA-256.

Results: 6 Brush atoms; 170 native Stream nodes; 142 leaf metadata; 109 can-vary; 0 currently keyframed or time-varying; 0 API errors.

The **Path** leaf `ADBE Paint Shape` returns `AEGP_StreamType_NO_DATA` (0) while `CanVaryOverTime` is TRUE. The public SDK cannot read its special value via ordinary `AEGP_GetNewStreamValue`. This is a real Adobe-owned native path but not a user-defined TDB class.

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_host_v2_receipt.py"
```

SHA-256: `860f60b2d25b57ebe698afa778dcee1cba06cfac76e0060f91f11a34ef529553`.
Dataset: `datasets/ae-paint-native-hierarchy-host-v2-2026-20261014.tsv` and summary JSON.

**Does not prove foreign native Stream registration**, AEP persistence or Timeline ownership. See F-VECTOR-087.
