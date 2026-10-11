// CompNodeAE Native Editable Path Bridge (EXPERIMENTAL AEGP).
// Converts REAL AEGP/PICA-authored cubic geometry into an AE-owned native Mask
// stream on a user-selected ORDINARY AV layer. No Shape Layer is created.
// All mutations are behind an explicit Animation menu action, with Undo.
// IMPORTANT: This uses PUBLIC mask streams, not effect-owned native Contents.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "entry.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include "VectorBridgeSuite.h"
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <algorithm>

namespace {
SPBasicSuite* basic=nullptr;
AEGP_PluginID pid=0;
AEGP_Command create_cmd=0;
AEGP_Command rendered_mask_cmd=0;
AEGP_Command inspect_cmd=0;

void Info(const char* text) {
  if(!basic)return;
  AEGP_SuiteHandler s(basic);
  s.UtilitySuite3()->AEGP_ReportInfo(pid,text);
}

bool PicaGetCubics(const A_Time& time,CNL_VectorCubicV1 (&out)[4]) {
  if(!basic || time.scale<=0)return false;
  const void* raw=nullptr;
  if(basic->AcquireSuite(kCNLVectorBridgeSuite1,
                         kCNLVectorBridgeSuiteVersion1,&raw)!=0 || !raw)
    return false;
  auto* api=static_cast<const CNL_VectorBridgeSuite1*>(raw);
  CNL_VectorPathInfoV1 inf{sizeof(CNL_VectorPathInfoV1),0,0,0};
  uint32_t count=0;
  bool result=(api->DescribePath(1,&inf)==A_Err_NONE &&
     inf.cubic_count==4 && inf.closed!=0 &&
     api->CopyCubicPath(1,time.value,time.scale,out,4,&count)==A_Err_NONE &&
     count==4);
  if(result){
    const double* p=reinterpret_cast<const double*>(out);
    for(size_t i=0;i<4*8;++i)if(!std::isfinite(p[i]))result=false;
  }
  basic->ReleaseSuite(kCNLVectorBridgeSuite1,kCNLVectorBridgeSuiteVersion1);
  return result;
}

A_Err CreateEditableMask(bool use_native_mask_rendering) {
  AEGP_SuiteHandler s(basic);
  AEGP_LayerH layer=nullptr;
  A_Err err=s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
  if(err||!layer) {
    Info("Select exactly one ordinary Solid/Footage layer, then try again.");
    return err;
  }
  AEGP_ObjectType ty=AEGP_ObjectType_NONE;
  err=s.LayerSuite5()->AEGP_GetLayerObjectType(layer,&ty);
  if(err)return err;
  if(ty!=AEGP_ObjectType_AV){
    Info("This experiment only accepts an ordinary AV layer, not a Shape Layer.");
    return A_Err_NONE;
  }
  A_Time t{};
  err=s.LayerSuite5()->AEGP_GetLayerCurrentTime(
      layer,AEGP_LTimeMode_CompTime,&t);
  if(err)return err;
  CNL_VectorCubicV1 cubic[4]{};
  if(!PicaGetCubics(t,cubic)){
    Info("VectorBridgeAEGP suite unavailable; native path was NOT created.");
    return A_Err_NONE;
  }

  // Coordinates are layer-local. This only creates a native editable Mask,
  // not an effect parameter subgroup, VectorArt owner, or native BEE operator.
  AEGP_ItemH item=nullptr;
  A_long w=0,h=0;
  err=s.LayerSuite5()->AEGP_GetLayerSourceItem(layer,&item);
  if(err||!item) {
    Info("This selected layer has no supported source dimensions.");
    return err;
  }
  err=s.ItemSuite9()->AEGP_GetItemDimensions(item,&w,&h);
  if(err||w<=0||h<=0)return err?err:A_Err_NONE;

  err=s.UtilitySuite3()->AEGP_StartUndoGroup(
         "CompNodeAE: Create Native Editable Mask from PICA");
  if(err)return err;

  AEGP_MaskRefH mask=nullptr;
  AEGP_StreamRefH stream=nullptr;
  AEGP_StreamValue val{};
  bool hasVal=false,created=false;
  A_long index=-1;

  do {
    err=s.MaskSuite4()->AEGP_CreateNewMask(layer,&mask,&index);
    if(err||!mask)break;
    created=true;
    // NONE: preserve the original layer image/effect render while allowing
    // native Pen handles and a genuine editable timeline Mask Path.
    err=s.MaskSuite4()->AEGP_SetMaskMode(mask,
          use_native_mask_rendering?PF_MaskMode_ADD:PF_MaskMode_NONE);
    if(err)break;
    err=s.MaskSuite4()->AEGP_SetMaskIsRotoBezier(mask,FALSE);
    if(err)break;
    err=s.StreamSuite2()->AEGP_GetNewMaskStream(pid,mask,
                                               AEGP_MaskStream_OUTLINE,&stream);
    if(err||!stream)break;
    err=s.StreamSuite2()->AEGP_GetNewStreamValue(pid,stream,
            AEGP_LTimeMode_CompTime,&t,TRUE,&val);
    if(err)break;
    hasVal=true;
    if(!val.val.mask){err=1;break;}

    for(A_long i=0;i<4 && !err;++i)
      err=s.MaskOutlineSuite2()->AEGP_CreateVertex(val.val.mask,i);
    if(err)break;
    for(A_long i=0;i<4 && !err;++i){
      const CNL_VectorCubicV1& cur=cubic[i];
      const CNL_VectorCubicV1& prior=cubic[(i+3)%4];
      AEGP_MaskVertex v{};
      v.x=cur.x0+w/2.0;
      v.y=cur.y0+h/2.0;
      // AEGP_MaskVertex tangents are RELATIVE to the vertex; cubic controls
      // x2,y2 of preceding segment are in-tangent at the current endpoint.
      v.tan_in_x=prior.x2-cur.x0;
      v.tan_in_y=prior.y2-cur.y0;
      v.tan_out_x=cur.x1-cur.x0;
      v.tan_out_y=cur.y1-cur.y0;
      err=s.MaskOutlineSuite2()->AEGP_SetMaskOutlineVertexInfo(
                      val.val.mask,i,&v);
    }
    if(err)break;
    err=s.MaskOutlineSuite2()->AEGP_SetMaskOutlineOpen(val.val.mask,FALSE);
    if(err)break;
    // SetStreamValue may ONLY be called on an unkeyframed stream; a newly
    // created native mask meets that precondition.
    err=s.StreamSuite2()->AEGP_SetStreamValue(pid,stream,&val);
  } while(false);

  if(hasVal)(void)s.StreamSuite2()->AEGP_DisposeStreamValue(&val);
  if(stream)(void)s.StreamSuite2()->AEGP_DisposeStream(stream);
  // Do not leave an invalid half-constructed native path behind.
  if(err&&created&&mask)(void)s.MaskSuite4()->AEGP_DeleteMaskFromLayer(mask);
  if(mask)(void)s.MaskSuite4()->AEGP_DisposeMask(mask);
  const A_Err endErr=s.UtilitySuite3()->AEGP_EndUndoGroup();
  if(!err)err=endErr;
  if(err){
    Info("Native mask creation failed; any partial created mask was rolled back.");
  } else {
    if(use_native_mask_rendering) {
      Info("Created a real native AE Mask Path in ADD mode. The native MASK "
           "renderer now clips this ordinary layer, and the Pen tool edits "
           "the four Bezier handles. This is NOT Shape Contents or VectorArt.");
    } else {
      Info("Created a real native AE Mask Path in NONE mode (image unchanged). "
           "Press M and edit its four native Bezier vertices with AE Pen/Selection. "
           "No Shape Layer or script; still NOT effect-owned Contents.");
    }
  }
  return err;
}

A_Err InspectNativeOwners() {
  AEGP_SuiteHandler s(basic);
  AEGP_LayerH layer=nullptr;
  A_Err err=s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
  if(err||!layer){Info("Select a layer to inspect first.");return err;}
  AEGP_ObjectType ty=AEGP_ObjectType_NONE;
  err=s.LayerSuite5()->AEGP_GetLayerObjectType(layer,&ty);
  if(err)return err;
  AEGP_StreamRefH root=nullptr;
  err=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefForLayer(pid,layer,&root);
  if(err||!root)return err;
  A_long count=0; AEGP_StreamGroupingType gt=AEGP_StreamGroupingType_NONE;
  A_Err tErr=s.DynamicStreamSuite2()->AEGP_GetStreamGroupingType(root,&gt);
  if(!tErr && gt!=AEGP_StreamGroupingType_LEAF)
    tErr=s.DynamicStreamSuite2()->AEGP_GetNumStreamsInGroup(root,&count);
  FILE* f=nullptr;
  std::string fname=std::string(getenv("TEMP")?getenv("TEMP"):".")+
       "\\CNL_NativePath_OwnerProbe.tsv";
  fopen_s(&f,fname.c_str(),"wb");
  if(f){
    fprintf(f,"selected_layer_object_type\t%ld\nroot_group_type\t%ld\nroot_children\t%ld\nquery_error\t%ld\n",
          long(ty),long(gt),long(count),long(tErr));
    for(A_long i=0;!tErr && i<count;++i){
      AEGP_StreamRefH child=nullptr;
      A_Err e=s.DynamicStreamSuite2()->AEGP_GetNewStreamRefByIndex(
                                       pid,root,i,&child);
      if(!e && child){
        A_char match[AEGP_MAX_STREAM_MATCH_NAME_SIZE]{};
        (void)s.DynamicStreamSuite2()->AEGP_GetMatchName(child,match);
        fprintf(f,"root_child\t%ld\t%s\n",long(i),match);
        (void)s.StreamSuite2()->AEGP_DisposeStream(child);
      }
    }
    fclose(f);
  }
  (void)s.StreamSuite2()->AEGP_DisposeStream(root);
  Info("Native root stream types recorded in TEMP\\CNL_NativePath_OwnerProbe.tsv (read only).");
  return err;
}

A_Err Command(AEGP_GlobalRefcon,AEGP_CommandRefcon,
              AEGP_Command action,AEGP_HookPriority,
              A_Boolean already_handled,A_Boolean* handled){
  if(already_handled)return A_Err_NONE;
  if(action!=create_cmd&&action!=inspect_cmd&&action!=rendered_mask_cmd)
    return A_Err_NONE;
  if(handled)*handled=TRUE;
  if(action==create_cmd)return CreateEditableMask(false);
  if(action==rendered_mask_cmd)return CreateEditableMask(true);
  return InspectNativeOwners();
}
A_Err Update(AEGP_GlobalRefcon,AEGP_UpdateMenuRefcon,AEGP_WindowType){
  AEGP_SuiteHandler s(basic);
  AEGP_LayerH layer=nullptr;
  (void)s.LayerSuite5()->AEGP_GetActiveLayer(&layer);
  if(layer){
    (void)s.CommandSuite1()->AEGP_EnableCommand(create_cmd);
    (void)s.CommandSuite1()->AEGP_EnableCommand(rendered_mask_cmd);
    return s.CommandSuite1()->AEGP_EnableCommand(inspect_cmd);
  }
  (void)s.CommandSuite1()->AEGP_DisableCommand(create_cmd);
  (void)s.CommandSuite1()->AEGP_DisableCommand(rendered_mask_cmd);
  return s.CommandSuite1()->AEGP_DisableCommand(inspect_cmd);
}
}
extern "C" DllExport AEGP_PluginInitFuncPrototype EntryPointFunc;
A_Err EntryPointFunc(SPBasicSuite* p,A_long,A_long,
                     AEGP_PluginID id,AEGP_GlobalRefcon*){
  basic=p;pid=id;
  AEGP_SuiteHandler s(p);
  A_Err e=s.CommandSuite1()->AEGP_GetUniqueCommand(&create_cmd);
  if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(
      create_cmd,"CompNodeAE: Create Native Editable Mask from PICA",
      AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
  if(!e)e=s.CommandSuite1()->AEGP_GetUniqueCommand(&rendered_mask_cmd);
  if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(
      rendered_mask_cmd,"CompNodeAE: Native Mask Renderer (ADD, Clips Layer)",
      AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
  if(!e)e=s.CommandSuite1()->AEGP_GetUniqueCommand(&inspect_cmd);
  if(!e)e=s.CommandSuite1()->AEGP_InsertMenuCommand(
      inspect_cmd,"CompNodeAE: Inspect Native Owner Roots (Read Only)",
      AEGP_Menu_ANIMATION,AEGP_MENU_INSERT_AT_TOP);
  if(!e)e=s.RegisterSuite5()->AEGP_RegisterCommandHook(
      pid,AEGP_HP_BeforeAE,AEGP_Command_ALL,Command,nullptr);
  if(!e)e=s.RegisterSuite5()->AEGP_RegisterUpdateMenuHook(
      pid,Update,nullptr);
  return e;
}
