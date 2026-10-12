// Read-only AEGP: confirm genuine AE-side parameter value types and
// stable native IDs of a user-installed CNL Owned Vector Document effect.
// NEVER reads opaque arb value memory; never writes project or registry.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include <Windows.h>
#include <cstdio>
#include <cstring>
#include <string>
namespace {
SPBasicSuite* basic=nullptr;
AEGP_PluginID id=0;
AEGP_Command cmd=0;
constexpr char kMatch[]="CNL Owned Vector Document";
constexpr char kTsv[]="CNL_OwnedEffect_StreamIdentity_v2.tsv";
A_Err inspect(){
 AEGP_SuiteHandler s(basic);
 AEGP_LayerH layer=nullptr;
 const A_Err active=s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
 if(active||!layer){
  s.UtilitySuite3()->AEGP_ReportInfo(id,"Select the Timeline layer with CNL Owned Vector Document applied. Read only.");
  return A_Err_NONE;
 }
 char temp[MAX_PATH+1]{};
 const DWORD n=GetTempPathA(MAX_PATH,temp);
 if(!n||n>=MAX_PATH)return A_Err_NONE;
 const std::string path=std::string(temp)+kTsv;
 FILE* out=fopen(path.c_str(),"wb");
 if(!out)return A_Err_NONE;
 fprintf(out,"# EXP-SHAPE-051 PUBLIC SDK READ ONLY; NO Arbitrary payload read\n");
 fprintf(out,"match_target\t%s\n",kMatch);
 A_long count=0;
 const auto ecount=s.EffectSuite5()->AEGP_GetLayerNumEffects(layer,&count);
 fprintf(out,"effect_count_error\t%d\neffect_count\t%ld\n",int(ecount),long(count));
 int matches=0;
 if(!ecount&&count>=0&&count<=128){
  for(A_long i=0;i<count;++i){
   AEGP_EffectRefH effect=nullptr;
   auto err=s.EffectSuite5()->AEGP_GetLayerEffectByIndex(id,layer,i,&effect);
   fprintf(out,"effect_ref\t%ld\t%d\n",long(i),int(err));
   if(err||!effect)continue;
   AEGP_InstalledEffectKey key=AEGP_InstalledEffectKey_NONE;
   err=s.EffectSuite5()->AEGP_GetInstalledKeyFromLayerEffect(effect,&key);
   A_char match[AEGP_MAX_EFFECT_MATCH_NAME_SIZE]{};
   const A_Err nameError=err?err:s.EffectSuite5()->AEGP_GetEffectMatchName(key,match);
   fprintf(out,"effect_match\t%ld\t%s\t%d\n",long(i),
     nameError?"(error)":match,int(nameError));
   if(!nameError&&!std::strcmp(match,kMatch)){
    ++matches;
    A_long parameters=0;
    const A_Err numErr=s.StreamSuite6()->AEGP_GetEffectNumParamStreams(effect,&parameters);
    fprintf(out,"target_effect\t%ld\t%ld\t%d\n",long(i),long(parameters),int(numErr));
    if(!numErr&&parameters>=1&&parameters<=64){
     // AE2026 independently confirmed index 0 causes internal param_index
     // validation failure for BOTH metadata and StreamRef acquisition.
     // This is the input layer, not one of the effect-owned data params.
     // Do not call either host API for param_index=0, even though the
     // SDK header describes the broad 0..N-1 range as including input.
     fprintf(out,"param_skipped\t0\tinput_layer_host_rejects_index_zero\n");
     for(A_long index=1;index<parameters;++index){
      PF_ParamType pfType=PF_Param_RESERVED;
      PF_ParamDefUnion metadata{};
      const auto pErr=s.EffectSuite5()->AEGP_GetEffectParamUnionByIndex(
        id,effect,index,&pfType,&metadata);
      AEGP_StreamRefH stream=nullptr;
      const auto rErr=s.StreamSuite6()->AEGP_GetNewEffectStreamByIndex(
        id,effect,index,&stream);
      AEGP_StreamType valueType=AEGP_StreamType_NO_DATA;
      int32_t unique=-1;
      A_Boolean variable=FALSE;
      A_Err typeErr=0,idErr=0,varErr=0;
      A_char paramMatch[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
      A_Err matchErr=0;
      if(!rErr&&stream){
       typeErr=s.StreamSuite6()->AEGP_GetStreamType(stream,&valueType);
       idErr=s.StreamSuite6()->AEGP_GetUniqueStreamID(stream,&unique);
       varErr=s.StreamSuite6()->AEGP_CanVaryOverTime(stream,&variable);
       matchErr=s.DynamicStreamSuite2()->AEGP_GetMatchName(stream,paramMatch);
      }
      fprintf(out,"param\t%ld\t%d\t%d\t%d\t%d\t%d\t%ld\t%d\t%d\t%d\t%s\t%d\n",
       long(index),int(pfType),int(pErr),int(valueType),int(typeErr),
       int(unique),long(variable),int(varErr),int(rErr),int(idErr),
       matchErr?"(error)":paramMatch,int(matchErr));
      if(stream)s.StreamSuite6()->AEGP_DisposeStream(stream);
     }
    }
   }
   s.EffectSuite5()->AEGP_DisposeEffect(effect);
  }
 }
 fprintf(out,"matched_CNL_effects\t%d\nprivate_registry_invoked\t0\nmutations\t0\nopaque_arb_payload_read\t0\n",matches);
 fclose(out);
 s.UtilitySuite3()->AEGP_ReportInfo(id,
   "CNL Native Effect Identity v2: READ ONLY report in TEMP\\CNL_OwnedEffect_StreamIdentity_v2.tsv");
 return A_Err_NONE;
}
A_Err onCommand(AEGP_GlobalRefcon,AEGP_CommandRefcon,
 AEGP_Command which,AEGP_HookPriority,A_Boolean before,A_Boolean* handled){
 if(before||which!=cmd)return A_Err_NONE;
 if(handled)*handled=TRUE;
 return inspect();
}
A_Err onMenu(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
 AEGP_SuiteHandler s(basic);
 return s.CommandSuite1()->AEGP_EnableCommand(cmd);
}
}
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* b,A_long,A_long,AEGP_PluginID plug,AEGP_GlobalRefcon*){
 basic=b;id=plug;AEGP_SuiteHandler s(b);
 A_Err err=s.CommandSuite1()->AEGP_GetUniqueCommand(&cmd);
 if(!err)err=s.CommandSuite1()->AEGP_InsertMenuCommand(cmd,
  "CNL Effect: Inspect Native Stream Identity (Read Only)",
  AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 if(!err)err=s.RegisterSuite5()->AEGP_RegisterCommandHook(plug,AEGP_HP_BeforeAE,
  AEGP_Command_ALL,onCommand,nullptr);
 if(!err)err=s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(plug,onMenu,nullptr);
 return err;
}
