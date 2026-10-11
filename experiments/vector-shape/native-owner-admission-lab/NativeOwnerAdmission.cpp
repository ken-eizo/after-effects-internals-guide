// EXP-SHAPE-039 — Public AEGP native owner/Contents admission probe.
// READ ONLY. Never mutates project, registers private factories or adds streams.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include <Windows.h>
#include <cstdio>
#include <string>
namespace {
SPBasicSuite* basic=nullptr;
AEGP_PluginID plugin=0;
AEGP_Command command=0;
int visited=0;
constexpr int kMaxNodes=240,kMaxDepth=4;
constexpr const char* candidates[]={
 "ADBE Vector Shape - CNL Probe","ADBE Vector Shape - Group",
 "ADBE Vector Graphic - Fill","ADBE Vector Filter - Trim",
 "ADBE Slider Control","CNL Native Independent Group"
};
void walk(AEGP_SuiteHandler& s,FILE* out,AEGP_StreamRefH stream,
          int depth,const char* parent) {
 if(depth>kMaxDepth||visited>=kMaxNodes)return;
 const int node=++visited;
 A_char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
 const A_Err ne=s.DynamicStreamSuite2()->AEGP_GetMatchName(stream,match);
 AEGP_StreamGroupingType kind=AEGP_StreamGroupingType_NONE;
 const A_Err ge=s.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(stream,&kind);
 fprintf(out,"stream\t%d\t%d\t%s\t%s\t%d\t%d\n",
   node,depth,parent,ne?"(error)":match,(int)kind,(int)ge);
 if(ge||kind==AEGP_StreamGroupingType_LEAF)return;
 A_long n=0;
 const A_Err ce=s.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(stream,&n);
 fprintf(out,"group\t%d\t%ld\t%d\n",node,(long)n,(int)ce);
 for(const char* name:candidates) {
  A_Boolean can=FALSE;
  const A_Err e=s.DynamicStreamSuite2()->AEGP_CanAddStream(stream,name,&can);
  fprintf(out,"admission\t%d\t%s\t%d\t%d\n",node,name,int(can!=FALSE),int(e));
 }
 if(ce||depth>=kMaxDepth||n<0||n>4000)return;
 for(A_long i=0;i<n&&i<100&&visited<kMaxNodes;++i){
  AEGP_StreamRefH child=nullptr;
  const A_Err e=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(plugin,stream,i,&child);
  if(e||!child){
   fprintf(out,"child_error\t%d\t%ld\t%d\n",node,(long)i,int(e));
  }else if(depth<kMaxDepth){
   walk(s,out,child,depth+1,ne?"?":match);
  }
  if(child)s.StreamSuite2()->AEGP_DisposeStream(child);
 }
}
A_Err run(){
 AEGP_SuiteHandler s(basic);
 AEGP_LayerH layer=nullptr;
 const A_Err active=s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
 if(active||!layer){
  s.UtilitySuite3()->AEGP_ReportInfo(plugin,"Select a Timeline layer first. No changes made.");
  return A_Err_NONE;
 }
 AEGP_ObjectType ty=AEGP_ObjectType_NONE;
 const A_Err t=s.LayerSuite5()->AEGP_GetLayerObjectType(layer,&ty);
 if(t)return t;
 char dir[MAX_PATH+1]{};
 DWORD len=GetTempPathA(MAX_PATH,dir);
 if(!len||len>=MAX_PATH)return A_Err_NONE;
 const std::string path=std::string(dir)+"CNL_NativeOwner_Admission.tsv";
 FILE* out=fopen(path.c_str(),"wb");
 if(!out)return A_Err_NONE;
 fprintf(out,"# EXP-SHAPE-039 READ ONLY; never registers or adds streams\n");
 fprintf(out,"layer_object_type\t%d\n",int(ty));
 AEGP_StreamRefH root=nullptr;
 const A_Err e=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefForLayer(plugin,layer,&root);
 fprintf(out,"root_stream_error\t%d\n",int(e));
 visited=0;
 if(!e&&root)walk(s,out,root,0,"(layer)");
 if(root)s.StreamSuite2()->AEGP_DisposeStream(root);
 fprintf(out,"visited_nodes\t%d\nprivate_registry_invoked\t0\nstream_created\t0\n",visited);
 fclose(out);
 s.UtilitySuite3()->AEGP_ReportInfo(plugin,
   "CNL Native Owner: Read-only trace in TEMP\\CNL_NativeOwner_Admission.tsv");
 return A_Err_NONE;
}
A_Err onCommand(AEGP_GlobalRefcon,AEGP_CommandRefcon,AEGP_Command action,
 AEGP_HookPriority,A_Boolean before,A_Boolean* handled){
 if(before||action!=command)return A_Err_NONE;
 if(handled)*handled=TRUE;
 return run();
}
A_Err onUpdate(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
 AEGP_SuiteHandler s(basic);
 return s.CommandSuite1()->AEGP_EnableCommand(command);
}
}
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* b,A_long,A_long,AEGP_PluginID id,AEGP_GlobalRefcon*){
 basic=b;plugin=id;
 AEGP_SuiteHandler s(b);
 A_Err e=s.CommandSuite1()->AEGP_GetUniqueCommand(&command);
 if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(command,
   "CNL Native Owner: Inspect Admission (Read Only)",
   AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 if(!e)e=s.RegisterSuite5()->AEGP_RegisterCommandHook(id,AEGP_HP_BeforeAE,
                AEGP_Command_ALL,onCommand,nullptr);
 if(!e)e=s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(id,onUpdate,nullptr);
 return e;
}
