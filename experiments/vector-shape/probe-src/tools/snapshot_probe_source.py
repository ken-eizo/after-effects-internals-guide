from pathlib import Path
import shutil,hashlib,json
src=Path(r'D:\Developer\ShapeLayerAE')
dst=Path(r'D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src')
files=['CMakeLists.txt','README.md','src/ShapeLayerProbe.cpp','src/ShapeLayerProbe_PiPL.r','tools/build_pipl.py','tools/audit_symbols.py','tools/audit_bee_disasm.py','tools/compare_vector_lineage.py','tools/analyze_registerstreams.py','tools/trace_registerstreams_xrefs.py','tools/inspect_registration_dispatch.py','tools/scan_factory_extensions.py','tools/audit_origin_identity.py','tools/trace_vector_selection_xrefs.py','tools/trace_vector_layer_creation.py','tools/archive_host_probe.py','tools/upgrade_probe_v2.py','tools/archive_host_probe_v2.py','tools/audit_tdb_factory.py','tools/locate_tdb_library.py','tools/probe_tdb_imports.py','tools/scan_shape_factory_inventory.py','tools/trace_bee_tdb_iat.py','tools/trace_tdb_factory_semantics.py','tools/trace_vector_canstore.py','tools/decode_canstore_constants.py','tools/record_vector_canstore_literals.py','tools/upgrade_probe_v3.py','tools/upgrade_private_getter.py','tools/update_manifests_v3.py','tools/print_factory_disassembly.py','tools/snapshot_probe_source.py','tools/verify_research.py','tools/archive_host_probe_v3.py','tools/reconcile_v3_host_manifest.py','tools/audit_vector_render_editor_boundary.py','tools/trace_vector_creator_xrefs.py','tools/group_creator_xrefs_by_unwind.py','tools/trace_creator_registration_bundles.py','tools/trace_vectorart_render_entrycalls.py']
rows=[]
for rel in files:
    source=src/rel
    target=dst/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    rows.append({'path':rel,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(dst/'SOURCE_SNAPSHOT.json').write_text(json.dumps({'source_directory':str(src),'purpose':'2026-10-11 reproducible source-only snapshot; no Adobe SDK/DLL redistribution','files':rows},indent=2)+'\n',encoding='utf-8')
print('COPIED',len(rows),'source files to',dst)
