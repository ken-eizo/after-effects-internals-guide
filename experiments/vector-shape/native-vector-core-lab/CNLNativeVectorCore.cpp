#include "CNLNativeVectorCore.h"
#include <map>
#include <vector>
#include <string>
#include <memory>
#include <cstring>
#include <cstdint>
#include <cmath>
#include <algorithm>
#include <limits>
#include <new>

namespace {
constexpr uint32_t kMaxNodes=100000, kMaxVertices=100000, kMaxName=1024;
constexpr size_t kMaxBlob=64u*1024u*1024u;
constexpr uint64_t kFNVOffset=1469598103934665603ULL;
constexpr uint64_t kFNVPrime=1099511628211ULL;
constexpr char kMagic[8]={'C','N','L','V','E','C','0','1'};
struct Node {
 uint64_t id=0,parent=0;
 CNL_NodeKind kind=CNL_NODE_GROUP;
 bool closed=false;
 std::string name;
 std::vector<uint64_t> children;
 std::vector<CNL_PathVertex> vertices;
};
bool valid(const CNL_PathVertex& v) {
 const double a[]={v.x,v.y,v.in_dx,v.in_dy,v.out_dx,v.out_dy};
 for(double x:a)if(!std::isfinite(x))return false;
 return true;
}
bool valid_name(const char* s){
 if(!s)return false;
 size_t n=0;
 while(n<=kMaxName && s[n])++n;
 return n<=kMaxName;
}
uint64_t fnv(const uint8_t* p,size_t n) {
 uint64_t x=kFNVOffset;
 for(size_t i=0;i<n;++i){x^=p[i];x*=kFNVPrime;}
 return x;
}
struct Writer {
 std::vector<uint8_t> b;
 void u8(uint8_t x){b.push_back(x);}
 void u16(uint16_t x){for(int i=0;i<2;++i)u8(uint8_t(x>>(i*8)));}
 void u32(uint32_t x){for(int i=0;i<4;++i)u8(uint8_t(x>>(i*8)));}
 void u64(uint64_t x){for(int i=0;i<8;++i)u8(uint8_t(x>>(i*8)));}
 void f64(double x){uint64_t y;std::memcpy(&y,&x,8);u64(y);}
 void text(const std::string& s){b.insert(b.end(),s.begin(),s.end());}
};
struct Reader {
 const uint8_t* p;size_t n,pos=0;
 bool bytes(uint8_t* out,size_t k){
  if(pos>n||k>n-pos)return false;
  if(out)std::memcpy(out,p+pos,k);
  pos+=k;return true;
 }
 bool u8(uint8_t& v){return bytes(&v,1);}
 bool u16(uint16_t& v){uint8_t b[2];if(!bytes(b,2))return false;v=b[0]|uint16_t(b[1])<<8;return true;}
 bool u32(uint32_t& v){uint8_t b[4];if(!bytes(b,4))return false;v=0;for(int i=0;i<4;++i)v|=uint32_t(b[i])<<(8*i);return true;}
 bool u64(uint64_t& v){uint8_t b[8];if(!bytes(b,8))return false;v=0;for(int i=0;i<8;++i)v|=uint64_t(b[i])<<(8*i);return true;}
 bool f64(double& v){uint64_t x;if(!u64(x))return false;std::memcpy(&v,&x,8);return std::isfinite(v);}
};
} // namespace

struct CNL_Document {
 std::map<CNL_NodeId,Node> nodes;
 uint64_t next_id=2;
 CNL_Document(){
  Node root;root.id=1;root.name="Contents";nodes.emplace(1,std::move(root));
 }
};

namespace {
CNL_Status attach(CNL_Document* doc,CNL_NodeId parent,Node&& child,CNL_NodeId* out){
 if(!doc||!out)return CNL_INVALID_ARGUMENT;
 auto p=doc->nodes.find(parent);
 if(p==doc->nodes.end())return CNL_NOT_FOUND;
 if(p->second.kind!=CNL_NODE_GROUP)return CNL_WRONG_TYPE;
 if(doc->nodes.size()>=kMaxNodes||doc->next_id==0||doc->next_id==UINT64_MAX)
  return CNL_LIMIT_EXCEEDED;
 const uint64_t id=doc->next_id;
 child.id=id;child.parent=parent;
 p->second.children.reserve(p->second.children.size()+1);
 doc->nodes.emplace(id,std::move(child));
 p->second.children.push_back(id);
 doc->next_id=id+1;*out=id;return CNL_OK;
}
void write_node(const CNL_Document& doc,const Node& root,Writer& w) {
 // Iterative preorder: no stack overflow for deeply nested vector groups.
 std::vector<const Node*> pending{&root};
 while(!pending.empty()){
  const Node* node=pending.back();pending.pop_back();
  w.u64(node->id);w.u64(node->parent);
  w.u8(uint8_t(node->kind));w.u8(node->closed?1:0);w.u16(0);
  w.u32(uint32_t(node->name.size()));
  w.u32(uint32_t(node->vertices.size()));
  w.text(node->name);
  for(const auto& v:node->vertices){
   w.f64(v.x);w.f64(v.y);w.f64(v.in_dx);w.f64(v.in_dy);
   w.f64(v.out_dx);w.f64(v.out_dy);
  }
  for(auto it=node->children.rbegin();it!=node->children.rend();++it)
   pending.push_back(&doc.nodes.at(*it));
 }
}
std::vector<uint8_t> serialize_doc(const CNL_Document& d){
 Writer w;
 for(char ch:kMagic)w.u8(uint8_t(ch));
 w.u32(1);
 w.u32(uint32_t(d.nodes.size()));
 w.u64(d.next_id);w.u32(0);
 write_node(d,d.nodes.at(1),w);
 w.u64(fnv(w.b.data(),w.b.size()));
 return std::move(w.b);
}
CNL_Status deserialize_doc(const void* buf,size_t n,CNL_Document** dest) {
 if(!buf||!dest)return CNL_INVALID_ARGUMENT;
 *dest=nullptr;
 if(n<36||n>kMaxBlob)return CNL_BAD_ARCHIVE;
 const auto* raw=static_cast<const uint8_t*>(buf);
 uint64_t check=0;
 Reader check_reader{raw+n-8,8};
 if(!check_reader.u64(check) || fnv(raw,n-8)!=check)return CNL_BAD_ARCHIVE;
 Reader r{raw,n-8};
 uint8_t magic[8]{};
 if(!r.bytes(magic,8)||std::memcmp(magic,kMagic,8))return CNL_BAD_ARCHIVE;
 uint32_t version=0,count=0,flags=0;uint64_t next_id=0;
 if(!r.u32(version))return CNL_BAD_ARCHIVE;
 if(version!=1)return CNL_UNSUPPORTED_ARCHIVE_VERSION;
 if(!r.u32(count)||!r.u64(next_id)||!r.u32(flags))return CNL_BAD_ARCHIVE;
 if(flags||count<1||count>kMaxNodes||next_id<=1)return CNL_BAD_ARCHIVE;
 auto doc=std::make_unique<CNL_Document>();
 doc->nodes.clear();
 uint64_t highest=0;
 for(uint32_t index=0;index<count;++index){
  Node v;
  uint8_t kind,closed;
  uint16_t reserved;
  uint32_t name_bytes,verts;
  if(!r.u64(v.id)||!r.u64(v.parent)||!r.u8(kind)||!r.u8(closed)
    ||!r.u16(reserved)||!r.u32(name_bytes)||!r.u32(verts))return CNL_BAD_ARCHIVE;
  if((kind!=CNL_NODE_GROUP&&kind!=CNL_NODE_PATH)||closed>1||reserved
    ||name_bytes>kMaxName||verts>kMaxVertices||v.id==0
    ||(kind==CNL_NODE_GROUP&&(closed||verts))
    ||(kind==CNL_NODE_PATH&&(verts<(closed?3u:2u))))return CNL_BAD_ARCHIVE;
  if(name_bytes>r.n-r.pos)return CNL_BAD_ARCHIVE;
  v.name.assign(reinterpret_cast<const char*>(r.p+r.pos),name_bytes);
  r.pos+=name_bytes;
  if(v.name.find('\0')!=std::string::npos)return CNL_BAD_ARCHIVE;
  v.kind=CNL_NodeKind(kind);v.closed=bool(closed);
  if(verts>(r.n-r.pos)/sizeof(CNL_PathVertex))return CNL_BAD_ARCHIVE;
  v.vertices.resize(verts);
  for(auto& p:v.vertices){
   if(!r.f64(p.x)||!r.f64(p.y)||!r.f64(p.in_dx)||!r.f64(p.in_dy)
     ||!r.f64(p.out_dx)||!r.f64(p.out_dy))return CNL_BAD_ARCHIVE;
  }
  if(index==0){
   if(v.id!=1||v.parent!=0||v.kind!=CNL_NODE_GROUP)return CNL_BAD_ARCHIVE;
  }else{
   if(v.id==1)return CNL_BAD_ARCHIVE;
   auto parent=doc->nodes.find(v.parent);
   if(parent==doc->nodes.end()||parent->second.kind!=CNL_NODE_GROUP)return CNL_BAD_ARCHIVE;
   parent->second.children.push_back(v.id);
  }
  highest=std::max(highest,v.id);
  if(!doc->nodes.emplace(v.id,std::move(v)).second)return CNL_BAD_ARCHIVE;
 }
 if(r.pos!=r.n||next_id<=highest||doc->nodes.size()!=count)return CNL_BAD_ARCHIVE;
 doc->next_id=next_id;
 *dest=doc.release();
 return CNL_OK;
}
} // namespace

extern "C" {
CNL_CoreVersion cnl_core_version(void){return {1,1};}
CNL_Document* cnl_document_create(void){
 try {return new CNL_Document();}
 catch(...){return nullptr;}
}
void cnl_document_destroy(CNL_Document* d){delete d;}
CNL_Status cnl_document_clone(const CNL_Document* d,CNL_Document** out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 *out=nullptr;
 try{*out=new CNL_Document(*d);return CNL_OK;}
 catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_NodeId cnl_document_root(const CNL_Document* d){return d?1:0;}
CNL_Status cnl_document_add_group(CNL_Document* d,CNL_NodeId parent,const char* name,CNL_NodeId* out){
 if(!d||!valid_name(name)||!out)return CNL_INVALID_ARGUMENT;
 try{Node n;n.name=name;return attach(d,parent,std::move(n),out);}
 catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status cnl_document_add_path(CNL_Document* d,CNL_NodeId parent,const char* name,int closed,
  const CNL_PathVertex* points,uint32_t count,CNL_NodeId* out){
 if(!d||!valid_name(name)||!points||!out||(closed!=0&&closed!=1)
   ||count>kMaxVertices||count<(closed?3u:2u))return CNL_INVALID_ARGUMENT;
 for(uint32_t i=0;i<count;++i)if(!valid(points[i]))return CNL_INVALID_ARGUMENT;
 try{Node n;n.kind=CNL_NODE_PATH;n.name=name;n.closed=closed!=0;
  n.vertices.assign(points,points+count);return attach(d,parent,std::move(n),out);}
 catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status cnl_document_add_ellipse(
 CNL_Document* d,CNL_NodeId parent,const char* name,
 double cx,double cy,double rx,double ry,CNL_NodeId* out) {
 if(!std::isfinite(cx)||!std::isfinite(cy)||!std::isfinite(rx)||
    !std::isfinite(ry)||rx<=0||ry<=0)return CNL_INVALID_ARGUMENT;
 constexpr double k=0.5522847498307936;
 const double dx=k*rx,dy=k*ry;
 const CNL_PathVertex p[4]={
  {cx+rx,cy,0,-dy,0,dy},
  {cx,cy+ry,dx,0,-dx,0},
  {cx-rx,cy,0,dy,0,-dy},
  {cx,cy-ry,-dx,0,dx,0}
 };
 for(const auto& v:p)if(!valid(v))return CNL_INVALID_ARGUMENT;
 return cnl_document_add_path(d,parent,name,1,p,4,out);
}
CNL_Status cnl_document_copy_cubics(
 const CNL_Document* d,CNL_NodeId id,
 CNL_CubicBezier* out,uint32_t* count){
 if(!d||!count)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_PATH)return CNL_WRONG_TYPE;
 const auto& n=it->second;
 const uint32_t needed=uint32_t(n.vertices.size()-(n.closed?0:1));
 const uint32_t capacity=*count;*count=needed;
 if(!out||capacity<needed)return CNL_NO_SPACE;
 for(uint32_t i=0;i<needed;++i){
  const auto& a=n.vertices[i];
  const auto& b=n.vertices[(i+1)%n.vertices.size()];
  out[i]={a.x,a.y,a.x+a.out_dx,a.y+a.out_dy,
          b.x+b.in_dx,b.y+b.in_dy,b.x,b.y};
 }
 return CNL_OK;
}
CNL_Status cnl_document_move_node(CNL_Document* d,CNL_NodeId id,CNL_NodeId parent){
 if(!d||id==1)return CNL_INVALID_ARGUMENT;
 auto node=d->nodes.find(id),p=d->nodes.find(parent);
 if(node==d->nodes.end()||p==d->nodes.end())return CNL_NOT_FOUND;
 if(p->second.kind!=CNL_NODE_GROUP)return CNL_WRONG_TYPE;
 if(parent==id)return CNL_CYCLE;
 for(CNL_NodeId cur=parent;cur;){
  if(cur==id)return CNL_CYCLE;
  auto it=d->nodes.find(cur);
  if(it==d->nodes.end())return CNL_INTERNAL_ERROR;
  cur=it->second.parent;
 }
 if(node->second.parent==parent)return CNL_OK;
 try{
  p->second.children.push_back(id);
  auto& old=d->nodes.at(node->second.parent).children;
  auto it=std::find(old.begin(),old.end(),id);
  if(it==old.end())return CNL_INTERNAL_ERROR;
  old.erase(it);
  node->second.parent=parent;
  return CNL_OK;
 }catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status cnl_document_get_kind(const CNL_Document* d,CNL_NodeId id,CNL_NodeKind* out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 *out=it->second.kind;return CNL_OK;
}
CNL_Status cnl_document_get_parent(const CNL_Document* d,CNL_NodeId id,CNL_NodeId* out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 *out=it->second.parent;return CNL_OK;
}
CNL_Status cnl_document_get_child_count(const CNL_Document* d,CNL_NodeId id,uint32_t* out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_GROUP)return CNL_WRONG_TYPE;
 *out=uint32_t(it->second.children.size());return CNL_OK;
}
CNL_Status cnl_document_get_child(const CNL_Document* d,CNL_NodeId id,uint32_t idx,CNL_NodeId* out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_GROUP)return CNL_WRONG_TYPE;
 if(idx>=it->second.children.size())return CNL_OUT_OF_RANGE;
 *out=it->second.children[idx];return CNL_OK;
}
CNL_Status cnl_document_get_name(const CNL_Document* d,CNL_NodeId id,char* dest,size_t* size){
 if(!d||!size)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 size_t needed=it->second.name.size()+1;
 size_t available=*size;*size=needed;
 if(!dest||available<needed)return CNL_NO_SPACE;
 std::memcpy(dest,it->second.name.c_str(),needed);return CNL_OK;
}
CNL_Status cnl_document_get_path_info(const CNL_Document* d,CNL_NodeId id,int* closed,uint32_t* size){
 if(!d||!closed||!size)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_PATH)return CNL_WRONG_TYPE;
 *closed=it->second.closed?1:0;*size=uint32_t(it->second.vertices.size());return CNL_OK;
}
CNL_Status cnl_document_get_vertex(const CNL_Document* d,CNL_NodeId id,uint32_t ix,CNL_PathVertex* out){
 if(!d||!out)return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_PATH)return CNL_WRONG_TYPE;
 if(ix>=it->second.vertices.size())return CNL_OUT_OF_RANGE;
 *out=it->second.vertices[ix];return CNL_OK;
}
CNL_Status cnl_document_set_vertex(CNL_Document* d,CNL_NodeId id,uint32_t ix,const CNL_PathVertex* in){
 if(!d||!in||!valid(*in))return CNL_INVALID_ARGUMENT;
 auto it=d->nodes.find(id);if(it==d->nodes.end())return CNL_NOT_FOUND;
 if(it->second.kind!=CNL_NODE_PATH)return CNL_WRONG_TYPE;
 if(ix>=it->second.vertices.size())return CNL_OUT_OF_RANGE;
 it->second.vertices[ix]=*in;return CNL_OK;
}
CNL_Status cnl_document_serialize(const CNL_Document* d,void* dest,size_t* count){
 if(!d||!count)return CNL_INVALID_ARGUMENT;
 try {
  auto data=serialize_doc(*d);
  if(data.size()>kMaxBlob)return CNL_LIMIT_EXCEEDED;
  size_t provided=*count;*count=data.size();
  if(!dest||provided<data.size())return CNL_NO_SPACE;
  std::memcpy(dest,data.data(),data.size());return CNL_OK;
 }catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status cnl_document_deserialize(const void* buffer,size_t n,CNL_Document** out){
 try{return deserialize_doc(buffer,n,out);}
 catch(...){return CNL_INTERNAL_ERROR;}
}
} // extern "C"
