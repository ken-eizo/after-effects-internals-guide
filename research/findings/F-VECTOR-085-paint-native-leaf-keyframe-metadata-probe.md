---
date: 2026-10-14
status: PASS offline Release AEX build, CTest 4/4, PE safety verification; new metadata query has NOT been run in live AE
evidence: E2-L compiled Windows x64 C++/PiPL plugin, installed SDK 25.6 public headers, static PE guard, no private host calls
---
# F-VECTOR-085 — Extend public Paint native hierarchy probe to inspect actual AE value types and keyframe ownership

## Implementation

Updated `D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype/ChapePaintNativeInspector.cpp` to keep the existing read-only `Animation > ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)` command but add a separate `leaf_meta` row per actual leaf.

The additional **public Adobe 25.6 AEGP functions** are:
- `StreamSuite2()->AEGP_GetStreamType`: value type (NO_DATA, OneD, TwoD, Color, Mask etc).
- `StreamSuite2()->AEGP_CanVaryOverTime`: native ability to animate.
- `StreamSuite2()->AEGP_IsStreamTimevarying`: current time variation including expressions.
- `KeyframeSuite5()->AEGP_GetStreamNumKFs`: number of native AE keyframes, skipped when Stream type is NO_DATA.

The original `node`, `can_add`, `paint_found`, source MatchName, group kind, counts and error rows remain intact, but the output format is now **v2**. This changes only the CNL research AEX source under ShapeLayerAE, **not** Adobe's built-in Paint.aex, libraries or production projects.

Output is `%TEMP%/ChapeLayer_PaintNativeHierarchy.tsv`. New records:
```text
leaf_meta <path> <stream_value_type_enum> <can_vary> <currently_timevarying> <value_type_is_data> <keyframe_count> <err_type> <err_can_vary> <err_time_varying> <err_keyframes>
metadata_leaves <N>
metadata_query_errors <N>
```

These fields are intended to demonstrate host-native property ownership/animation of existing Paint leaves, not foreign type creation. `GetStreamGroupingType=NONE` is **not** the same as `AEGP_StreamType_NO_DATA` (mistaken equivalence avoided in F-VECTOR-083).

## Tests and limitations

- MSVC Windows x64 Release build **PASS**.
- Existing four CNL native CTest suites **4/4 PASS**.
- CNL AEX PiPL/x64/37 exported C ABI and no direct BEE/TDB/FLT import verification **PASS**.
- Static SDK source and read-only inspector guard **PASS**.
- Latest AEX SHA-256 `392359b2c7216d2d284c2207a623d3b58bc60c1cb37137e72fe9b7c1d9a53c3a` (after v2 leaf metadata update).

**No in-host execution of the v2 metadata read has been performed.** The previous in-host Paint hierarchy proof (F-VECTOR-083) is genuine but from the **older v1 inspector**. No host keys/values, save/reopen, or expression results may be invented.

The active AE process is not restarted, and the currently loaded installed AEX is not automatically overwritten. The user must intentionally deploy the new research AEX in a safe test installation/project after AE is closed before new host metadata can be measured.

The legitimate source of the new methods is the installed `AE_GeneralPlug.h` and legacy `AE_GeneralPlugOld.h`; neither SDK provides a foreign `TDB_StreamBase` factory-registration API.

Repro:
```powershell
cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
python D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\verify_native_shape_aex.py
python D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\verify_paint_sdk_and_inspector.py
```

A source snapshot is maintained at `experiments/vector-shape/probe-src/tools/ChapePaintNativeInspector.cpp` for independent review.
