// End-to-end OFFLINE AE effect ABI test. NEVER launch After Effects.
// Validates host-owned arbitrary handles, archive persistence and rendering.
#define NOMINMAX
#include <windows.h>
#include "AEConfig.h"
#include "entry.h"
#include "AE_Effect.h"
#include "AE_EffectCB.h"
#include "AE_Macros.h"
#include "CNLNativeVectorCore.h"
#include <cstdio>
#include <cstdarg>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <array>
#include <map>
#include <algorithm>
#include <stdint.h>
namespace {
using Main=PF_Err (*)(PF_Cmd,PF_InData*,PF_OutData*,PF_ParamDef**,PF_LayerDef*,void*);
std::map<PF_Handle,size_t> allocations;
PF_ParamDef captured[5]{};
int nparam=1;
[[noreturn]] void fail(const char* s){std::fprintf(stderr,"FAIL %s\n",s);std::exit(5);}
void check(bool b,const char* s){if(!b)fail(s);}
PF_Handle HostNew(A_HandleSize size){
 if(size<=0||size>2*1024*1024)return nullptr;
 auto pp=static_cast<PF_Handle>(std::malloc(sizeof(void*)));
 if(!pp)return nullptr;
 *pp=std::malloc(static_cast<size_t>(size));
 if(!*pp){std::free(pp);return nullptr;}
 allocations[pp]=static_cast<size_t>(size);
 return pp;
}
void HostDispose(PF_Handle p){
 if(!p)return;
 auto it=allocations.find(p);
 if(it==allocations.end())fail("unknown or double disposed handle");
 std::free(*p);std::free(p);allocations.erase(it);
}
void* HostLock(PF_Handle p){return allocations.count(p)?*p:nullptr;}
void HostUnlock(PF_Handle){}
A_HandleSize HostSize(PF_Handle p){return allocations.count(p)?static_cast<A_HandleSize>(allocations.at(p)):0;}
PF_Err AddParam(PF_ProgPtr,PF_ParamIndex index,PF_ParamDef* def){
 if(index!=-1||!def||nparam>=5)fail("bad AddParam");
 captured[nparam++]=*def;return PF_Err_NONE;
}
PF_Err CopyWorld(PF_ProgPtr,PF_EffectWorld* src,PF_EffectWorld* dst,
                  PF_Rect*,PF_Rect*){
 if(!src||!dst||!src->data||!dst->data)return PF_Err_BAD_CALLBACK_PARAM;
 for(int y=0;y<std::min(int(src->height),int(dst->height));++y)
  std::memcpy(reinterpret_cast<char*>(dst->data)+y*dst->rowbytes,
              reinterpret_cast<const char*>(src->data)+y*src->rowbytes,
              static_cast<size_t>(std::min(int(src->width),int(dst->width)))*4);
 return PF_Err_NONE;
}
int Format(char* dst,const char* fmt,...){
 va_list a;va_start(a,fmt);int n=std::vsnprintf(dst,255,fmt,a);va_end(a);return n;
}
uint64_t digest(const std::vector<PF_Pixel8>& img){
 uint64_t h=1469598103934665603ull;
 for(auto& x:img)
  for(uint8_t c:{x.alpha,x.red,x.green,x.blue}){h^=c;h*=1099511628211ull;}
 return h;
}
}
int main(int argc,char** argv){
 if(argc!=2)fail("usage: OwnedVectorHostMock.exe CNLOwnedVectorEffect.aex");
 HMODULE h=LoadLibraryA(argv[1]);check(h!=nullptr,"AEX load failed");
 auto main=reinterpret_cast<Main>(GetProcAddress(h,"EffectMain"));
 check(main!=nullptr,"EffectMain symbol missing");
 PF_UtilCallbacks utils{};
 utils.host_new_handle=HostNew;utils.host_dispose_handle=HostDispose;
 utils.host_lock_handle=HostLock;utils.host_unlock_handle=HostUnlock;
 utils.host_get_handle_size=HostSize;
 utils.copy=CopyWorld;utils.ansi.sprintf=Format;
 PF_InData in_data{};PF_OutData out{};
 in_data.utils=&utils;in_data.inter.add_param=AddParam;
 PF_ParamDef* ps[5]{};
 check(main(PF_Cmd_GLOBAL_SETUP,&in_data,&out,ps,nullptr,nullptr)==0,"Global Setup");
 check(main(PF_Cmd_PARAMS_SETUP,&in_data,&out,ps,nullptr,nullptr)==0,"Params Setup");
 check(nparam==5&&out.num_params==5,"unexpected parameter registration");
 check(captured[1].param_type==PF_Param_ARBITRARY_DATA,"host-owned arbitrary parameter missing");
 check(captured[1].u.arb_d.dephault!=nullptr,"default archive unallocated");
 auto invoke=[&](PF_ArbParamsExtra& e){e.id=1;return main(PF_Cmd_ARBITRARY_CALLBACK,
            &in_data,&out,ps,nullptr,&e);};
 PF_ArbParamsExtra e{};
 PF_ArbitraryH original=captured[1].u.arb_d.dephault;
 e.which_function=PF_Arbitrary_COPY_FUNC;
 PF_ArbitraryH copied=nullptr;
 e.u.copy_func_params.src_arbH=original;
 e.u.copy_func_params.dst_arbPH=&copied;
 check(invoke(e)==0&&copied&&copied!=original,"COPY deep handle");
 PF_ArbCompareResult cmp=PF_ArbCompare_NOT_EQUAL;
 e={};e.which_function=PF_Arbitrary_COMPARE_FUNC;
 e.u.compare_func_params.a_arbH=original;e.u.compare_func_params.b_arbH=copied;
 e.u.compare_func_params.compareP=&cmp;
 check(invoke(e)==0&&cmp==PF_ArbCompare_EQUAL,"COMPARE equality");
 A_u_long size=0;
 e={};e.which_function=PF_Arbitrary_FLAT_SIZE_FUNC;
 e.u.flat_size_func_params.arbH=original;
 e.u.flat_size_func_params.flat_data_sizePLu=&size;
 check(invoke(e)==0&&size>32&&size<10000,"FLAT_SIZE");
 std::vector<uint8_t> flat(size);
 e={};e.which_function=PF_Arbitrary_FLATTEN_FUNC;
 e.u.flatten_func_params.arbH=original;
 e.u.flatten_func_params.buf_sizeLu=size;
 e.u.flatten_func_params.flat_dataPV=flat.data();
 check(invoke(e)==0,"FLATTEN");
 PF_ArbitraryH roundtrip=nullptr;
 e={};e.which_function=PF_Arbitrary_UNFLATTEN_FUNC;
 e.u.unflatten_func_params.flat_dataPV=flat.data();
 e.u.unflatten_func_params.buf_sizeLu=size;
 e.u.unflatten_func_params.arbPH=&roundtrip;
 check(invoke(e)==0&&roundtrip,"UNFLATTEN");
 e={};e.which_function=PF_Arbitrary_COMPARE_FUNC;
 e.u.compare_func_params.a_arbH=original;
 e.u.compare_func_params.b_arbH=roundtrip;
 e.u.compare_func_params.compareP=&cmp;
 check(invoke(e)==0&&cmp==PF_ArbCompare_EQUAL,"roundtrip matches exact bytes");
 PF_ArbitraryH corrupt=nullptr;
 flat.back()^=0x77;
 e={};e.which_function=PF_Arbitrary_UNFLATTEN_FUNC;
 e.u.unflatten_func_params.flat_dataPV=flat.data();
 e.u.unflatten_func_params.buf_sizeLu=size;
 e.u.unflatten_func_params.arbPH=&corrupt;
 check(invoke(e)!=0&&!corrupt,"reject corrupted archive");
 flat.back()^=0x77;
 e={};e.which_function=PF_Arbitrary_UNFLATTEN_FUNC;
 e.u.unflatten_func_params.flat_dataPV=flat.data();
 e.u.unflatten_func_params.buf_sizeLu=size-1;
 e.u.unflatten_func_params.arbPH=&corrupt;
 check(invoke(e)!=0&&!corrupt,"reject truncated archive");
 // Produce genuinely different nested native CNL Contents in the compiled AEX,
 // then pass its serialised archive back through AE Arbitrary UNFLATTEN.
 auto makeDoc=reinterpret_cast<decltype(&cnl_document_create)>(GetProcAddress(h,"cnl_document_create"));
 auto rootDoc=reinterpret_cast<decltype(&cnl_document_root)>(GetProcAddress(h,"cnl_document_root"));
 auto addGroup=reinterpret_cast<decltype(&cnl_document_add_group)>(GetProcAddress(h,"cnl_document_add_group"));
 auto addEllipse=reinterpret_cast<decltype(&cnl_document_add_ellipse)>(GetProcAddress(h,"cnl_document_add_ellipse"));
 auto serialize=reinterpret_cast<decltype(&cnl_document_serialize)>(GetProcAddress(h,"cnl_document_serialize"));
 auto destroyDoc=reinterpret_cast<decltype(&cnl_document_destroy)>(GetProcAddress(h,"cnl_document_destroy"));
 check(makeDoc&&rootDoc&&addGroup&&addEllipse&&serialize&&destroyDoc,
       "native document API exports missing");
 auto doc=makeDoc();check(doc!=nullptr,"new independent native CNL document");
 CNL_NodeId parent=0,nested=0,path1=0,path2=0;
 check(addGroup(doc,rootDoc(doc),"Independent Contents",&parent)==CNL_OK &&
       addGroup(doc,parent,"Nested Group",&nested)==CNL_OK &&
       addEllipse(doc,nested,"Ellipse Left",-102,46,78,155,&path1)==CNL_OK &&
       addEllipse(doc,parent,"Ellipse Right",110,-68,55,38,&path2)==CNL_OK,
       "independent CNL nested geometry construction");
 size_t mlen=0;
 check(serialize(doc,nullptr,&mlen)==CNL_NO_SPACE&&mlen>size,
       "new nested archive must be longer");
 std::vector<uint8_t> modifiedBytes(mlen);
 check(serialize(doc,modifiedBytes.data(),&mlen)==CNL_OK,
       "serialize modified independent document");
 destroyDoc(doc);
 PF_ArbitraryH modified=nullptr;
 e={};e.which_function=PF_Arbitrary_UNFLATTEN_FUNC;
 e.u.unflatten_func_params.flat_dataPV=modifiedBytes.data();
 e.u.unflatten_func_params.buf_sizeLu=static_cast<A_u_long>(mlen);
 e.u.unflatten_func_params.arbPH=&modified;
 check(invoke(e)==0&&modified,"modified Contents UNFLATTEN");
 e={};e.which_function=PF_Arbitrary_COMPARE_FUNC;
 e.u.compare_func_params.a_arbH=original;
 e.u.compare_func_params.b_arbH=modified;
 e.u.compare_func_params.compareP=&cmp;
 check(invoke(e)==0&&cmp!=PF_ArbCompare_EQUAL,
       "different hierarchy must not compare equal");
 e={};e.which_function=PF_Arbitrary_NEW_FUNC;
 PF_ArbitraryH fresh=nullptr;e.u.new_func_params.arbPH=&fresh;
 check(invoke(e)==0&&fresh,"NEW");
 e={};e.which_function=PF_Arbitrary_INTERP_FUNC;
 PF_ArbitraryH interp=nullptr;
 e.u.interp_func_params.left_arbH=copied;e.u.interp_func_params.right_arbH=roundtrip;
 e.u.interp_func_params.tF=0.7;
 e.u.interp_func_params.interpPH=&interp;
 check(invoke(e)==0&&interp,"INTERP step-copy");
 e={};e.which_function=PF_Arbitrary_PRINT_SIZE_FUNC;
 A_u_long printn=0;e.u.print_size_func_params.print_sizePLu=&printn;
 e.u.print_size_func_params.arbH=original;
 check(invoke(e)==0&&printn>size*2&&printn<2*size+64,"PRINT_SIZE");
 std::vector<char> text(printn);
 e={};e.which_function=PF_Arbitrary_PRINT_FUNC;
 e.u.print_func_params.arbH=original;
 e.u.print_func_params.print_sizeLu=printn;
 e.u.print_func_params.print_bufferPC=text.data();
 check(invoke(e)==0&&std::strstr(text.data(),"CNLVEC1:")==text.data(),"PRINT");
 PF_ArbitraryH fromText=nullptr;
 e={};e.which_function=PF_Arbitrary_SCAN_FUNC;
 e.u.scan_func_params.bufPC=text.data();
 e.u.scan_func_params.bytes_to_scanLu=printn;
 e.u.scan_func_params.arbPH=&fromText;
 check(invoke(e)==0&&fromText,"reversible SCAN");
 e={};e.which_function=PF_Arbitrary_COMPARE_FUNC;
 e.u.compare_func_params.a_arbH=original;
 e.u.compare_func_params.b_arbH=fromText;
 e.u.compare_func_params.compareP=&cmp;
 check(invoke(e)==0&&cmp==PF_ArbCompare_EQUAL,"PRINT/SCAN byte-identical");
 text[9]='Z';
 PF_ArbitraryH invalidText=nullptr;
 e={};e.which_function=PF_Arbitrary_SCAN_FUNC;
 e.u.scan_func_params.bufPC=text.data();
 e.u.scan_func_params.bytes_to_scanLu=printn;
 e.u.scan_func_params.arbPH=&invalidText;
 check(invoke(e)!=0&&!invalidText,"malformed PRINT/SCAN rejected");
 constexpr int W=640,H=480;
 std::vector<PF_Pixel8> src(size_t(W)*H),dst(size_t(W)*H);
 for(auto& px:src){px.alpha=255;px.red=11;px.green=17;px.blue=29;}
 PF_ParamDef input{};input.param_type=PF_Param_LAYER;
 input.u.ld.width=W;input.u.ld.height=H;input.u.ld.rowbytes=W*4;input.u.ld.data=src.data();
 ps[0]=&input;for(int i=1;i<5;++i)ps[i]=&captured[i];
 captured[1].u.arb_d.value=roundtrip;
 PF_LayerDef world{};
 world.width=W;world.height=H;world.rowbytes=W*4;world.data=dst.data();
 check(main(PF_Cmd_RENDER,&in_data,&out,ps,&world,nullptr)==0,"render archive path");
 auto first=digest(dst);
 int visible=std::count_if(dst.begin(),dst.end(),[](const PF_Pixel8& a){return a.alpha>0;});
 check(visible>300&&visible<W*H/2,"vector alpha coverage");
 captured[1].u.arb_d.value=modified;
 check(main(PF_Cmd_RENDER,&in_data,&out,ps,&world,nullptr)==0,
       "render deeply nested host-owned Contents");
 auto nestedHash=digest(dst);
 check(first!=nestedHash,"independent geometry changes raster, not just metadata");
 captured[1].u.arb_d.value=roundtrip;
 captured[2].u.sd.value=14;
 check(main(PF_Cmd_RENDER,&in_data,&out,ps,&world,nullptr)==0,"render changed stroke");
 auto thick=digest(dst);
 check(first!=thick,"stroke slider affects final raster");
 captured[2].u.sd.value=5;captured[4].u.bd.value=FALSE;
 check(main(PF_Cmd_RENDER,&in_data,&out,ps,&world,nullptr)==0,"render preserve input");
 check(dst[0].alpha==255&&dst[0].blue==29,"underlying source maintained");
 for(auto hnd:{copied,roundtrip,modified,fresh,interp,fromText,original}){
  e={};e.which_function=PF_Arbitrary_DISPOSE_FUNC;
  e.u.dispose_func_params.arbH=hnd;
  check(invoke(e)==0,"dispose");
 }
 check(allocations.empty(),"no leaked arb handles");
 std::printf("PASS AE effect-owned archive lifecycle: Params=5 bytes=%u "
  "rendered=%d framehash=%llu strokehash=%llu "
  "copy/flatten/unflatten/corrupt/compare/interp/print-scan/dispose clean\n",
  size,visible,(unsigned long long)first,(unsigned long long)thick);
 return 0;
}
