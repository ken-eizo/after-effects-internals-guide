// EXP-SHAPE-030: DANGEROUS disposable-host private TDB type registration.
// Do not install for daily editing. No private calls at AEGP startup.
// Only user-triggered with exact pinned SHA256, one-shot explicit flag AND
// opt-in environment variable. No Masks, Shapes, scripts or PF_World rendering.
//
// Test goal (if host executed): is a newly named native TDB type accepted?
// Uses Adobe's COMPLETE native ParamPathStream Creator. Never fabricates
// a TDB_StreamBase, never touches Adobe vtables or project streams.
// IMPORTANT: Success does NOT establish editor/Contents/VectorArt support.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include <Windows.h>
#include <wincrypt.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <functional>
#include <string>
#include <vector>
#pragma comment(lib,"Advapi32.lib")

namespace {
SPBasicSuite* g_basic=nullptr;
AEGP_PluginID g_id=0;
AEGP_Command g_command=0;
static_assert(sizeof(void*)==8,"Only Windows x64 MSVC permitted");

struct alignas(16) NativeMatchNameOpaque {unsigned char guid[16];};
static_assert(sizeof(NativeMatchNameOpaque)==16,"TDB MatchName native GUID payload");
using CreatorSignature=void*(const NativeMatchNameOpaque&,void*,bool,unsigned,unsigned);
using CreatorObject=std::function<CreatorSignature>;
using Getter=void* (__cdecl*)();
using NativeNameConstructor=void* (__cdecl*)(NativeMatchNameOpaque*,const char*,bool);
using NativeParamPathCreator=void* (__cdecl*)(const NativeMatchNameOpaque&,void*,bool,unsigned,unsigned);
using NativeRegister=bool (__cdecl*)(void*,const NativeMatchNameOpaque&,CreatorObject,bool);
using NativeUnregister=bool (__cdecl*)(void*,const NativeMatchNameOpaque&);

std::string hashModule(HMODULE module){
 if(!module)return {};
 wchar_t path[4096]{};
 if(!GetModuleFileNameW(module,path,4096))return {};
 HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
  nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(file==INVALID_HANDLE_VALUE)return {};
 HCRYPTPROV prov=0;
 HCRYPTHASH h=0;
 bool good=CryptAcquireContextW(&prov,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=FALSE;
 if(good)good=CryptCreateHash(prov,CALG_SHA_256,0,0,&h)!=FALSE;
 unsigned char bytes[65536];
 DWORD count=0;
 while(good){
  if(!ReadFile(file,bytes,sizeof(bytes),&count,nullptr)){good=false;break;}
  if(!count)break;
  if(!CryptHashData(h,bytes,count,0)){good=false;break;}
 }
 BYTE hash[32]{};
 DWORD n=32;
 if(good)good=CryptGetHashParam(h,HP_HASHVAL,hash,&n,0)!=FALSE&&n==32;
 if(h)CryptDestroyHash(h);
 if(prov)CryptReleaseContext(prov,0);
 CloseHandle(file);
 if(!good)return {};
 static const char hexdigits[]="0123456789abcdef";
 std::string hex;
 hex.reserve(64);
 for(const auto b:hash){hex.push_back(hexdigits[b>>4]);hex.push_back(hexdigits[b&15]);}
 return hex;
}
int pinned(const std::string& digest){
 if(digest=="82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b")return 2026;
 if(digest=="2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69")return 2025;
 return 0;
}
void writeLog(FILE* out,const char* state,int number){
 if(!out)return;
 std::fprintf(out,"stage\t%s\t%d\n",state,number);
 std::fflush(out); // preserve last stage even if Adobe assertion exits host
}
void report(const char* message) {
 if(!g_basic)return;
 AEGP_SuiteHandler s(g_basic);
 s.UtilitySuite3()->AEGP_ReportInfo(g_id,message);
}
bool ackAndConsume(const std::string& tempDir,FILE* log){
 char value[256]{};
 const DWORD len=GetEnvironmentVariableA("CNL_TDB_DISPOSABLE_HOST_TEST",value,(DWORD)sizeof(value));
 if(len==0||len>=sizeof(value)||
    std::strcmp(value,"I_ACCEPT_PRIVATE_REGISTRY_CRASH_RISK")!=0){
  writeLog(log,"env_ack_missing",1);return false;
 }
 const std::string marker=tempDir+"CNL_TDB_DISPOSABLE_ACK.flag";
 FILE* file=fopen(marker.c_str(),"rb");
 if(!file){writeLog(log,"one_shot_ack_missing",1);return false;}
 char buffer[128]{};
 const size_t n=fread(buffer,1,sizeof(buffer)-1,file);
 fclose(file);
 std::string text(buffer,n);
 while(!text.empty()&&(text.back()=='\r'||text.back()=='\n'))text.pop_back();
 if(text!="CNL_TDB_ONLY_DISPOSABLE_NO_REAL_PROJECTS"){
  writeLog(log,"one_shot_ack_content_invalid",1);return false;
 }
 if(!DeleteFileA(marker.c_str())){writeLog(log,"one_shot_ack_cannot_consume",1);return false;}
 writeLog(log,"explicit_two_factor_ack_consumed",1);
 return true;
}

A_Err Run(){
 if(!g_basic)return A_Err_NONE;
 AEGP_SuiteHandler s(g_basic);
 char folder[MAX_PATH+2]{};
 DWORD len=GetTempPathA(MAX_PATH,folder);
 if(len==0||len>MAX_PATH)return A_Err_NONE;
 std::string tempDir=folder;
 FILE* log=fopen((tempDir+"CNL_PrivateTDB_Disposable_Test.tsv").c_str(),"wb");
 if(!log){report("CNL Private TDB: cannot write audit log. Nothing attempted.");return A_Err_NONE;}
 std::fprintf(log,
  "# PRIVATE ABI MUTATION RISK. Does not create AE Shape or Mask. No user project should be open.\n"
  "# Even an automatic unregister may not restore all AE internal state.\n"
  "kind\tlabel\tvalue\n");
 writeLog(log,"manual_command_started",1);
 // Fail closed: no active selected layer, and explicit 2-factor acknowledgement.
 AEGP_LayerH current=nullptr;
 A_Err layerResult=s.LayerSuite5()->AEGP_GetActiveLayer(&current);
 if(layerResult==A_Err_NONE&&current){
  writeLog(log,"active_layer_not_allowed",1);
  fclose(log);report("CNL Private TDB: REFUSED. Active layer detected.");return A_Err_NONE;
 }
 HMODULE tdb=GetModuleHandleW(L"TDB.dll");
 if(!tdb){
  writeLog(log,"TDB_module_missing",1);
  fclose(log);report("CNL Private TDB: REFUSED. TDB.dll not loaded.");return A_Err_NONE;
 }
 const std::string digest=hashModule(tdb);
 const int year=pinned(digest);
 std::fprintf(log,"fact\tTDB_sha256\t%s\n",digest.c_str());
 std::fprintf(log,"fact\tpinned_version\t%d\n",year);
 std::fflush(log);
 if(!year){
  writeLog(log,"binary_hash_unknown_or_failed",1);
  fclose(log);report("CNL Private TDB: REFUSED. Unknown TDB.dll version.");return A_Err_NONE;
 }
 const auto sym=[tdb](const char* name){return GetProcAddress(tdb,name);};
 auto get=sym("?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ");
 auto ctor=sym("??0TDB_MatchName@@QEAA@PEBD_N@Z");
 auto create=sym("?Create@TDB_ParamPathStream@@SAPEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z");
 auto reg=sym("?RegisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@V?$function@$$A6APEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z@std@@_N@Z");
 auto unreg=sym("?UnregisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@@Z");
 if(!get||!ctor||!create||!reg||!unreg){
  writeLog(log,"exact_exports_missing",1);
  fclose(log);report("CNL Private TDB: REFUSED. Native exports missing.");return A_Err_NONE;
 }
 const auto b=reinterpret_cast<const uint8_t*>(get);
 MEMORY_BASIC_INFORMATION mbi{};
 if(!VirtualQuery(b,&mbi,sizeof(mbi))||mbi.State!=MEM_COMMIT ||
   (mbi.Protect&(PAGE_NOACCESS|PAGE_GUARD))||
    !(b[0]==0x48&&b[1]==0x8b&&b[2]==0x05&&b[7]==0xc3)){
  writeLog(log,"getter_opcode_unknown",1);
  fclose(log);report("CNL Private TDB: REFUSED. Getter fingerprint mismatch.");return A_Err_NONE;
 }
 writeLog(log,"exact_host_binary_and_exports_validated",1);
 // Do not consume the one-shot ack until all read-only preflight checks pass.
 if(!ackAndConsume(tempDir,log)){
  fclose(log);report("CNL Private TDB: REFUSED. Disposable-test acknowledgement missing.");return A_Err_NONE;
 }
 // No standard Shape Layer or Mask is created here. This registration is
 // strictly a new MatchName to native class Creator factory-acceptance test.
 void* factory=reinterpret_cast<Getter>(get)();
 if(!factory){
  writeLog(log,"factory_pointer_null",1);
  fclose(log);report("CNL Private TDB: REFUSED. Factory pointer null.");return A_Err_NONE;
 }
 NativeMatchNameOpaque name{};
 char candidate[140]{};
 std::snprintf(candidate,sizeof(candidate),
  "CNL Experimental Native ParamPath Registration %lu",
  (unsigned long)GetCurrentProcessId());
 writeLog(log,"before_private_MatchName_constructor",1);
 reinterpret_cast<NativeNameConstructor>(ctor)(&name,candidate,false);
 writeLog(log,"private_MatchName_constructor_returned",1);
 const auto creator=reinterpret_cast<NativeParamPathCreator>(create);
 CreatorObject callable=[creator](const NativeMatchNameOpaque& m,void* f,
                                      bool a,unsigned b,unsigned c)->void*{
  // Correct native creation and allocator remain owned by Adobe.
  return creator(m,f,a,b,c);
 };
 writeLog(log,"before_private_register_factory_func",1);
 // Returns only after eager canonical CreateStream and native virtual calls.
 const bool installed=reinterpret_cast<NativeRegister>(reg)(
  factory,name,callable,false);
 writeLog(log,"register_result",installed?1:0);
 bool removed=false;
 if(installed){
  writeLog(log,"before_private_unregister_factory_func",1);
  removed=reinterpret_cast<NativeUnregister>(unreg)(factory,name);
  writeLog(log,"unregister_result",removed?1:0);
 }
 std::fprintf(log,"fact\tmatched_existing_Shape_Contents\t0\n");
 std::fprintf(log,"fact\tcreated_Mask_or_Shape_Layer\t0\n");
 std::fprintf(log,"fact\tindependent_Contents_owner_proven\t0\n");
 std::fprintf(log,"fact\tAE_Pen_editable_native_path_proven\t0\n");
 std::fprintf(log,"fact\tBEE_VectorArt_renderer_proven\t0\n");
 std::fclose(log);
 if(installed&&removed)report(
  "CNL Private TDB: experimental REGISTER and UNREGISTER returned success. "
  "This is NOT independent Contents/Pen/VectorArt. Inspect TEMP TSV; restart AE.");
 else report(
  "CNL Private TDB: registration failed or cleanup NOT confirmed! "
  "Inspect TEMP TSV. CLOSE AE. Never trust the current process for further experiments.");
 return A_Err_NONE;
}
A_Err CommandHook(AEGP_GlobalRefcon,AEGP_CommandRefcon,AEGP_Command command,
 AEGP_HookPriority,A_Boolean already,A_Boolean* handled){
 if(already||command!=g_command)return A_Err_NONE;
 if(handled)*handled=TRUE;
 return Run();
}
A_Err UpdateHook(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
 if(!g_basic)return A_Err_NONE;
 AEGP_SuiteHandler s(g_basic);
 return s.CommandSuite1()->AEGP_EnableCommand(g_command);
}
} // namespace
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* basic,A_long,A_long,
 AEGP_PluginID id,AEGP_GlobalRefcon*){
 g_basic=basic;g_id=id;
 AEGP_SuiteHandler s(basic);
 A_Err e=s.CommandSuite1()->AEGP_GetUniqueCommand(&g_command);
 if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(
  g_command,"CNL Private TDB: Disposable Type Registration (DANGER)",
  AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 if(!e)e=s.RegisterSuite5()->AEGP_RegisterCommandHook(
  g_id,AEGP_HP_BeforeAE,AEGP_Command_ALL,CommandHook,nullptr);
 if(!e)e=s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(
  g_id,UpdateHook,nullptr);
 return e;
}
