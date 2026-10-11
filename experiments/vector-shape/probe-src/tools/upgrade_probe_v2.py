"""Upgrade ShapeLayerAE read-only observer with explicit native stream identity and indexed-group capability matrix.
Leaves existing tree TSV semantics intact. Precondition-checks every specialized query.
"""
from pathlib import Path
p=Path(r"D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp")
text=p.read_text(encoding="utf-8")
anchor="// AEGP stream refs must be disposed by the caller. Root is owned by caller."
assert anchor in text
new= r'''// Additional read-only metadata: do not convert AEGP_StreamRefH pointer addresses
// into identity. AE SDK 25.6 StreamSuite6 provides a public unique stream ID.
static void Meta(AEGP_SuiteHandler& s, AEGP_StreamRefH ref,
                 FILE* metadata, FILE* addcaps,
                 int depth, long index, long parent_id,
                 AEGP_StreamGroupingType grouping, const char* match) {
    if (!metadata || !ref) return;
    int32_t unique_id = -1;
    A_long sdk_depth = -1;
    AEGP_DynStreamFlags dyn_flags = 0;
    A_Boolean modified = FALSE;
    AEGP_StreamType value_type = AEGP_StreamType_NO_DATA;
    A_Err e_id = s.StreamSuite6()->AEGP_GetUniqueStreamID(ref, &unique_id);
    A_Err e_depth = s.DynamicStreamSuite2()->AEGP_GetStreamDepth(ref, &sdk_depth);
    A_Err e_flags = s.DynamicStreamSuite2()->AEGP_GetDynamicStreamFlags(ref, &dyn_flags);
    A_Err e_modified = s.DynamicStreamSuite2()->AEGP_GetStreamIsModified(ref, &modified);
    A_Err e_type = A_Err_NONE;
    if (grouping == AEGP_StreamGroupingType_LEAF)
        e_type = s.StreamSuite6()->AEGP_GetStreamType(ref, &value_type);
    fprintf(metadata,
            "%d\t%ld\t%ld\t%ld\t%d\t%ld\t%lu\t%d\t%ld\t%ld\t%ld\t%ld\t%ld\t%s\n",
            depth,index,parent_id,(long)unique_id,(int)grouping,
            (long)sdk_depth,(unsigned long)dyn_flags,(int)modified,
            (long)value_type,(long)e_id,(long)e_depth,(long)e_flags,
            (long)(e_modified?e_modified:e_type),match?match:"");
    // CanAdd is a read-only query, valid ONLY for an INDEXED_GROUP.
    // Probe ONLY documented built-in match names; never call AddStream here.
    if (addcaps && grouping == AEGP_StreamGroupingType_INDEXED_GROUP) {
        static const char* known[] = {
            "ADBE Vector Group", "ADBE Vector Shape - Group",
            "ADBE Vector Shape - Rect", "ADBE Vector Graphic - Fill",
            "ADBE Vector Graphic - Stroke", "ADBE Slider Control"
        };
        for (const char* candidate : known) {
            A_Boolean allowed = FALSE;
            A_Err e = s.DynamicStreamSuite2()->AEGP_CanAddStream(ref, candidate, &allowed);
            fprintf(addcaps,"%ld\t%s\t%s\t%d\t%ld\n",
                    (long)unique_id,match?match:"",candidate,
                    (int)allowed,(long)e);
        }
    }
}
'''
text=text.replace(anchor,new+"\n"+anchor,1)
old="""                  FILE* out, int depth, long index, int& count) {"""
new="""                  FILE* out, FILE* meta, FILE* canadd,
                  int depth, long index, long parent_uid, int& count) {"""
assert old in text;text=text.replace(old,new,1)
old="""    Emit(out, depth, "stream", index, (long)grouping, (long)children,"""
new="""    if (!e1) Meta(s, ref, meta, canadd, depth, index, parent_uid, grouping,
                  e2 ? "(match-query-error)" : match);
    int32_t current_uid = -1;
    if (!e1) (void)s.StreamSuite6()->AEGP_GetUniqueStreamID(ref, &current_uid);
    Emit(out, depth, "stream", index, (long)grouping, (long)children,"""
assert old in text;text=text.replace(old,new,1)
old="""            Visit(s, child, out, depth+1, i, count);"""
new="""            Visit(s, child, out, meta, canadd, depth+1, i, current_uid, count);"""
assert old in text;text=text.replace(old,new,1)
old="""    fprintf(out, "depth\\tkind\\tindex\\tgrouping\\tchildren\\tmatch_name\\tdisplay_name\\taegp_error\\n");
    AEGP_StreamRefH root = nullptr;"""
new="""    fprintf(out, "depth\\tkind\\tindex\\tgrouping\\tchildren\\tmatch_name\\tdisplay_name\\taegp_error\\n");
    const std::string base = std::string(tmp ? tmp : ".");
    FILE* meta = fopen((base + "\\\\ShapeLayerAE_stream_metadata.tsv").c_str(), "wb");
    FILE* canadd = fopen((base + "\\\\ShapeLayerAE_canadd.tsv").c_str(), "wb");
    if (meta) fprintf(meta, "depth\\tindex\\tparent_stream_uid\\tunique_stream_id\\tgrouping\\tsdk_depth\\tdynamic_flags\\tis_modified\\tleaf_stream_type\\tuid_error\\tdepth_error\\tflags_error\\tother_error\\tmatch_name\\n");
    if (canadd) fprintf(canadd, "parent_stream_uid\\tparent_match_name\\tcandidate_match_name\\tcan_add\\tquery_error\\n");
    AEGP_StreamRefH root = nullptr;"""
assert old in text;text=text.replace(old,new,1)
old="""        Visit(s, root, out, 0, 0, nodes);"""
new="""        Visit(s, root, out, meta, canadd, 0, 0, -1, nodes);"""
assert old in text;text=text.replace(old,new,1)
old="""    fclose(out);
    s.UtilitySuite3()->AEGP_ReportInfo"""
new="""    fclose(out);
    if (meta) fclose(meta);
    if (canadd) fclose(canadd);
    s.UtilitySuite3()->AEGP_ReportInfo"""
assert old in text;text=text.replace(old,new,1)
p.write_text(text,encoding="utf-8")
print("PATCHED",p,len(text.splitlines()),"lines")
