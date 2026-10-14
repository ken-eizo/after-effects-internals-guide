# EXP-SHAPE-085 — Public AEGP Paint leaf metadata probe v2

**Status: PASS Windows Release AEX build; CTest 4/4; PiPL/PE/ABI inspection. NOT YET TESTED INSIDE AE with v2 metadata calls.**

Updated read-only `ChapePaintNativeInspector.cpp`, retaining existing Paint native hierarchy traversal and CanAdd read-only matrix, adding:
- `AEGP_GetStreamType` (actual value type).
- `AEGP_CanVaryOverTime` and `AEGP_IsStreamTimevarying`.
- `AEGP_GetStreamNumKFs` for leaf Streams whose type is not `AEGP_StreamType_NO_DATA`.

New TSV `leaf_meta` rows and `metadata_leaves` / `metadata_query_errors` totals. Tool does not set/create/delete/reorder Stream values or keys.

Build / offline checks:
```powershell
cmake --build D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype --config Release
ctest --test-dir D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype -C Release --output-on-failure
python D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype\verify_native_shape_aex.py
python D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\verify_paint_sdk_and_inspector.py
```
Result 4/4 tests PASS, static PE inspector PASS, AEX SHA256 `392359b2c7216d2d284c2207a623d3b58bc60c1cb37137e72fe9b7c1d9a53c3a`.

**Host run cannot be claimed**: the previous F-VECTOR-083 TSV came from v1 and does not include `leaf_meta`. No Adobe installed AEX was overwritten in this session, no Adobe production process terminated, and no private Adobe ABI was invoked.

Details `research/findings/F-VECTOR-085-paint-native-leaf-keyframe-metadata-probe.md`.
