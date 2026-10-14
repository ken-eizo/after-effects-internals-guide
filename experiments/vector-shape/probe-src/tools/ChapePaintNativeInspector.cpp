// ChapeLayer: read-only public-AEGP inspection of Adobe's *Paint* brush tool effect.
// NOT Paint Bucket, Brush Strokes, or a custom native stream registrar.
// Adapted to the SDK25.6 AEGP/Streamie traversal contract without mutating streams.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include <Windows.h>
#include <cstdio>
#include <string>
#include <algorithm>

namespace {
using namespace std;
void safeField(char* s){
 if(!s)return;
 for(;*s;++s)if(*s=='\t'||*s=='\r'||*s=='\n')*s=' ';
}
class Inspector {
public:
 AEGP_SuiteHandler& suites;
 AEGP_PluginID plugin;
 FILE* output;
 int budget=500;
 int nodes=0;
 int errors=0;
 explicit Inspector(AEGP_SuiteHandler& s,AEGP_PluginID i,FILE* out):suites(s),plugin(i),output(out){}
 void dispose(AEGP_StreamRefH h) {
  if(h) {
   const A_Err e=suites.StreamSuite2()->AEGP_DisposeStream(h);
   if(e)++errors;
  }
 }
 void walk(AEGP_StreamRefH parent,int depth,const string& parentPath) {
  if(!parent||depth>8||budget<=0)return;
  char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
  char name[AEGP_MAX_STREAM_NAME_SIZE]{};
  const A_Err matchErr=suites.DynamicStreamSuite2()->AEGP_GetMatchName(parent,match);
  const A_Err nameErr=suites.StreamSuite2()->AEGP_GetStreamName(parent,TRUE,name);
  AEGP_StreamGroupingType kind=AEGP_StreamGroupingType_NONE;
  const A_Err groupErr=suites.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(parent,&kind);
  const bool container=!groupErr && (kind==AEGP_StreamGroupingType_INDEXED_GROUP||kind==AEGP_StreamGroupingType_NAMED_GROUP);
  A_long count=-1;
  const A_Err countErr=container?suites.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(parent,&count):0;
  if(matchErr || groupErr || (container&&countErr))++errors;
  safeField(match);safeField(name);
  string path=parentPath+"/"+(matchErr?"(no match)":match);
  fprintf(output,"node\t%d\t%s\t%s\t%s\t%d\t%ld\t%d\t%d\t%d\t%d\n",
          depth,path.c_str(),matchErr?"(error)":match,nameErr?"(error)":name,
          (int)kind,(long)count,(int)matchErr,(int)nameErr,(int)groupErr,(int)countErr);
  ++nodes;
  --budget;
  // This is purely a parent-admission query, never a creator invocation.
  // Even TRUE does not prove an unknown TDB Stream class can be instantiated.
  if(container && kind==AEGP_StreamGroupingType_INDEXED_GROUP &&
     string(match)=="ADBE Paint Group"){
   const char* candidates[]={
     "ADBE Paint Atom",
     "ADBE Paint Nibbler Atom",
     "ADBE Paint Shape",
     "ADBE Vector Group",
     "CNL:PaintAtom",
     "ADBE Paint Atom - CNLProbe"
   };
   for(const char* candidate:candidates){
    A_Boolean can=FALSE;
    const A_Err ce=suites.DynamicStreamSuite2()->AEGP_CanAddStream(parent,candidate,&can);
    fprintf(output,"can_add\t%s\t%s\t%d\t%d\n",path.c_str(),candidate,(int)(can!=FALSE),(int)ce);
    if(ce)++errors;
   }
  }
  if(!container||countErr||count<0)return;
  const A_long limit=min<A_long>(count,120);
  for(A_long i=0;i<limit&&budget>0;++i){
   AEGP_StreamRefH child=nullptr;
   const A_Err e=suites.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(plugin,parent,i,&child);
   if(e||!child){
    fprintf(output,"child_error\t%s\t%ld\t%d\n",path.c_str(),(long)i,(int)e);
    ++errors;
   }else{
    walk(child,depth+1,path+"["+to_string(i)+"]");
   }
   dispose(child);
  }
  if(count>limit)fprintf(output,"children_truncated\t%s\t%ld\n",path.c_str(),(long)(count-limit));
 }
};
}

A_Err CNL_RunPaintNativeInspector(SPBasicSuite* basic,AEGP_PluginID plugin){
 if(!basic)return A_Err_NONE;
 AEGP_SuiteHandler suites(basic);
 char tmp[MAX_PATH+2]{};
 const DWORD len=GetTempPathA(MAX_PATH,tmp);
 if(!len||len>=MAX_PATH)return A_Err_NONE;
 const string file=string(tmp)+"ChapeLayer_PaintNativeHierarchy.tsv";
 FILE* out=fopen(file.c_str(),"wb");
 if(!out){
  suites.UtilitySuite3()->AEGP_ReportInfo(plugin,"ChapeLayer Paint: Could not open TEMP TSV file.");
  return A_Err_NONE;
 }
 fprintf(out,"format\tChapeLayer native Adobe Paint effect timeline audit v1\n");
 fprintf(out,"host_project_mutated\t0\nprivate_host_calls\t0\n");
 fprintf(out,"source_sdk\tAEGP Streamie (Adobe AE SDK 25.6)\n");
 AEGP_LayerH layer=nullptr;
 AEGP_StreamRefH root=nullptr,effects=nullptr,paint=nullptr;
 Inspector inspector(suites,plugin,out);
 const A_Err active=suites.LayerSuite5()->AEGP_GetActiveLayer(&layer);
 fprintf(out,"active_layer_err\t%d\n",(int)active);
 if(!active&&layer){
  AEGP_ObjectType objectType=AEGP_ObjectType_NONE;
  const A_Err objectErr=suites.LayerSuite5()->AEGP_GetLayerObjectType(layer,&objectType);
  fprintf(out,"layer_object_type\t%d\t%d\n",(int)objectType,(int)objectErr);
  if(!objectErr && objectType!=AEGP_ObjectType_CAMERA && objectType!=AEGP_ObjectType_LIGHT){
   const A_Err rootErr=suites.DynamicStreamSuite2()->AEGP_GetNewStreamRefForLayer(plugin,layer,&root);
   fprintf(out,"layer_root_err\t%d\n",(int)rootErr);
   if(!rootErr&&root){
    AEGP_StreamGroupingType kind=AEGP_StreamGroupingType_NONE;
    const A_Err kindErr=suites.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(root,&kind);
    fprintf(out,"root_grouping\t%d\t%d\n",(int)kind,(int)kindErr);
    if(!kindErr&&kind==AEGP_StreamGroupingType_NAMED_GROUP){
     const A_Err paradeErr=suites.DynamicStreamSuite2()->AEGP_GetNewStreamRefByMatchname(
       plugin,root,AEGP_StreamGroupName_EFFECT_PARADE,&effects);
     fprintf(out,"effect_parade_err\t%d\n",(int)paradeErr);
     if(!paradeErr&&effects){
      AEGP_StreamGroupingType ekind=AEGP_StreamGroupingType_NONE;
      A_long count=0;
      const A_Err ek=suites.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(effects,&ekind);
      const A_Err ec=suites.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(effects,&count);
      fprintf(out,"effect_parade_grouping\t%d\t%d\t%ld\t%d\n",(int)ekind,(int)ek,(long)count,(int)ec);
      if(!ek&&!ec&&ekind==AEGP_StreamGroupingType_INDEXED_GROUP){
       for(A_long index=0;index<count&&index<128;++index){
        AEGP_StreamRefH current=nullptr;
        const A_Err ce=suites.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(
          plugin,effects,index,&current);
        if(ce||!current){++inspector.errors;inspector.dispose(current);continue;}
        char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
        const A_Err me=suites.DynamicStreamSuite2()->AEGP_GetMatchName(current,match);
        safeField(match);
        fprintf(out,"effect_instance\t%ld\t%s\t%d\n",(long)index,match,(int)me);
        if(!me && string(match)=="ADBE Paint"){
         paint=current;
         fprintf(out,"paint_found\t1\t%ld\n",(long)index);
         break;
        }
        inspector.dispose(current);
       }
      }
     }
    }
   }
  }
 }
 if(paint)inspector.walk(paint,0,"ADBE Effect Parade");
 else fprintf(out,"paint_found\t0\n");
 fprintf(out,"inspected_nodes\t%d\nerrors\t%d\nfinal\tread_only_completed\n",inspector.nodes,inspector.errors);
 inspector.dispose(paint);
 inspector.dispose(effects);
 inspector.dispose(root);
 fclose(out);
 suites.UtilitySuite3()->AEGP_ReportInfo(plugin,
  "ChapeLayer: Paint native property hierarchy inspection complete. See TEMP\\ChapeLayer_PaintNativeHierarchy.tsv. No project changes.");
 return A_Err_NONE;
}
