// CNL-native Shape runtime as an actual Adobe AEGP module.
// This lab does NOT insert a foreign BEE Layer or modify host/private TDB.
// A menu command exercises the CNL-owned document/Undo/vector renderer only.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include "CNLShapeRuntime.h"
#include <Windows.h>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>
// Defined in ChapeHostAdmissionProbe.cpp, outside this translation unit.
A_Err CNL_RunChapeHostProbe(SPBasicSuite*,AEGP_PluginID);
namespace {
SPBasicSuite* basic=nullptr;
AEGP_PluginID plugin=0;
AEGP_Command testCommand=0;
AEGP_Command chapeMenuCommand=0;
AEGP_Command chapeFallbackCommand=0;
AEGP_Command hostAdmissionCommand=0;
// The probe uses only public AEGP DynamicStreamSuite reads.
struct DestroyShape {
 void operator()(CNL_ShapeLayer* p)const{cnl_shape_destroy(p);}
};
using ShapePtr=std::unique_ptr<CNL_ShapeLayer,DestroyShape>;
void notify(const char* message) {
 if(!basic)return;
 AEGP_SuiteHandler s(basic);
 s.UtilitySuite3()->AEGP_ReportInfo(plugin,message);
}
A_Err selfTest(){
 char path[MAX_PATH+2]{};
 const DWORD n=GetTempPathA(MAX_PATH,path);
 if(!n||n>MAX_PATH)return A_Err_NONE;
 const std::string root=path;
 FILE* tsv=std::fopen((root+"CNL_NativeShapeLayer_Prototype.tsv").c_str(),"wb");
 if(!tsv){notify("CNL native prototype: Cannot write TEMP log.");return A_Err_NONE;}
 std::fprintf(tsv,"key\tvalue\n");
 std::fprintf(tsv,"experiment\tCNL Native Shape Layer Prototype Engine\n");
 std::fprintf(tsv,"ae_project_mutated\t0\nprivate_BEE_TDB_called\t0\n");
 ShapePtr shape(cnl_shape_create());
 const CNL_ShapeFeatures f=cnl_shape_features();
 std::fprintf(tsv,"adobe_native_contents_registered\t%u\n",f.connected_to_adobe_contents);
 std::fprintf(tsv,"adobe_native_layer_registered\t%u\n",f.connected_to_adobe_native_tdb);
 std::fprintf(tsv,"adobe_native_pen\t%u\n",f.connected_to_adobe_pen);
 std::fprintf(tsv,"adobe_native_vectorart\t%u\n",f.connected_to_adobe_vectorart);
 bool pass=shape&&cnl_shape_contents_root(shape.get())==1;
 CNL_NodeId group=0, pathid=0;
 if(pass)pass=cnl_shape_add_group(shape.get(),1,"CNL Independent Contents",&group)==CNL_OK;
 if(pass)pass=cnl_shape_add_ellipse(shape.get(),group,"Bezier Ellipse",200,135,85,55,&pathid)==CNL_OK;
 if(pass){
   CNL_PathVertex v{};
   pass=cnl_shape_get_vertex(shape.get(),pathid,0,&v)==CNL_OK;
   if(pass){
     v.x+=24;v.out_dx+=14;
     pass=cnl_shape_set_vertex(shape.get(),pathid,0,&v)==CNL_OK;
   }
 }
 if(pass)pass=cnl_shape_undo(shape.get())==CNL_OK;
 if(pass)pass=cnl_shape_redo(shape.get())==CNL_OK;
 std::vector<char> svg;
 if(pass){
   size_t needed=0;
   pass=cnl_shape_svg(shape.get(),nullptr,&needed)==CNL_NO_SPACE && needed>200;
   if(pass){
     svg.resize(needed);
     pass=cnl_shape_svg(shape.get(),svg.data(),&needed)==CNL_OK;
   }
 }
 if(pass){
   FILE* out=std::fopen((root+"CNL_NativeShapeLayer_Prototype.svg").c_str(),"wb");
   if(out){pass=std::fwrite(svg.data(),1,svg.size()-1,out)==svg.size()-1;std::fclose(out);}
   else pass=false;
 }
 size_t bytes=0;
 if(pass){
   pass=cnl_shape_archive(shape.get(),nullptr,&bytes)==CNL_NO_SPACE && bytes>48;
   if(pass){
     std::vector<unsigned char> archive(bytes);
     pass=cnl_shape_archive(shape.get(),archive.data(),&bytes)==CNL_OK;
     CNL_ShapeLayer* reread=nullptr;
     if(pass)pass=cnl_shape_from_archive(archive.data(),bytes,&reread)==CNL_OK;
     cnl_shape_destroy(reread);
   }
 }
 std::fprintf(tsv,"cubic_shape_node_id\t%llu\n",(unsigned long long)pathid);
 std::fprintf(tsv,"native_cnl_undo_depth\t%u\n",cnl_shape_undo_depth(shape.get()));
 std::fprintf(tsv,"native_cnl_archive_bytes\t%zu\n",bytes);
 std::fprintf(tsv,"native_cnl_engine_self_test_pass\t%d\n",int(pass));
 std::fclose(tsv);
 notify(pass?"CNL Native Shape runtime PASS. See TEMP\\CNL_NativeShapeLayer_Prototype.tsv and .svg. AE Contents NOT registered.":"CNL Native Shape runtime FAILED. See TEMP TSV.");
 return A_Err_NONE;
}
A_Err commandHook(AEGP_GlobalRefcon,AEGP_CommandRefcon,AEGP_Command cmd,AEGP_HookPriority,A_Boolean already,A_Boolean* handled){
 if(already || (cmd!=testCommand && cmd!=chapeMenuCommand && cmd!=chapeFallbackCommand && cmd!=hostAdmissionCommand))return A_Err_NONE;
 if(handled)*handled=TRUE;
 if(cmd==testCommand)return selfTest();
 if(cmd==hostAdmissionCommand)return CNL_RunChapeHostProbe(basic,plugin);
 // No Adobe-native CNL layer creator exists yet. Refuse a false substitute.
 notify("ChapeLayer: new native AE Layer type is not registered yet. No layer was created. ChapeLayer's custom C++ Contents engine is functional; use the read-only admission probe under Animation.");
 return A_Err_NONE;
}
A_Err updateHook(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
 if(!basic)return A_Err_NONE;
 AEGP_SuiteHandler s(basic);
 A_Err e=s.CommandSuite1()->AEGP_EnableCommand(testCommand);
 if(!e)e=s.CommandSuite1()->AEGP_EnableCommand(chapeMenuCommand);
 if(!e)e=s.CommandSuite1()->AEGP_EnableCommand(chapeFallbackCommand);
 if(!e)e=s.CommandSuite1()->AEGP_EnableCommand(hostAdmissionCommand);
 return e;
}
}
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* b,A_long,A_long,AEGP_PluginID id,AEGP_GlobalRefcon*){
 basic=b;plugin=id;
 AEGP_SuiteHandler s(b);
 A_Err e=s.CommandSuite1()->AEGP_GetUniqueCommand(&testCommand);
 const A_Err testId=e;
 if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(testCommand,
    "CNL Native Shape: Independent Engine Self-Test (No Host Edits)",
    AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 const A_Err testInsert=e;
 A_Err newId=s.CommandSuite1()->AEGP_GetUniqueCommand(&chapeMenuCommand);
 A_Err newInsert=newId;
 if(!newId)newInsert=s.CommandSuite1()->AEGP_InsertMenuCommand(chapeMenuCommand,
    "ChapeLayer (Native Type Pending)",
    AEGP_Menu_NEW,AEGP_MENU_INSERT_AT_TOP);
 // Experimental fallback: distinguish a missing NEW submenu item from
 // failure to register the AEGP command anywhere at all.
 A_Err fallbackId=s.CommandSuite1()->AEGP_GetUniqueCommand(&chapeFallbackCommand);
 A_Err fallbackInsert=fallbackId;
 if(!fallbackId)fallbackInsert=s.CommandSuite1()->AEGP_InsertMenuCommand(chapeFallbackCommand,
    "ChapeLayer: Native Type Status (Fallback)",
    AEGP_Menu_LAYER,AEGP_MENU_INSERT_AT_TOP);
 A_Err probeId=s.CommandSuite1()->AEGP_GetUniqueCommand(&hostAdmissionCommand);
 A_Err probeInsert=probeId;
 if(!probeId)probeInsert=s.CommandSuite1()->AEGP_InsertMenuCommand(hostAdmissionCommand,
    "ChapeLayer: Inspect Native Contents Admission (Read Only)",
    AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
 A_Err hooks=s.RegisterSuite5()->AEGP_RegisterCommandHook(
    id,AEGP_HP_BeforeAE,AEGP_Command_ALL,commandHook,nullptr);
 A_Err update=s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(id,updateHook,nullptr);
 // Log command and menu insertion results at actual AE load time; a zero
 // result means the call succeeded, not that AE rendered the menu item.
 char tmp[MAX_PATH+2]{};
 const DWORD n=GetTempPathA(MAX_PATH,tmp);
 if(n && n<MAX_PATH){
   FILE* out=fopen((std::string(tmp)+"ChapeLayer_MenuRegistration.tsv").c_str(),"wb");
   if(out){
      fprintf(out,"kind\tvalue\nversion\tChapeLayer_MenuDiagnose_v2\n");
      fprintf(out,"test_command_id\t%ld\ntest_get_error\t%d\ntest_insert_error\t%d\n",
          (long)testCommand,(int)testId,(int)testInsert);
      fprintf(out,"new_command_id\t%ld\nnew_get_error\t%d\nnew_insert_error\t%d\n",
          (long)chapeMenuCommand,(int)newId,(int)newInsert);
      fprintf(out,"fallback_command_id\t%ld\nfallback_get_error\t%d\nfallback_insert_error\t%d\n",
          (long)chapeFallbackCommand,(int)fallbackId,(int)fallbackInsert);
      fprintf(out,"probe_command_id\t%ld\nprobe_get_error\t%d\nprobe_insert_error\t%d\n",
          (long)hostAdmissionCommand,(int)probeId,(int)probeInsert);
      fprintf(out,"command_hook_error\t%d\nupdate_hook_error\t%d\n",
          (int)hooks,(int)update);
      fprintf(out,"AEGP_Menu_NEW_enum\t%d\nAEGP_Menu_LAYER_enum\t%d\n",
          (int)AEGP_Menu_NEW,(int)AEGP_Menu_LAYER);
      fclose(out);
   }
 }
 return hooks?hooks:(update?update:(testInsert?testInsert:A_Err_NONE));
}
