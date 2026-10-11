// CNL Native Vector Host Bridge Probe (research).
// A REAL AEGP carrying CNL's independently owned vector-data core.
// This does NOT register a native Adobe TDB type or BEE operator.
// No private mutable API calls. No Shape Layer, Mask, PF_World, or script.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include "../host_abi_shared/NativeProjectSafety.h"
#include "CNLNativeVectorCore.h"
#include <Windows.h>
#include <wincrypt.h>
#include <cstdio>
#include <cstring>
#include <string>
#include <memory>
#include <algorithm>
#pragma comment(lib, "Advapi32.lib")

namespace {
SPBasicSuite* g_basic=nullptr;
AEGP_PluginID g_plugin=0;
AEGP_Command g_command=0;
struct DestroyDoc{void operator()(CNL_Document* p) const{cnl_document_destroy(p);}};
std::string exeModuleSHA256(const wchar_t* name) {
 HMODULE module=GetModuleHandleW(name);
 if(!module)return {};
 wchar_t path[4096]{};
 if(!GetModuleFileNameW(module,path,4096))return {};
 HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                        nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(file==INVALID_HANDLE_VALUE)return {};
 HCRYPTPROV prov=0;HCRYPTHASH h=0;
 bool ok=CryptAcquireContextW(&prov,nullptr,nullptr,PROV_RSA_AES,CRYPT_VERIFYCONTEXT)!=FALSE;
 if(ok)ok=CryptCreateHash(prov,CALG_SHA_256,0,0,&h)!=FALSE;
 unsigned char bytes[65536];
 DWORD count=0;
 while(ok && ReadFile(file,bytes,sizeof(bytes),&count,nullptr)&&count){
  if(!CryptHashData(h,bytes,count,0)){ok=false;break;}
 }
 BYTE digest[32]{};
 DWORD n=sizeof(digest);
 if(ok)ok=CryptGetHashParam(h,HP_HASHVAL,digest,&n,0)!=FALSE&&n==32;
 if(h)CryptDestroyHash(h);
 if(prov)CryptReleaseContext(prov,0);
 CloseHandle(file);
 if(!ok)return {};
 static const char digits[]="0123456789abcdef";
 std::string out;
 for(BYTE x:digest){out.push_back(digits[x>>4]);out.push_back(digits[x&15]);}
 return out;
}
int pinnedTDB(const std::string& sha) {
 if(sha=="82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b")
  return 2026;
 if(sha=="2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69")
  return 2025;
 return 0;
}
struct ExportObservation {
 int module=0,pinned=0,getter=0,creator=0,registrar=0,unregistrar=0,canonical=0;
 int getter_pattern=0,factory_nonnull=0;
 std::string sha;
};
ExportObservation inspectTDB(){
 ExportObservation r;
 HMODULE tdb=GetModuleHandleW(L"TDB.dll");
 if(!tdb)return r;
 r.module=1;
 r.sha=exeModuleSHA256(L"TDB.dll");
 r.pinned=pinnedTDB(r.sha);
 const auto find=[tdb](const char* symbol){return GetProcAddress(tdb,symbol);};
 const auto getter=find("?Get_AE_StreamFactory@@YAPEAVTDB_StreamFactory@@XZ");
 r.getter=getter!=nullptr;
 r.creator=find("?Create@TDB_ParamPathStream@@SAPEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z")!=nullptr;
 r.registrar=find("?RegisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@V?$function@$$A6APEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z@std@@_N@Z")!=nullptr;
 r.unregistrar=find("?UnregisterFactoryFunc@TDB_StreamFactory@@QEAA_NAEBVTDB_MatchName@@@Z")!=nullptr;
 r.canonical=find("?GetCanonicalInstance@TDB_StreamFactory@@QEAAPEAVTDB_StreamBase@@AEBVTDB_MatchName@@@Z")!=nullptr;
 // Do not invoke private getter without an exact DLL hash and known tiny code fingerprint.
 if(r.pinned && getter) {
  auto code=reinterpret_cast<const unsigned char*>(getter);
  MEMORY_BASIC_INFORMATION mem{};
  if(VirtualQuery(code,&mem,sizeof(mem)) &&
     mem.State==MEM_COMMIT && !(mem.Protect&(PAGE_NOACCESS|PAGE_GUARD)) &&
     code[0]==0x48&&code[1]==0x8b&&code[2]==0x05&&code[7]==0xc3) {
   r.getter_pattern=1;
   using Getter=void*(__cdecl*)();
   r.factory_nonnull=reinterpret_cast<Getter>(getter)()!=nullptr;
   // Only compare pointer with nullptr. NEVER dereference/store it.
  }
 }
 return r;
}
A_Err RunPreflight(){
 if(!g_basic)return A_Err_NONE;
 AEGP_SuiteHandler suites(g_basic);
 char folder[MAX_PATH+2]{};
 DWORD length=GetTempPathA(MAX_PATH,folder);
 if(!length || length>MAX_PATH)return A_Err_NONE;
 std::string path=std::string(folder)+"CNL_NativeVector_HostPreflight.tsv";
 FILE* output=fopen(path.c_str(),"wb");
 if(!output){suites.UtilitySuite3()->AEGP_ReportInfo(g_plugin,
  "CNL Native Vector: cannot write the TEMP preflight report.");return A_Err_NONE;}
 const auto obs=inspectTDB();
 std::fprintf(output,"# CNL AEGP in-host static/native source preflight. No host mutation.\n");
 std::fprintf(output,"# This is NOT an AE-native registered Contents, Path or renderer.\n");
 std::fprintf(output,"field\tvalue\n");
 std::fprintf(output,"tdb_module_loaded\t%d\n",obs.module);
 std::fprintf(output,"tdb_sha256\t%s\n",obs.sha.c_str());
 std::fprintf(output,"pinned_AE_TDB_year\t%d\n",obs.pinned);
 std::fprintf(output,"private_factory_getter_export\t%d\n",obs.getter);
 std::fprintf(output,"private_creator_ParamPathStream_export\t%d\n",obs.creator);
 std::fprintf(output,"private_factory_registrar_export\t%d\n",obs.registrar);
 std::fprintf(output,"private_factory_unregister_export\t%d\n",obs.unregistrar);
 std::fprintf(output,"private_canonical_instance_export\t%d\n",obs.canonical);
 std::fprintf(output,"getter_exact_opcode_pattern\t%d\n",obs.getter_pattern);
 std::fprintf(output,"getter_factory_pointer_nonnull\t%d\n",obs.factory_nonnull);
 // Public AEGP suites only: reflect the SAME empty-project gate as the
 // dangerous probe, without ever executing private registration.
 const auto projectGate=CNL_CheckDisposableProject(suites);
 std::fprintf(output,"disposable_project_gate_pass\t%d\n",projectGate.empty?1:0);
 std::fprintf(output,"disposable_project_gate_reason\t%s\n",projectGate.reason);
 std::fprintf(output,"disposable_project_count\t%ld\n",(long)projectGate.projects);
 std::fprintf(output,"disposable_non_root_items\t%ld\n",(long)projectGate.non_root_items);
 std::fprintf(output,"disposable_render_queue_items\t%ld\n",(long)projectGate.render_queue_items);
 std::fprintf(output,"disposable_project_is_dirty\t%d\n",projectGate.dirty?1:0);
 std::fprintf(output,"private_registry_registration_invoked\t0\n");
 std::fprintf(output,"new_native_host_stream_created\t0\n");
 std::fprintf(output,"AE_native_Pen_tool_linked\t0\n");
 std::fprintf(output,"AE_VectorArt_renderer_linked\t0\n");
 std::unique_ptr<CNL_Document,DestroyDoc> document(cnl_document_create());
 CNL_Status status=CNL_INTERNAL_ERROR;
 CNL_NodeId parent=0,path_id=0;
 uint32_t count=0;
 CNL_CubicBezier cubic[4]{};
 if(document){
  status=cnl_document_add_group(document.get(),cnl_document_root(document.get()),
                                "CNL procedural native geometry",&parent);
  if(status==CNL_OK)
   status=cnl_document_add_ellipse(document.get(),parent,"Generated Cubic Ellipse",
                                      200,100,75,45,&path_id);
  if(status==CNL_OK){
   count=4;
   status=cnl_document_copy_cubics(document.get(),path_id,cubic,&count);
  }
 }
 std::fprintf(output,"CNL_document_created\t%d\n",document!=nullptr);
 std::fprintf(output,"CNL_double_bezier_cubic_status\t%d\n",(int)status);
 std::fprintf(output,"CNL_generated_path_id\t%llu\n",(unsigned long long)path_id);
 std::fprintf(output,"CNL_native_cubic_segment_count\t%u\n",count);
 if(status==CNL_OK){
  std::fprintf(output,"CNL_first_cubic_P0X\t%.17g\n",cubic[0].x0);
  std::fprintf(output,"CNL_first_cubic_P0Y\t%.17g\n",cubic[0].y0);
  std::fprintf(output,"CNL_first_cubic_P1X\t%.17g\n",cubic[0].x1);
  std::fprintf(output,"CNL_first_cubic_P1Y\t%.17g\n",cubic[0].y1);
  std::fprintf(output,"CNL_first_cubic_P2X\t%.17g\n",cubic[0].x2);
  std::fprintf(output,"CNL_first_cubic_P2Y\t%.17g\n",cubic[0].y2);
  std::fprintf(output,"CNL_first_cubic_P3X\t%.17g\n",cubic[0].x3);
  std::fprintf(output,"CNL_first_cubic_P3Y\t%.17g\n",cubic[0].y3);
  size_t needed=0;
  CNL_Status archive_status=cnl_document_serialize(document.get(),nullptr,&needed);
  std::fprintf(output,"CNL_procedural_document_archive_bytes\t%zu\n",
   archive_status==CNL_NO_SPACE?needed:0);
 }
 std::fclose(output);
 char msg[510]{};
 std::snprintf(msg,sizeof(msg),
  "CNL Native Vector Host Preflight: Bezier=%s, pinned TDB=%d, "
  "factory getter=%d, empty-project gate=%s. "
  "Adobe native type NOT registered. "
  "Report: TEMP\\CNL_NativeVector_HostPreflight.tsv",
  status==CNL_OK?"YES":"FAIL",obs.pinned,obs.factory_nonnull,
  projectGate.empty?"PASS":"BLOCKED");
 suites.UtilitySuite3()->AEGP_ReportInfo(g_plugin,msg);
 return A_Err_NONE;
}
A_Err CommandHook(AEGP_GlobalRefcon,AEGP_CommandRefcon,AEGP_Command command,
                  AEGP_HookPriority,A_Boolean already_handled,A_Boolean* handled){
 if(already_handled||command!=g_command)return A_Err_NONE;
 if(handled)*handled=TRUE;
 return RunPreflight();
}
A_Err UpdateHook(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
 if(!g_basic)return A_Err_NONE;
 AEGP_SuiteHandler suites(g_basic);
 return suites.CommandSuite1()->AEGP_EnableCommand(g_command);
}
} // namespace
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* basic,A_long,A_long,
                     AEGP_PluginID id,AEGP_GlobalRefcon*){
 g_basic=basic;g_plugin=id;
 AEGP_SuiteHandler suites(basic);
 A_Err err=suites.CommandSuite1()->AEGP_GetUniqueCommand(&g_command);
 if(!err)err=suites.CommandSuite1()->AEGP_InsertMenuCommand(
  g_command,"CNL Native Vector: Host Preflight (Read Only)",
  AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 if(!err)err=suites.RegisterSuite5()->AEGP_RegisterCommandHook(
  id,AEGP_HP_BeforeAE,AEGP_Command_ALL,CommandHook,nullptr);
 if(!err)err=suites.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(
  id,UpdateHook,nullptr);
 return err;
}
