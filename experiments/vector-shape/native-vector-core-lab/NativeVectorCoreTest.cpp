#include "CNLNativeVectorCore.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include <memory>
#include <algorithm>
#include <limits>
#include <string>
#define CHECK(x) do{auto&& _res=(x);if(!static_cast<bool>(_res)){\
 std::fprintf(stderr,"FAIL %s @%d\n",#x,__LINE__);return 2;}}while(false)
struct DocDeleter{void operator()(CNL_Document* d)const{cnl_document_destroy(d);}};
using Doc=std::unique_ptr<CNL_Document,DocDeleter>;
static uint64_t hash(const uint8_t* p,size_t n){
 uint64_t v=1469598103934665603ULL;
 for(size_t i=0;i<n;++i){v^=p[i];v*=1099511628211ULL;}return v;
}
static void update_u64(std::vector<uint8_t>& x,size_t pos,uint64_t v){
 for(int i=0;i<8;++i)x[pos+i]=uint8_t(v>>(8*i));
}
int main(){
 CHECK(cnl_core_version().abi_version==1);
 CHECK(cnl_core_version().archive_version==1);
 Doc d(cnl_document_create());CHECK(d);
 const CNL_NodeId root=cnl_document_root(d.get());CHECK(root==1);
 CNL_NodeId group=0,group2=0,path=0;
 CHECK(cnl_document_add_group(d.get(),root,"Procedural Geometry",&group)==CNL_OK);
 CHECK(cnl_document_add_group(d.get(),group,"LFO Generator",&group2)==CNL_OK);
 CNL_PathVertex four[4]={
 {0,0,-5,0,0,-5},{50,0,-5,0,5,0},{50,50,0,-5,0,5},{0,50,5,0,-5,0}
 };
 CHECK(cnl_document_add_path(d.get(),group2,"Editable Path",1,four,4,&path)==CNL_OK);
 CHECK(path==4);
 CNL_NodeKind type{};
 CHECK(cnl_document_get_kind(d.get(),path,&type)==CNL_OK&&type==CNL_NODE_PATH);
 CHECK(cnl_document_get_kind(d.get(),root,&type)==CNL_OK&&type==CNL_NODE_GROUP);
 uint32_t kids=0;CNL_NodeId child=0,parent=0;
 CHECK(cnl_document_get_child_count(d.get(),group2,&kids)==CNL_OK&&kids==1);
 CHECK(cnl_document_get_child(d.get(),group2,0,&child)==CNL_OK&&child==path);
 CHECK(cnl_document_get_parent(d.get(),path,&parent)==CNL_OK&&parent==group2);
 CHECK(cnl_document_move_node(d.get(),group,group2)==CNL_CYCLE);
 CHECK(cnl_document_move_node(d.get(),root,group2)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_document_move_node(d.get(),path,path)==CNL_WRONG_TYPE);
 CHECK(cnl_document_move_node(d.get(),path,group)==CNL_OK);
 CHECK(cnl_document_get_child_count(d.get(),group2,&kids)==CNL_OK&&kids==0);
 CHECK(cnl_document_get_child_count(d.get(),group,&kids)==CNL_OK&&kids==2);
 CHECK(cnl_document_move_node(d.get(),path,group2)==CNL_OK);
 CHECK(cnl_document_get_child_count(d.get(),group2,&kids)==CNL_OK&&kids==1);
 int closed=0;uint32_t nv=0;
 CHECK(cnl_document_get_path_info(d.get(),path,&closed,&nv)==CNL_OK&&closed==1&&nv==4);
 CNL_PathVertex v{};
 CHECK(cnl_document_get_vertex(d.get(),path,3,&v)==CNL_OK&&v.x==0&&v.y==50);
 size_t namelen=0;
 CHECK(cnl_document_get_name(d.get(),path,nullptr,&namelen)==CNL_NO_SPACE);
 CHECK(namelen==std::strlen("Editable Path")+1);
 std::vector<char> name(namelen);
 CHECK(cnl_document_get_name(d.get(),path,name.data(),&namelen)==CNL_OK);
 CHECK(std::string(name.data())=="Editable Path");
 CHECK(cnl_document_get_vertex(d.get(),root,0,&v)==CNL_WRONG_TYPE);
 CHECK(cnl_document_get_child_count(d.get(),path,&kids)==CNL_WRONG_TYPE);
 CHECK(cnl_document_get_vertex(d.get(),path,999,&v)==CNL_OUT_OF_RANGE);
 CHECK(cnl_document_add_group(d.get(),999,"invalid parent",&child)==CNL_NOT_FOUND);
 CHECK(cnl_document_add_group(d.get(),path,"invalid parent",&child)==CNL_WRONG_TYPE);
 CNL_PathVertex invalid=four[0];
 invalid.x=std::numeric_limits<double>::quiet_NaN();
 CHECK(cnl_document_set_vertex(d.get(),path,0,&invalid)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_document_add_path(d.get(),root,"NaN",0,&invalid,2,&child)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_document_add_path(d.get(),root,"TooFew",1,four,2,&child)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_document_set_vertex(d.get(),path,1,&four[0])==CNL_OK);
 CHECK(cnl_document_set_vertex(d.get(),path,1,&four[1])==CNL_OK);
 size_t required=0;
 CHECK(cnl_document_serialize(d.get(),nullptr,&required)==CNL_NO_SPACE);
 CHECK(required>200&&required<4096);
 std::vector<uint8_t> binary(required,0xcd);
 size_t small=required-1;
 CHECK(cnl_document_serialize(d.get(),binary.data(),&small)==CNL_NO_SPACE);
 CHECK(small==required&&binary[0]==0xcd); // no writes on insufficient space
 size_t size=required;
 CHECK(cnl_document_serialize(d.get(),binary.data(),&size)==CNL_OK&&size==required);
 CHECK(std::memcmp(binary.data(),"CNLVEC01",8)==0);
 std::vector<uint8_t> again(required);
 CHECK(cnl_document_serialize(d.get(),again.data(),&size)==CNL_OK);
 CHECK(binary==again);  // stable deterministic serialization

 CNL_Document* raw=nullptr;
 CHECK(cnl_document_deserialize(binary.data(),binary.size(),&raw)==CNL_OK&&raw);
 Doc loaded(raw);
 CHECK(cnl_document_get_child_count(loaded.get(),root,&kids)==CNL_OK&&kids==1);
 CHECK(cnl_document_get_child_count(loaded.get(),group2,&kids)==CNL_OK&&kids==1);
 CHECK(cnl_document_get_vertex(loaded.get(),path,3,&v)==CNL_OK&&v.y==50);
 size_t loadedbytes=0;
 CHECK(cnl_document_serialize(loaded.get(),nullptr,&loadedbytes)==CNL_NO_SPACE);
 CHECK(loadedbytes==binary.size());
 std::vector<uint8_t> restored(loadedbytes);
 CHECK(cnl_document_serialize(loaded.get(),restored.data(),&loadedbytes)==CNL_OK);
 CHECK(restored==binary);

 Doc cloned(nullptr);
 CHECK(cnl_document_clone(d.get(),&raw)==CNL_OK&&raw);
 cloned.reset(raw);
 v.x=260;v.out_dx=125;
 CHECK(cnl_document_set_vertex(cloned.get(),path,0,&v)==CNL_OK);
 CNL_PathVertex original{};
 CHECK(cnl_document_get_vertex(d.get(),path,0,&original)==CNL_OK&&original.x==0);
 CHECK(cnl_document_get_vertex(cloned.get(),path,0,&original)==CNL_OK&&original.x==260);

 auto corrupt=binary;corrupt[corrupt.size()-11]^=4;
 CHECK(cnl_document_deserialize(corrupt.data(),corrupt.size(),&raw)==CNL_BAD_ARCHIVE);
 corrupt=binary;corrupt[8]=2;
 update_u64(corrupt,corrupt.size()-8,hash(corrupt.data(),corrupt.size()-8));
 CHECK(cnl_document_deserialize(corrupt.data(),corrupt.size(),&raw)==CNL_UNSUPPORTED_ARCHIVE_VERSION);
 corrupt=binary;corrupt[12]=0;corrupt[13]=0;corrupt[14]=0;corrupt[15]=0;
 update_u64(corrupt,corrupt.size()-8,hash(corrupt.data(),corrupt.size()-8));
 CHECK(cnl_document_deserialize(corrupt.data(),corrupt.size(),&raw)==CNL_BAD_ARCHIVE);
 corrupt=binary;corrupt[40]=0; // root id = 1 at offset 28, 40 = parent field
 corrupt[28]=2;  // corrupt root node id
 update_u64(corrupt,corrupt.size()-8,hash(corrupt.data(),corrupt.size()-8));
 CHECK(cnl_document_deserialize(corrupt.data(),corrupt.size(),&raw)==CNL_BAD_ARCHIVE);
 CHECK(cnl_document_deserialize(binary.data(),binary.size()-1,&raw)==CNL_BAD_ARCHIVE);
 CHECK(cnl_document_deserialize(nullptr,0,&raw)==CNL_INVALID_ARGUMENT);
 // Exact cubic output is a vector value: no pixels, mask or AE Shape involved.
 uint32_t n_cubics=0;
 CHECK(cnl_document_copy_cubics(d.get(),path,nullptr,&n_cubics)==CNL_NO_SPACE);
 CHECK(n_cubics==4);
 CNL_CubicBezier cubics[4]{};
 CHECK(cnl_document_copy_cubics(d.get(),path,cubics,&n_cubics)==CNL_OK);
 CHECK(cubics[0].x0==four[0].x&&cubics[0].y0==four[0].y);
 CHECK(cubics[0].x1==four[0].x+four[0].out_dx);
 CHECK(cubics[0].y1==four[0].y+four[0].out_dy);
 CHECK(cubics[0].x2==four[1].x+four[1].in_dx);
 CHECK(cubics[0].y2==four[1].y+four[1].in_dy);
 CHECK(cubics[0].x3==four[1].x&&cubics[0].y3==four[1].y);
 CHECK(cubics[3].x3==four[0].x&&cubics[3].y3==four[0].y);
 CNL_NodeId ellipse=0;
 CHECK(cnl_document_add_ellipse(d.get(),root,"CNL procedural ellipse",
                 200,100,75,45,&ellipse)==CNL_OK);
 CHECK(cnl_document_add_ellipse(d.get(),root,"invalid",-1,0,-75,10,&child)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_document_copy_cubics(d.get(),ellipse,nullptr,&n_cubics)==CNL_NO_SPACE&&n_cubics==4);
 CHECK(cnl_document_copy_cubics(d.get(),ellipse,cubics,&n_cubics)==CNL_OK);
 CHECK(std::abs(cubics[0].x0-275)<1e-12&&std::abs(cubics[0].y0-100)<1e-12);
 CHECK(std::abs(cubics[0].y1-100-45*0.5522847498307936)<1e-10);
 CHECK(std::abs(cubics[0].x2-200-75*0.5522847498307936)<1e-10);
 CHECK(std::abs(cubics[0].x3-200)<1e-12);
 // Test documents with multiple nested paths, stable identity and differing handles.
 for(int i=0;i<75;++i){
  char title[32];std::snprintf(title,sizeof(title),"Generated_%03d",i);
  CNL_PathVertex shape[4];std::memcpy(shape,four,sizeof(shape));shape[0].x=double(i);
  CHECK(cnl_document_add_path(d.get(),group,title,(i%2),shape,4,&child)==CNL_OK);
 }
 CHECK(cnl_document_get_child_count(d.get(),group,&kids)==CNL_OK&&kids==76);
 size_t many=0;CHECK(cnl_document_serialize(d.get(),nullptr,&many)==CNL_NO_SPACE);
 std::vector<uint8_t> manyblob(many);
 CHECK(cnl_document_serialize(d.get(),manyblob.data(),&many)==CNL_OK);
 CHECK(cnl_document_deserialize(manyblob.data(),manyblob.size(),&raw)==CNL_OK);
 Doc loadedmany(raw);
 CHECK(cnl_document_get_child_count(loadedmany.get(),group,&kids)==CNL_OK&&kids==76);
 CNL_NodeId created=0;
 CHECK(cnl_document_add_group(loadedmany.get(),root,"New",&created)==CNL_OK&&created>path);
 // A very deep native Contents hierarchy must serialize without C++ recursion.
 Doc deep(cnl_document_create());CHECK(deep);
 CNL_NodeId cursor=cnl_document_root(deep.get()),next=0;
 for(int i=0;i<2048;++i){
  CHECK(cnl_document_add_group(deep.get(),cursor,"deep-group",&next)==CNL_OK);
  cursor=next;
 }
 size_t depth_size=0;
 CHECK(cnl_document_serialize(deep.get(),nullptr,&depth_size)==CNL_NO_SPACE);
 std::vector<uint8_t> depth_archive(depth_size);
 CHECK(cnl_document_serialize(deep.get(),depth_archive.data(),&depth_size)==CNL_OK);
 CHECK(cnl_document_deserialize(depth_archive.data(),depth_archive.size(),&raw)==CNL_OK);
 Doc depth_restored(raw);
 CHECK(cnl_document_get_parent(depth_restored.get(),cursor,&parent)==CNL_OK&&parent!=0);
 std::printf("PASS NativeVectorCore REAL compiled DLL: stable indexed Contents tree, C ABI, "
 "Bezier handles, move, cycle protection, clone isolation, checksummed deterministic "
 "roundtrip, version/corrupt rejection, 75 procedural paths; root=%llu "
 "path=%llu initial_archive_bytes=%zu large_archive_bytes=%zu\n",
 (unsigned long long)root,(unsigned long long)path,required,many);
 return 0;
}
