// Native Effect SDK consumer of a PICA vector geometry suite, NOT native BEE VectorArt.
// The effect passes pixels through unchanged while obtaining double Bezier curves.
#include "AEConfig.h"
#include "entry.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_Macros.h"
#include "SPBasic.h"
#include "VectorBridgeSuite.h"
#include <cstdio>
namespace {
struct VectorSnapshot {bool ok=false;uint32_t n=0;double x=0;};
VectorSnapshot Fetch(SPBasicSuite* basic,int64_t t,int64_t scale) {
 VectorSnapshot result;
 if(!basic)return result;
 const void* generic_suite=nullptr;
 SPErr e=basic->AcquireSuite(kCNLVectorBridgeSuite1,
                            kCNLVectorBridgeSuiteVersion1,&generic_suite);
 const auto* suite=static_cast<const CNL_VectorBridgeSuite1*>(generic_suite);
 if(e||!suite)return result;
 CNL_VectorPathInfoV1 info={sizeof(CNL_VectorPathInfoV1),0,0,0};
 CNL_VectorCubicV1 cubics[4]{};
 uint32_t actual=0;
 if(suite->DescribePath(0,&info)==A_Err_NONE && info.cubic_count==4 &&
    suite->CopyCubicPath(0,t,scale,cubics,4,&actual)==A_Err_NONE && actual==4) {
    result.ok=true;result.n=actual;result.x=cubics[0].x0;
 }
 basic->ReleaseSuite(kCNLVectorBridgeSuite1,kCNLVectorBridgeSuiteVersion1);
 return result;
}
}
extern "C" DllExport PF_Err PluginDataEntryFunction2(
 PF_PluginDataPtr inPtr,PF_PluginDataCB2 cb,SPBasicSuite*,const char*,const char*) {
 PF_Err result=PF_Err_INVALID_CALLBACK;
 result=PF_REGISTER_EFFECT_EXT2(inPtr,cb,
 "Vector Bridge Consumer (Research)","CNL Vector Bridge Consumer",
 "CompNodeAE Research",AE_RESERVED_INFO,"EffectMain",
 "https://github.com/ken-eizo/after-effects-internals-guide");
 return result;
}
extern "C" DllExport PF_Err EffectMain(
 PF_Cmd cmd,PF_InData* in_data,PF_OutData* out_data,PF_ParamDef* params[],
 PF_LayerDef* output) {
 if(!in_data||!out_data)return PF_Err_BAD_CALLBACK_PARAM;
 switch(cmd) {
 case PF_Cmd_ABOUT: {
   VectorSnapshot r=Fetch(in_data->pica_basicP,0,1);
   PF_SPRINTF(out_data->return_msg,
     "CompNodeAE Vector Geometry Bridge\rPICA suite: %s\r"
     "Native Bezier segments: %lu; first X: %.2f\r"
     "This is NOT a host Shape Layer or native AE vector renderer.",
     r.ok?"connected":"not available",(unsigned long)r.n,r.x);
   break;
 }
 case PF_Cmd_GLOBAL_SETUP:
   out_data->my_version=PF_VERSION(1,0,0,PF_Stage_DEVELOP,1);
   // The passthrough output depends on input pixels: PIX_INDEPENDENT would be wrong.
   out_data->out_flags=PF_OutFlag_NONE;
   // The effect has no per-frame mutable globals or sequence data. Each render
   // acquires/releases an immutable PICA geometry suite and uses caller-local POD.
   out_data->out_flags2=PF_OutFlag2_SUPPORTS_THREADED_RENDERING;
   break;
 case PF_Cmd_PARAMS_SETUP:
   out_data->num_params=1;
   break;
 case PF_Cmd_RENDER: {
   const auto check=Fetch(in_data->pica_basicP,in_data->current_time,in_data->time_scale);
   (void)check;
   if(!params||!params[0]||!output)return PF_Err_BAD_CALLBACK_PARAM;
   return PF_COPY(&params[0]->u.ld,output,nullptr,nullptr);
 }
 default:break;
 }
 return PF_Err_NONE;
}
