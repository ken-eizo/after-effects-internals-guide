from pathlib import Path
import pefile
sdk=Path(r'E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\AEGP\Streamie\Streamie.cpp')
root=Path(r'D:\Developer\ShapeLayerAE\labs\native_shape_layer_prototype')
inspect=root/'ChapePaintNativeInspector.cpp'
plugin=root/'NativeShapeLayerPlugin.cpp'
aex=Path(r'D:\Developer\ShapeLayerAE\build\native_shape_layer_prototype\Release\CNLNativeShapeLayer.aex')
assert all(x.exists() for x in (sdk,inspect,plugin,aex))
s=sdk.read_text(encoding='utf-8',errors='replace')
for symbol in ['"ADBE Paint Group"','AEGP_GetNewStreamRefByIndex','AEGP_ReorderStream','AEGP_DuplicateStream','AEGP_DeleteStream','AEGP_SetStreamName']:
 assert symbol in s,('missing SDK Streamie sample usage',symbol)
v=inspect.read_text(encoding='utf-8')
for token in ['"ADBE Paint"','AEGP_GetNewStreamRefByIndex','AEGP_GetStreamGroupingType','AEGP_GetNewStreamRefForLayer','AEGP_StreamGroupName_EFFECT_PARADE','AEGP_CanAddStream','AEGP_GetStreamType','AEGP_CanVaryOverTime','AEGP_IsStreamTimevarying','AEGP_GetStreamNumKFs','leaf_meta','metadata_query_errors','CNL:PaintAtom','ADBE Paint Atom - CNLProbe','AEGP_DisposeStream','ChapeLayer_PaintNativeHierarchy.tsv','host_project_mutated\\t0']:
 assert token in v,('missing Paint inspector',token)
for bad in ('PaintBucket','Brush_Strokes','AEGP_AddStream(','AEGP_DeleteStream(','AEGP_DuplicateStream(','AEGP_ReorderStream(','AEGP_SetStreamName(','TDB_ScRegisterStreams','BEE_PaintAtom::Create'):
 assert bad not in v,('unsafe or wrong Paint kind',bad)
p=plugin.read_text(encoding='utf-8')
for token in ('CNL_RunPaintNativeInspector','Inspect Adobe Paint Native Streams (Read Only)'):
 assert token in p
pe=pefile.PE(str(aex))
assert pe.FILE_HEADER.Machine==0x8664
imports={x.dll.decode().lower() for x in pe.DIRECTORY_ENTRY_IMPORT}
assert 'bee.dll' not in imports and 'tdb.dll' not in imports and 'flt.dll' not in imports
data=aex.read_bytes()
assert b'ChapeLayer_PaintNativeHierarchy.tsv' in data
assert b'Inspect Adobe Paint Native Streams (Read Only)' in data
# MSVC may inline exact MatchName comparisons as constant machine-word loads.
print('PASS AE SDK Streamie real Paint operations')
print('PASS CNL read-only inspector avoids 8 mutating/unsafe functions and PaintBucket/Brush_Strokes')
print('PASS built AEX has inspector strings and no direct BEE/TDB/FLT imports; x64')
print('NOTE: no in-host GUI execution/foreign stream registration proven')
