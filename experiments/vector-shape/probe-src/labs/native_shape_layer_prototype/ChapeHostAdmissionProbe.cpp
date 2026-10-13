// ChapeLayer: read-only host Indexed Group / MatchName admission matrix.
// Using PUBLIC AEGP_DynamicStreamSuite, no AddStream / BEE / TDB calls.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include "ChapeHierarchyRules.h"
#include <Windows.h>
#include <cstdio>
#include <cstring>
#include <string>
namespace {
const char* candidates[]={
 "ADBE Vector Group",
 "ADBE Vector Shape - Group",
 "ADBE Vector Graphic - Fill",
 "ADBE Vector Filter - Trim",
 "ADBE Vector Shape - ChapeLayerProbe",
 "ADBE Vector Graphic - ChapeLayerProbe",
 "ADBE Vector Filter - ChapeLayerProbe",
 "CNL:Forward",
 "CNL:Reverse",
 "CNL:Path",
 "ADBE Slider Control"
};
void record(AEGP_SuiteHandler& s,AEGP_PluginID id,FILE* out,const char* scope,AEGP_StreamRefH stream){
 if(!stream){fprintf(out,"missing_scope\t%s\n",scope);return;}
 A_char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
 const A_Err m=s.DynamicStreamSuite2()->AEGP_GetMatchName(stream,match);
 AEGP_StreamGroupingType type=AEGP_StreamGroupingType_NONE;
 const A_Err k=s.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(stream,&type);
 A_long children=-1;
 const A_Err n=s.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(stream,&children);
 fprintf(out,"scope\t%s\t%s\t%d\t%d\t%ld\t%d\n",scope,
   m?"(error)":match,(int)m,(int)type,(long)children,(int)n);
 if(k||type!=AEGP_StreamGroupingType_INDEXED_GROUP)return;
 for(auto name:candidates){
   A_Boolean can=FALSE;
   const A_Err e=s.DynamicStreamSuite2()->AEGP_CanAddStream(stream,name,&can);
   fprintf(out,"can_add\t%s\t%s\t%d\t%d\n",scope,name,int(can!=FALSE),int(e));
 }
 // The child order is observable through public Indexed Group APIs.
 // This is NOT proof of the BEE rendering order or reducer semantics.
 for(A_long i=0;i<children&&i<120;++i){
   AEGP_StreamRefH item=nullptr;
   const A_Err err=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(
       id,stream,i,&item);
   A_char label[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
   AEGP_StreamGroupingType childType=AEGP_StreamGroupingType_NONE;
   const A_Err labelErr=item?s.DynamicStreamSuite2()->AEGP_GetMatchName(item,label):A_Err(-1);
   const A_Err typeErr=item?s.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(item,&childType):A_Err(-1);
   fprintf(out,"indexed_child\t%s\t%ld\t%s\t%d\t%d\t%d\t%d\n",
       scope,(long)i,item?label:"(null)",int(childType),int(err),int(labelErr),int(typeErr));
   if(item)s.StreamSuite2()->AEGP_DisposeStream(item);
 }
}
AEGP_StreamRefH byName(AEGP_SuiteHandler& s,AEGP_PluginID id,
                        AEGP_StreamRefH parent,const char* name){
 if(!parent)return nullptr;
 AEGP_StreamRefH child=nullptr;
 if(s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByMatchname(id,parent,name,&child)){
  if(child)s.StreamSuite2()->AEGP_DisposeStream(child);
  return nullptr;
 }
 return child;
}
}
A_Err CNL_RunChapeHostProbe(SPBasicSuite* basic,AEGP_PluginID id){
 if(!basic)return A_Err_NONE;
 AEGP_SuiteHandler s(basic);
 AEGP_LayerH layer=nullptr;
 const A_Err active=s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
 if(active||!layer){
  s.UtilitySuite3()->AEGP_ReportInfo(id,"ChapeLayer: Select a native Shape Layer in the Timeline to inspect its Contents. No changes made.");
  return A_Err_NONE;
 }
 char dir[MAX_PATH+2]{};
 const DWORD length=GetTempPathA(MAX_PATH,dir);
 if(!length||length>=MAX_PATH)return A_Err_NONE;
 const std::string filename=std::string(dir)+"ChapeLayer_HostAdmission_ReadOnly.tsv";
 FILE* out=fopen(filename.c_str(),"wb");
 if(!out)return A_Err_NONE;
 fprintf(out,"format\tChapeLayer Host Native Indexed Contents Admission v1\n");
 fprintf(out,"host_changes\t0\nprivate_factory_calls\t0\n");
 AEGP_ObjectType kind=AEGP_ObjectType_NONE;
 const A_Err eobj=s.LayerSuite5()->AEGP_GetLayerObjectType(layer,&kind);
 fprintf(out,"active_layer_kind\t%d\t%d\n",(int)kind,(int)eobj);
 AEGP_StreamRefH root=nullptr, rootVectors=nullptr,contents=nullptr,nested=nullptr;
 const A_Err er=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefForLayer(id,layer,&root);
 fprintf(out,"root_stream_err\t%d\n",(int)er);
 if(!er&&root){
  record(s,id,out,"Layer",root);
  rootVectors=byName(s,id,root,"ADBE Root Vectors Group");
  record(s,id,out,"Root Vectors",rootVectors);
  contents=byName(s,id,rootVectors,"ADBE Vectors Group");
  record(s,id,out,"Shape Contents",contents);
  if(contents){
   A_long count=0;
   if(!s.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(contents,&count)){
    for(A_long i=0;i<count&&i<100&&!nested;++i){
     AEGP_StreamRefH candidate=nullptr;
     if(!s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(id,contents,i,&candidate)&&candidate){
       A_char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
       if(!s.DynamicStreamSuite2()->AEGP_GetMatchName(candidate,match)&&
          !std::strcmp(match,"ADBE Vector Group"))
        nested=byName(s,id,candidate,"ADBE Vectors Group");
     }
     if(candidate)s.StreamSuite2()->AEGP_DisposeStream(candidate);
    }
   }
  }
  record(s,id,out,"Nested Group Contents",nested);
 }
 if(nested)s.StreamSuite2()->AEGP_DisposeStream(nested);
 if(contents)s.StreamSuite2()->AEGP_DisposeStream(contents);
 if(rootVectors)s.StreamSuite2()->AEGP_DisposeStream(rootVectors);
 if(root)s.StreamSuite2()->AEGP_DisposeStream(root);
 // Control experiment: unlike Adobe's fixed native stream classes, the
 // CNL-owned schema can define new type identities and evaluation order.
 chape::Hierarchy own;
 const auto r1=own.registerType({"CNL:Forward",{"CNL:Path","CNL:Reverse"},true,chape::Order::Forward});
 const auto r2=own.registerType({"CNL:Reverse",{"CNL:Path"},true,chape::Order::Reverse});
 const auto r3=own.registerType({"CNL:Path",{},false,chape::Order::Forward});
 const auto r4=own.setChildren("CNL:Document",{"CNL:Forward"});
 uint64_t g=0,a=0,b=0,rev=0,c=0,d=0;
 bool ownPass=r1==chape::Result::Ok&&r2==chape::Result::Ok&&r3==chape::Result::Ok&&r4==chape::Result::Ok;
 if(ownPass)ownPass=own.add(1,"CNL:Forward","Stack",g)==chape::Result::Ok;
 if(ownPass)ownPass=own.add(g,"CNL:Path","A",a)==chape::Result::Ok;
 if(ownPass)ownPass=own.add(g,"CNL:Path","B",b)==chape::Result::Ok;
 if(ownPass)ownPass=own.add(g,"CNL:Reverse","Reverse",rev)==chape::Result::Ok;
 if(ownPass)ownPass=own.add(rev,"CNL:Path","C",c)==chape::Result::Ok;
 if(ownPass)ownPass=own.add(rev,"CNL:Path","D",d)==chape::Result::Ok;
 fprintf(out,"cnl_schema_control_pass\t%d\n",ownPass?1:0);
 fprintf(out,"cnl_can_add_custom_path_to_reverse\t%d\n",own.canAdd(rev,"CNL:Path")?1:0);
 fprintf(out,"cnl_can_add_custom_group_to_reverse\t%d\n",own.canAdd(rev,"CNL:Forward")?1:0);
 if(ownPass)for(const auto& event:own.evaluationTrace())
   fprintf(out,"cnl_evaluation_trace\t%s\n",event.c_str());
 fprintf(out,"final\tread_only_complete\n");
 fclose(out);
 s.UtilitySuite3()->AEGP_ReportInfo(id,"ChapeLayer: Read-only host Contents admission in TEMP\\ChapeLayer_HostAdmission_ReadOnly.tsv. Nothing added to the project.");
 return A_Err_NONE;
}
