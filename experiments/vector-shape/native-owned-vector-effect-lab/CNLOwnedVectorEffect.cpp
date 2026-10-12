// Effect-owned independent vector document. PUBLIC Adobe SDK ONLY.
// No Mask/Shape layers, no TDB/BEE private API, no AE-native Pen tool yet.
#include "AEConfig.h"
#include "entry.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_Macros.h"
#include "Param_Utils.h"
#include "SPBasic.h"
#include "CNLNativeVectorCore.h"
#include "VectorRenderer.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
namespace {
constexpr uint32_t kMagic=0x314c4e43;
constexpr size_t kMaxArchive=1024*1024;
constexpr int kInput=0,kDoc=1,kStroke=2,kColor=3,kClear=4,kCount=5;
constexpr char kPrefix[]="CNLVEC1:"; // reversible hexadecimal AE text archive
struct Header {uint32_t magic,bytes;};
PF_Err Fail(){return PF_Err_BAD_CALLBACK_PARAM;}
bool Host(PF_InData* in_data){return in_data&&in_data->utils&&in_data->utils->host_new_handle&&
 in_data->utils->host_get_handle_size&&in_data->utils->host_dispose_handle&&
 in_data->utils->host_lock_handle&&in_data->utils->host_unlock_handle;}
PF_Err NewBytes(PF_InData* in_data,const void* src,size_t count,PF_ArbitraryH* out){
 if(!Host(in_data)||!out||!src||!count||count>kMaxArchive)return Fail();
 *out=nullptr;
 auto h=PF_NEW_HANDLE(static_cast<A_HandleSize>(count+sizeof(Header)));
 if(!h)return Fail();
 auto p=static_cast<unsigned char*>(PF_LOCK_HANDLE(h));
 if(!p){PF_DISPOSE_HANDLE(h);return Fail();}
 Header hd{kMagic,static_cast<uint32_t>(count)};
 std::memcpy(p,&hd,sizeof(hd));std::memcpy(p+sizeof(hd),src,count);
 PF_UNLOCK_HANDLE(h);*out=h;return PF_Err_NONE;
}
bool Read(PF_InData* in_data,PF_ArbitraryH h,std::vector<uint8_t>& bytes){
 if(!Host(in_data)||!h)return false;
 size_t total=static_cast<size_t>(PF_GET_HANDLE_SIZE(h));
 if(total<=sizeof(Header)||total>kMaxArchive+sizeof(Header))return false;
 auto p=static_cast<const uint8_t*>(PF_LOCK_HANDLE(h));
 if(!p)return false;
 Header hd{};std::memcpy(&hd,p,sizeof(hd));
 bool good=hd.magic==kMagic&&hd.bytes>0&&hd.bytes==total-sizeof(hd);
 if(good)bytes.assign(p+sizeof(hd),p+total);
 PF_UNLOCK_HANDLE(h);
 if(!good)return false;
 CNL_Document* doc=nullptr;
 good=cnl_document_deserialize(bytes.data(),bytes.size(),&doc)==CNL_OK&&doc;
 if(doc)cnl_document_destroy(doc);
 return good;
}
PF_Err Copy(PF_InData* in_data,PF_ArbitraryH src,PF_ArbitraryH* dst){
 std::vector<uint8_t> bytes;
 return Read(in_data,src,bytes)?NewBytes(in_data,bytes.data(),bytes.size(),dst):Fail();
}
PF_Err Default(PF_InData* in_data,PF_ArbitraryH* dst){
 auto doc=cnl_document_create();if(!doc)return Fail();
 CNL_NodeId group=0,path=0;
 bool ok=cnl_document_add_group(doc,cnl_document_root(doc),"Contents",&group)==CNL_OK &&
 cnl_document_add_ellipse(doc,group,"Bezier Ellipse",0,0,128,92,&path)==CNL_OK;
 size_t n=0;
 if(ok)ok=cnl_document_serialize(doc,nullptr,&n)==CNL_NO_SPACE&&n&&n<=kMaxArchive;
 std::vector<uint8_t> b(n);
 if(ok)ok=cnl_document_serialize(doc,b.data(),&n)==CNL_OK;
 cnl_document_destroy(doc);
 return ok?NewBytes(in_data,b.data(),n,dst):Fail();
}
PF_Err Arb(PF_InData* in_data,PF_ArbParamsExtra* ex){
 if(!Host(in_data)||!ex||ex->id!=1)return Fail();
 switch(ex->which_function){
 case PF_Arbitrary_NEW_FUNC:return Default(in_data,ex->u.new_func_params.arbPH);
 case PF_Arbitrary_DISPOSE_FUNC:
  if(ex->u.dispose_func_params.arbH)PF_DISPOSE_HANDLE(ex->u.dispose_func_params.arbH);
  return PF_Err_NONE;
 case PF_Arbitrary_COPY_FUNC:
  return Copy(in_data,ex->u.copy_func_params.src_arbH,ex->u.copy_func_params.dst_arbPH);
 case PF_Arbitrary_FLAT_SIZE_FUNC:{
  auto& q=ex->u.flat_size_func_params;
  std::vector<uint8_t> b;
  if(!q.flat_data_sizePLu||!Read(in_data,q.arbH,b))return Fail();
  *q.flat_data_sizePLu=static_cast<A_u_long>(b.size());return PF_Err_NONE;}
 case PF_Arbitrary_FLATTEN_FUNC:{
  auto& q=ex->u.flatten_func_params;
  std::vector<uint8_t> b;
  if(!q.flat_dataPV||!Read(in_data,q.arbH,b)||q.buf_sizeLu!=b.size())return Fail();
  std::memcpy(q.flat_dataPV,b.data(),b.size());return PF_Err_NONE;}
 case PF_Arbitrary_UNFLATTEN_FUNC:{
  auto& q=ex->u.unflatten_func_params;
  if(!q.arbPH||!q.flat_dataPV||!q.buf_sizeLu||q.buf_sizeLu>kMaxArchive)return Fail();
  CNL_Document* doc=nullptr;
  bool ok=cnl_document_deserialize(q.flat_dataPV,q.buf_sizeLu,&doc)==CNL_OK&&doc;
  if(doc)cnl_document_destroy(doc);
  return ok?NewBytes(in_data,q.flat_dataPV,q.buf_sizeLu,q.arbPH):Fail();}
 case PF_Arbitrary_INTERP_FUNC:{
  auto& q=ex->u.interp_func_params;
  return Copy(in_data,q.tF<0.5?q.left_arbH:q.right_arbH,q.interpPH);}
 case PF_Arbitrary_COMPARE_FUNC:{
  auto& q=ex->u.compare_func_params;
  std::vector<uint8_t> a,b;
  if(!q.compareP||!Read(in_data,q.a_arbH,a)||!Read(in_data,q.b_arbH,b))return Fail();
  *q.compareP=a==b?PF_ArbCompare_EQUAL:PF_ArbCompare_NOT_EQUAL;
  return PF_Err_NONE;}
 case PF_Arbitrary_PRINT_SIZE_FUNC:{
  auto& q=ex->u.print_size_func_params;
  if(!q.print_sizePLu)return Fail();
  std::vector<uint8_t> b;
  if(!Read(in_data,q.arbH,b))return Fail();
  *q.print_sizePLu=static_cast<A_u_long>(sizeof(kPrefix)+b.size()*2);
  return PF_Err_NONE;}
 case PF_Arbitrary_PRINT_FUNC:{
  auto& q=ex->u.print_func_params;
  std::vector<uint8_t> b;
  if(!q.print_bufferPC||!Read(in_data,q.arbH,b)||
     q.print_sizeLu<sizeof(kPrefix)+b.size()*2)return Fail();
  const char digits[]="0123456789ABCDEF";
  std::memcpy(q.print_bufferPC,kPrefix,sizeof(kPrefix)-1);
  size_t at=sizeof(kPrefix)-1;
  for(uint8_t v:b){
   q.print_bufferPC[at++]=digits[v>>4];
   q.print_bufferPC[at++]=digits[v&15];
  }
  q.print_bufferPC[at]=0;
  return PF_Err_NONE;}
 case PF_Arbitrary_SCAN_FUNC:{
  auto& q=ex->u.scan_func_params;
  if(!q.bufPC||!q.arbPH||q.bytes_to_scanLu<=sizeof(kPrefix)-1||
     q.bytes_to_scanLu>sizeof(kPrefix)+2*kMaxArchive)return Fail();
  size_t n=q.bytes_to_scanLu;
  if(q.bufPC[n-1]=='\0')--n;
  const size_t prefix=sizeof(kPrefix)-1;
  if(n<=prefix||std::memcmp(q.bufPC,kPrefix,prefix)!=0||
     (n-prefix)%2||n-prefix>2*kMaxArchive)return Fail();
  auto nibble=[](char v)->int{
   if(v>='0'&&v<='9')return v-'0';
   if(v>='A'&&v<='F')return v-'A'+10;
   if(v>='a'&&v<='f')return v-'a'+10;
   return -1;
  };
  std::vector<uint8_t> bytes((n-prefix)/2);
  for(size_t i=0;i<bytes.size();++i){
   const int hi=nibble(q.bufPC[prefix+2*i]);
   const int lo=nibble(q.bufPC[prefix+2*i+1]);
   if(hi<0||lo<0)return Fail();
   bytes[i]=static_cast<uint8_t>((hi<<4)|lo);
  }
  CNL_Document* check=nullptr;
  const bool valid=cnl_document_deserialize(bytes.data(),bytes.size(),&check)==CNL_OK&&check;
  if(check)cnl_document_destroy(check);
  return valid?NewBytes(in_data,bytes.data(),bytes.size(),q.arbPH):Fail();}
 default:return Fail();
 }
}
PF_Err Params(PF_InData* in_data,PF_OutData* out){
 PF_ParamDef def;AEFX_CLR_STRUCT(def);
 auto err=Default(in_data,&def.u.arb_d.dephault);if(err)return err;
 PF_ADD_ARBITRARY2("CNL Owned Contents",0,0,PF_ParamFlag_NONE,
    PF_PUI_NO_ECW_UI,def.u.arb_d.dephault,1,nullptr);
 AEFX_CLR_STRUCT(def);PF_ADD_SLIDER("Stroke Width",1,35,1,35,5,2);
 AEFX_CLR_STRUCT(def);PF_ADD_COLOR("Stroke Color",76,228,255,3);
 AEFX_CLR_STRUCT(def);PF_ADD_CHECKBOX("Transparent Input","Draw over transparency",TRUE,0,4);
 out->num_params=kCount;return PF_Err_NONE;
}
bool Collect(CNL_Document* doc,std::vector<CNL_VectorCubicV1>& curves){
 std::vector<CNL_NodeId> stack{cnl_document_root(doc)};
 unsigned nodes=0;
 while(!stack.empty()){
  if(++nodes>16384)return false;
  CNL_NodeId id=stack.back();stack.pop_back();
  CNL_NodeKind kind{};
  if(cnl_document_get_kind(doc,id,&kind)!=CNL_OK)return false;
  if(kind==CNL_NODE_GROUP){
   uint32_t n=0;
   if(cnl_document_get_child_count(doc,id,&n)!=CNL_OK||n>8192)return false;
   for(uint32_t k=n;k>0;--k){
    CNL_NodeId child=0;
    if(cnl_document_get_child(doc,id,k-1,&child)!=CNL_OK)return false;
    stack.push_back(child);
   }
  }else if(kind==CNL_NODE_PATH){
   uint32_t n=0;
   if(cnl_document_copy_cubics(doc,id,nullptr,&n)!=CNL_NO_SPACE||
       n==0||n>4096||curves.size()+n>4096)return false;
   std::vector<CNL_CubicBezier> cubics(n);
   if(cnl_document_copy_cubics(doc,id,cubics.data(),&n)!=CNL_OK)return false;
   for(auto& c:cubics)curves.push_back({c.x0,c.y0,c.x1,c.y1,c.x2,c.y2,c.x3,c.y3});
  }else return false;
 }
 return !curves.empty();
}
PF_Err Render(PF_InData* in_data,PF_ParamDef* params[],PF_LayerDef* out){
 if(!params||!out||!out->data)return Fail();
 std::vector<uint8_t> bytes;
 if(!Read(in_data,params[kDoc]->u.arb_d.value,bytes))return Fail();
 CNL_Document* doc=nullptr;
 if(cnl_document_deserialize(bytes.data(),bytes.size(),&doc)!=CNL_OK||!doc)return Fail();
 std::vector<CNL_VectorCubicV1> cubics;bool good=Collect(doc,cubics);
 cnl_document_destroy(doc);if(!good)return Fail();
 bool clear=params[kClear]->u.bd.value!=FALSE;
 if(!clear && PF_COPY(&params[kInput]->u.ld,out,nullptr,nullptr))return Fail();
 cnlvec::Config cfg{};cfg.copies=1;cfg.orbit=0;cfg.scale=1;
 cfg.rotation=0;cfg.clearInput=clear;
 cfg.stroke=std::clamp(double(params[kStroke]->u.sd.value),1.0,35.0);
 cfg.color={params[kColor]->u.cd.value.red,params[kColor]->u.cd.value.green,
            params[kColor]->u.cd.value.blue};
 return cnlvec::Draw(cubics.data(),static_cast<uint32_t>(cubics.size()),
   reinterpret_cast<cnlvec::Pixel8*>(out->data),out->rowbytes,
   out->width,out->height,cfg)?PF_Err_NONE:Fail();
}
}
extern "C" DllExport PF_Err PluginDataEntryFunction2(PF_PluginDataPtr p,
 PF_PluginDataCB2 cb,SPBasicSuite*,const char*,const char*){
 PF_Err result=PF_Err_INVALID_CALLBACK;
 result=PF_REGISTER_EFFECT_EXT2(p,cb,"CNL Owned Vector Document (Research)",
   "CNL Owned Vector Document","CNL Research",AE_RESERVED_INFO,"EffectMain",
   "https://github.com/ken-eizo/after-effects-internals-guide");
 return result;
}
extern "C" DllExport PF_Err EffectMain(PF_Cmd cmd,PF_InData* in_data,
 PF_OutData* out,PF_ParamDef* params[],PF_LayerDef* dst,void* extra){
 if(!in_data||!out)return Fail();
 try {
  switch(cmd){
   case PF_Cmd_ABOUT:
    PF_SPRINTF(out->return_msg,"CNL Owned Vector: effect-owned serialized cubic "
      "Bezier document. No Shape/Mask. NOT native Pen or BEE_VectorArt.");
    return PF_Err_NONE;
   case PF_Cmd_GLOBAL_SETUP:
    out->my_version=PF_VERSION(1,0,0,PF_Stage_DEVELOP,2);
    out->out_flags=PF_OutFlag_NON_PARAM_VARY;
    out->out_flags2=PF_OutFlag2_SUPPORTS_THREADED_RENDERING;
    return PF_Err_NONE;
   case PF_Cmd_PARAMS_SETUP:return Params(in_data,out);
   case PF_Cmd_ARBITRARY_CALLBACK:return Arb(in_data,static_cast<PF_ArbParamsExtra*>(extra));
   case PF_Cmd_RENDER:return Render(in_data,params,dst);
   default:return PF_Err_NONE;
  }
 }catch(...){return Fail();}
}
