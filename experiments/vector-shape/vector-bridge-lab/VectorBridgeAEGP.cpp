// CompNodeAE research AEGP: exposes procedural Bezier data via public PICA Suite.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "SPSuites.h"
#include "SPRuntme.h"
#include "VectorBridgeSuite.h"
#include <cmath>
namespace {
constexpr A_Err Bad=static_cast<A_Err>(0x4101);
A_Err Describe(uint32_t kind,CNL_VectorPathInfoV1* p){
 if(!p||kind>1||p->byte_size!=sizeof(*p))return Bad;
 p->cubic_count=4;p->closed=1;p->geometry_revision=1;return A_Err_NONE;
}
A_Err Copy(uint32_t kind,int64_t t,int64_t scale,CNL_VectorCubicV1* out,
           uint32_t cap,uint32_t* written) {
 if(!written)return Bad;
 *written=4;
 if(kind>1||scale<=0||!out||cap<4)return Bad;
 constexpr double k=0.5522847498307936;
 const double r=100.0+25.0*std::sin((double)t/(double)scale*1.3);
 const double rx=r,ry=r*(kind==0?1.0:0.45);
 const double xx[5]={rx,0,-rx,0,rx}, yy[5]={0,ry,0,-ry,0};
 const double dx[4]={0,-rx,0,rx},dy[4]={ry,0,-ry,0};
 for(unsigned i=0;i<4;++i){
  auto& c=out[i];c.x0=xx[i];c.y0=yy[i];c.x3=xx[i+1];c.y3=yy[i+1];
  c.x1=xx[i]+dx[i]*k;c.y1=yy[i]+dy[i]*k;
  c.x2=xx[i+1]-dx[(i+1)%4]*k;c.y2=yy[i+1]-dy[(i+1)%4]*k;
 }return A_Err_NONE;
}
CNL_VectorBridgeSuite1 Suite={Describe,Copy};
SPSuiteRef SuiteRef=nullptr;
}
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* basic,A_long,A_long,AEGP_PluginID,AEGP_GlobalRefcon*){
 if(!basic)return Bad;
 const void* generic_suite=nullptr;
 SPErr e=basic->AcquireSuite(kSPSuitesSuite,kSPSuitesSuiteVersion,&generic_suite);
 auto* s=static_cast<const SPSuitesSuite*>(generic_suite);
 if(e||!s)return static_cast<A_Err>(e?e:Bad);
 e=s->AddSuite(kSPRuntimeSuiteList,nullptr,kCNLVectorBridgeSuite1,
               kCNLVectorBridgeSuiteVersion1,1,&Suite,&SuiteRef);
 const SPErr release=basic->ReleaseSuite(kSPSuitesSuite,kSPSuitesSuiteVersion);
 return static_cast<A_Err>(e?e:release);
}
