// Minimal self-contained PICA stand-in to smoke-test two compiled Adobe .aex DLLs.
// This is NOT the After Effects host: no rendering, Timeline, streams or native tools.
#include <windows.h>
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <cmath>
#include <cstdint>
#include <string>
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AE_Effect.h"
#include "SPBasic.h"
#include "SPSuites.h"
#include "VectorBridgeSuite.h"

namespace {
SPSuitesSuite g_suites{};
SPBasicSuite g_basic{};
const CNL_VectorBridgeSuite1* g_provider=nullptr;
int g_suite_add_calls=0,g_suite_acquires=0;
SPErr Add(SPSuiteListRef,SPPluginRef,const char* name,int32 version,int32,
          const void* procedures,SPSuiteRef* handle) {
 if(!name||std::strcmp(name,kCNLVectorBridgeSuite1)!=0||
    version!=kCNLVectorBridgeSuiteVersion1||!procedures||!handle)return 111;
 g_provider=static_cast<const CNL_VectorBridgeSuite1*>(procedures);
 ++g_suite_add_calls;
 *handle=reinterpret_cast<SPSuiteRef>(0x1234);
 return 0;
}
SPErr Acquire(const char* name,int32 version,const void** out) {
 if(!out||!name)return 112;
 *out=nullptr;
 if(std::strcmp(name,kSPSuitesSuite)==0 && version==kSPSuitesSuiteVersion){
  *out=&g_suites;return 0;
 }
 if(std::strcmp(name,kCNLVectorBridgeSuite1)==0 &&
    version==kCNLVectorBridgeSuiteVersion1 && g_provider){
  *out=g_provider;++g_suite_acquires;return 0;
 }
 return 113;
}
SPErr Release(const char*,int32){return 0;}
int MockSprintf(char* dst,const char* format, ...){
 if(!dst||!format)return -1;
 va_list args;va_start(args,format);
 const int n=std::vsnprintf(dst,255,format,args);
 va_end(args);
 return n;
}
void Fail(const char* why){std::fprintf(stderr,"FAIL: %s\n",why);std::exit(1);}
} // namespace
int main(int argc,char** argv){
 if(argc!=3)Fail("usage: mock provider.aex consumer.aex");
 std::fprintf(stderr,"MOCK stage=before_initialization\n");
 g_suites.AddSuite=Add;
 g_basic.AcquireSuite=Acquire;g_basic.ReleaseSuite=Release;
 std::fprintf(stderr,"MOCK stage=before_load_provider\n");
 const HMODULE provider=LoadLibraryA(argv[1]);
 if(!provider)Fail("provider AEX LoadLibrary failed");
 std::fprintf(stderr,"MOCK stage=before_load_consumer\n");
 const HMODULE consumer=LoadLibraryA(argv[2]);
 if(!consumer)Fail("consumer AEX LoadLibrary failed");
 using Init=A_Err (*)(SPBasicSuite*,A_long,A_long,AEGP_PluginID,AEGP_GlobalRefcon*);
 Init init=reinterpret_cast<Init>(GetProcAddress(provider,"EntryPointFunc"));
 if(!init)Fail("provider EntryPointFunc not exported");
 std::fprintf(stderr,"MOCK stage=before_register_suite\n");
 if(init(&g_basic,26,5,0,nullptr)!=A_Err_NONE)Fail("provider registration failed");
 if(g_suite_add_calls!=1 || !g_provider)Fail("provider did not register PICA Suite");
 std::fprintf(stderr,"MOCK stage=after_register_suite\n");
 CNL_VectorPathInfoV1 info{sizeof(info),0,0,0};
 if(g_provider->DescribePath(0,&info)!=0||info.cubic_count!=4||info.closed!=1)
    Fail("path schema mismatch");
 CNL_VectorCubicV1 cubics[4]{};
 uint32_t written=0;
 if(g_provider->CopyCubicPath(0,0,1,cubics,4,&written)!=0||written!=4)
    Fail("t=0 geometry transfer failed");
 const double r0=cubics[0].x0;
 if(g_provider->CopyCubicPath(1,12,24,cubics,4,&written)!=0)
    Fail("t=.5 geometry transfer failed");
 const double r1=cubics[0].x0;
 if(std::abs(r0-r1)<1)Fail("time-varying curve did not change");
 written=0;
 if(g_provider->CopyCubicPath(0,0,1,cubics,2,&written)==0||written!=4)
    Fail("capacity check failed");
 std::fprintf(stderr,"MOCK stage=before_consumer_about\n");
 using Effect=PF_Err (*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*);
 Effect effect=reinterpret_cast<Effect>(GetProcAddress(consumer,"EffectMain"));
 if(!effect)Fail("consumer EffectMain not exported");
 PF_InData in{};PF_OutData out{};PF_ParamDef* params[1]{nullptr};
 PF_UtilCallbacks utilities{};
 utilities.ansi.sprintf=MockSprintf;
 in.utils=&utilities;
 in.pica_basicP=&g_basic;
 std::fprintf(stderr,"MOCK stage=calling_consumer_about\n");
 if(effect(PF_Cmd_ABOUT,&in,&out,params,nullptr)!=0)
    Fail("consumer EffectMain About failed");
 std::fprintf(stderr,"MOCK stage=after_consumer_about\n");
 if(!std::strstr(out.return_msg,"connected") ||
    !std::strstr(out.return_msg,"segments: 4"))
    Fail("consumer About did not receive native vector geometry");
 if(g_suite_acquires<1)Fail("consumer did not acquire provider PICA Suite");
 std::printf("PASS provider_aex_load=1 consumer_aex_load=1 suite_registered=%d "
    "native_cubics=%u time0_radius=%.3f time05_radius=%.3f "
    "consumer_suite_acquires=%d consumer_about=%s\n",
    g_suite_add_calls,info.cubic_count,r0,r1,g_suite_acquires,out.return_msg);
 // Host owns module unloading; minimal mock exits without simulating AE death hooks.
 return 0;
}
