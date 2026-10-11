"""Patch ShapeLayerAE v3: opt-in unknown match-name admissibility and UID sentinel retest.
No native streams created/mutated and no private code called.
"""
from pathlib import Path
p=Path(r"D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp")
s=p.read_text(encoding="utf-8")
def rep(old,new):
    global s
    assert s.count(old)==1,(old[:110],s.count(old))
    s=s.replace(old,new,1)
rep("static AEGP_Command g_command = 0;","static AEGP_Command g_command = 0;\nstatic AEGP_Command g_unknown_command = 0;\nstatic bool g_probe_unknown = false;")
rep("    int32_t unique_id = -1;", """    // Sentinel controls detect a host implementation that leaves the out-param
    // unchanged. Two independent calls are observational only.
    int32_t unique_id = 0x13579BDF;
    int32_t unique_id2 = 0x02468ACE;""")
rep("    A_Err e_id = s.StreamSuite6()->AEGP_GetUniqueStreamID(ref, &unique_id);",
    "    A_Err e_id = s.StreamSuite6()->AEGP_GetUniqueStreamID(ref, &unique_id);\n    A_Err e_id2 = s.StreamSuite6()->AEGP_GetUniqueStreamID(ref, &unique_id2);")
rep("    fprintf(metadata,\n            \"%d\\t%ld\\t%ld\\t%ld\\t%d\\t%ld\\t%lu\\t%d\\t%ld\\t%ld\\t%ld\\t%ld\\t%ld\\t%s\\n\",",
    "    fprintf(metadata,\n            \"%d\\t%ld\\t%ld\\t%ld\\t%d\\t%ld\\t%lu\\t%d\\t%ld\\t%ld\\t%ld\\t%ld\\t%ld\\t%s\\t%ld\\t%ld\\n\",")
rep('            (long)(e_modified?e_modified:e_type),match?match:"");',
    '            (long)(e_modified?e_modified:e_type),match?match:"",\n            (long)unique_id2,(long)e_id2);')
rep("""        for (const char* candidate : known) {
            A_Boolean allowed = FALSE;
            A_Err e = s.DynamicStreamSuite2()->AEGP_CanAddStream(ref, candidate, &allowed);
            fprintf(addcaps,"%ld\\t%s\\t%s\\t%d\\t%ld\\n",
                    (long)unique_id,match?match:"",candidate,
                    (int)allowed,(long)e);
        }""",
"""        for (const char* candidate : known) {
            A_Boolean allowed = FALSE;
            A_Err e = s.DynamicStreamSuite2()->AEGP_CanAddStream(ref, candidate, &allowed);
            fprintf(addcaps,"%ld\\t%s\\t%s\\t%d\\t%ld\\n",
                    (long)unique_id,match?match:"",candidate,
                    (int)allowed,(long)e);
        }
        // This special probe runs ONLY from the separate explicit menu command.
        // Prefix hypotheses are tested without creating any stream objects.
        if (g_probe_unknown) {
            static const char* unknown[] = {
                "ADBE Vector Shape - ShapeLayerAEProbe",
                "ADBE Vector Graphic - ShapeLayerAEProbe",
                "ADBE Vector Filter - ShapeLayerAEProbe",
                "ADBE Vector Group - ShapeLayerAEProbe",
                "ShapeLayerAE Custom Stream",
                "ADBE Vector Filter - Repeater"
            };
            for (const char* candidate : unknown) {
                A_Boolean allowed = FALSE;
                A_Err e = s.DynamicStreamSuite2()->AEGP_CanAddStream(ref, candidate, &allowed);
                fprintf(addcaps,"%ld\\t%s\\t%s\\t%d\\t%ld\\n",
                        (long)unique_id,match?match:"",candidate,(int)allowed,(long)e);
            }
        }""")
rep("static A_Err DumpActiveLayer() {", "static A_Err DumpActiveLayer(bool unknown_names = false) {\n    g_probe_unknown = unknown_names;")
rep('    FILE* canadd = fopen((base + "\\\\ShapeLayerAE_canadd.tsv").c_str(), "wb");',
    '    FILE* canadd = fopen((base + (unknown_names ? "\\\\ShapeLayerAE_canadd_unknown.tsv" : "\\\\ShapeLayerAE_canadd.tsv")).c_str(), "wb");')
rep('    if (meta) fprintf(meta, "depth\\tindex\\tparent_stream_uid\\tunique_stream_id\\tgrouping\\tsdk_depth\\tdynamic_flags\\tis_modified\\tleaf_stream_type\\tuid_error\\tdepth_error\\tflags_error\\tother_error\\tmatch_name\\n");',
    '    if (meta) fprintf(meta, "depth\\tindex\\tparent_stream_uid\\tunique_stream_id\\tgrouping\\tsdk_depth\\tdynamic_flags\\tis_modified\\tleaf_stream_type\\tuid_error\\tdepth_error\\tflags_error\\tother_error\\tmatch_name\\tuid_second_call\\tsecond_uid_error\\n");')
rep("    if (canadd) fclose(canadd);\n    s.UtilitySuite3()", "    if (canadd) fclose(canadd);\n    g_probe_unknown = false;\n    s.UtilitySuite3()")
rep("""    if (command != g_command || already_handled) return A_Err_NONE;
    if (handled) *handled = TRUE;
    return DumpActiveLayer();""",
"""    if (already_handled || (command != g_command && command != g_unknown_command))
        return A_Err_NONE;
    if (handled) *handled = TRUE;
    return DumpActiveLayer(command == g_unknown_command);""")
rep("""    if (layer) return s.CommandSuite1()->AEGP_EnableCommand(g_command);
    return s.CommandSuite1()->AEGP_DisableCommand(g_command);""",
"""    if (layer) {
        s.CommandSuite1()->AEGP_EnableCommand(g_unknown_command);
        return s.CommandSuite1()->AEGP_EnableCommand(g_command);
    }
    s.CommandSuite1()->AEGP_DisableCommand(g_unknown_command);
    return s.CommandSuite1()->AEGP_DisableCommand(g_command);""")
rep("""    if (!err) err = s.RegisterSuite5()->AEGP_RegisterCommandHook(
        g_id, AEGP_HP_BeforeAE, AEGP_Command_ALL, CommandHook, nullptr);""",
"""    if (!err) err = s.CommandSuite1()->AEGP_GetUniqueCommand(&g_unknown_command);
    if (!err) err = s.CommandSuite1()->AEGP_InsertMenuCommand(
        g_unknown_command, "ShapeLayerAE: Probe Unknown Shape Names (Experimental)",
        AEGP_Menu_ANIMATION, AEGP_MENU_INSERT_AT_TOP);
    if (!err) err = s.RegisterSuite5()->AEGP_RegisterCommandHook(
        g_id, AEGP_HP_BeforeAE, AEGP_Command_ALL, CommandHook, nullptr);""")
p.write_text(s,encoding="utf-8")
print("PATCHED v3",p,"lines",len(s.splitlines()))
