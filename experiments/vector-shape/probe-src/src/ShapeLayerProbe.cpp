// ShapeLayerAE: read-only public AEGP observatory probe.
// This is deliberately NOT a private native stream type factory.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include <cstdio>
#include <cstring>
#include <ctime>
#include <cstdlib>
#include <string>

static SPBasicSuite* g_basic = nullptr;
static AEGP_PluginID g_id = 0;
static AEGP_Command g_command = 0;
static const int kMaxDepth = 24;
static const int kMaxNodes = 20000;

static void Emit(FILE* out, int depth, const char* where,
                 long index, long grouping, long childCount,
                 const char* match, const char* display, long err) {
    fprintf(out, "%d\t%s\t%ld\t%ld\t%ld\t%s\t%s\t%ld\n",
            depth, where, index, grouping, childCount,
            match ? match : "", display ? display : "", err);
}

// AEGP stream refs must be disposed by the caller. Root is owned by caller.
static void Visit(AEGP_SuiteHandler& s, AEGP_StreamRefH ref,
                  FILE* out, int depth, long index, int& count) {
    if (!ref || depth > kMaxDepth || count >= kMaxNodes) return;
    ++count;
    AEGP_StreamGroupingType grouping = AEGP_StreamGroupingType_NONE;
    A_long children = 0;
    A_char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE] = {0};
    A_char name[1024] = {0};
    A_Err e1 = s.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(ref, &grouping);
    A_Err e2 = s.DynamicStreamSuite2()->AEGP_GetMatchName(ref, match);
    A_Err e3 = s.StreamSuite2()->AEGP_GetStreamName(ref, FALSE, name);
    A_Err e4 = 0;
    // NONE=-1, LEAF=0, NAMED_GROUP=1, INDEXED_GROUP=2.
    // GetNumStreamsInGroup on LEAF invokes AE's internal verification failure.
    const bool is_group = !e1 &&
        (grouping == AEGP_StreamGroupingType_NAMED_GROUP ||
         grouping == AEGP_StreamGroupingType_INDEXED_GROUP);
    if (is_group)
        e4 = s.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(ref, &children);
    Emit(out, depth, "stream", index, (long)grouping, (long)children,
         e2 ? "(match-query-error)" : match,
         e3 ? "(name-query-error)" : name,
         (long)(e1 ? e1 : (e2 ? e2 : (e3 ? e3 : e4))));
    if (e1 || e4 || depth == kMaxDepth) return;
    if (children > kMaxNodes) children = kMaxNodes;
    for (A_long i = 0; i < children && count < kMaxNodes; ++i) {
        AEGP_StreamRefH child = nullptr;
        A_Err e = s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(g_id, ref, i, &child);
        if (e) {
            Emit(out, depth+1, "child-query-error", i, -1, 0, "", "", (long)e);
        } else {
            Visit(s, child, out, depth+1, i, count);
        }
        if (child) s.StreamSuite2()->AEGP_DisposeStream(child);
    }
}

static A_Err DumpActiveLayer() {
    if (!g_basic) return A_Err_NONE;
    AEGP_SuiteHandler s(g_basic);
    AEGP_LayerH layer = nullptr;
    A_Err err = s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
    if (err || !layer) {
        s.UtilitySuite3()->AEGP_ReportInfo(g_id, "ShapeLayerAE: Select a layer first.");
        return err;
    }
    const char* tmp = getenv("TEMP");
    std::string path = std::string(tmp ? tmp : ".") + "\\ShapeLayerAE_stream_tree.tsv";
    FILE* out = fopen(path.c_str(), "wb");
    if (!out) {
        s.UtilitySuite3()->AEGP_ReportInfo(g_id, "ShapeLayerAE: Unable to open output log.");
        return A_Err_NONE;
    }
    fprintf(out, "# ShapeLayerAE read-only AEGP tree probe; host version must be recorded separately\n");
    fprintf(out, "# output_path=%s\n", path.c_str());
    fprintf(out, "depth\tkind\tindex\tgrouping\tchildren\tmatch_name\tdisplay_name\taegp_error\n");
    AEGP_StreamRefH root = nullptr;
    err = s.DynamicStreamSuite2()->AEGP_GetNewStreamRefForLayer(g_id, layer, &root);
    if (!err && root) {
        int nodes = 0;
        Visit(s, root, out, 0, 0, nodes);
        fprintf(out, "# nodes=%d\n", nodes);
    } else {
        fprintf(out, "# get_layer_root_error=%ld\n", (long)err);
    }
    if (root) s.StreamSuite2()->AEGP_DisposeStream(root);
    fclose(out);
    s.UtilitySuite3()->AEGP_ReportInfo(g_id, "ShapeLayerAE: Stream tree written to TEMP\\ShapeLayerAE_stream_tree.tsv");
    return err;
}

static A_Err CommandHook(AEGP_GlobalRefcon, AEGP_CommandRefcon,
                         AEGP_Command command, AEGP_HookPriority,
                         A_Boolean already_handled, A_Boolean* handled) {
    if (command != g_command || already_handled) return A_Err_NONE;
    if (handled) *handled = TRUE;
    return DumpActiveLayer();
}
static A_Err UpdateMenuHook(AEGP_GlobalRefcon, AEGP_UpdateMenuRefcon,
                            AEGP_WindowType) {
    AEGP_SuiteHandler s(g_basic);
    AEGP_LayerH layer = nullptr;
    s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
    if (layer) return s.CommandSuite1()->AEGP_EnableCommand(g_command);
    return s.CommandSuite1()->AEGP_DisableCommand(g_command);
}

extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* pica, A_long, A_long,
                     AEGP_PluginID plugin_id, AEGP_GlobalRefcon*) {
    g_basic = pica;
    g_id = plugin_id;
    AEGP_SuiteHandler s(g_basic);
    A_Err err = s.CommandSuite1()->AEGP_GetUniqueCommand(&g_command);
    if (!err) err = s.CommandSuite1()->AEGP_InsertMenuCommand(
        g_command, "ShapeLayerAE: Dump Stream Tree", AEGP_Menu_ANIMATION,
        AEGP_MENU_INSERT_AT_TOP);
    if (!err) err = s.RegisterSuite5()->AEGP_RegisterCommandHook(
        g_id, AEGP_HP_BeforeAE, AEGP_Command_ALL, CommandHook, nullptr);
    if (!err) err = s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(
        g_id, UpdateMenuHook, nullptr);
    return err;
}
