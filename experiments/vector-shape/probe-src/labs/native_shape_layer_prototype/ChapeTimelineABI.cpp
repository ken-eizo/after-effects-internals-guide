#include "ChapeTimelineABI.h"
#include "ChapeNativeTimeline.h"
#include <cstring>
#include <memory>
#include <new>
#include <vector>
struct CHAPE_Timeline{chape::timeline::Document document;};
namespace {
using namespace chape::timeline;
CHAPE_Result result(Code x){return static_cast<CHAPE_Result>(static_cast<unsigned>(x));}
Value from(const CHAPE_Value& v){
 Value r;for(int i=0;i<4;++i)r.items[i]=v.components[i];return r;
}
CHAPE_Value into(const Value& v){
 CHAPE_Value r{};for(int i=0;i<4;++i)r.components[i]=v.items[i];return r;
}
}
extern "C" {
uint32_t chape_timeline_abi_version(void){return 1;}
CHAPE_Timeline* chape_timeline_create(void){
 try{return new CHAPE_Timeline();}catch(...){return nullptr;}
}
void chape_timeline_destroy(CHAPE_Timeline* t){delete t;}
CHAPE_Result chape_timeline_define_type(CHAPE_Timeline* t,const char* name,uint32_t kind,uint32_t order){
 if(!t||!name||kind>4||order>1)return CHAPE_INVALID;
 try{return result(t->document.registerType({name,static_cast<Kind>(kind),{},static_cast<Order>(order)}));}
 catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_permit(CHAPE_Timeline* t,const char* parent,const char* const* child,size_t n){
 if(!t||!parent||(n&&!child)||n>256)return CHAPE_INVALID;
 try{
  std::vector<std::string> permitted;
  for(size_t i=0;i<n;++i){if(!child[i])return CHAPE_INVALID;permitted.emplace_back(child[i]);}
  return result(t->document.permit(parent,std::move(permitted)));
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_add(CHAPE_Timeline* t,uint64_t parent,const char* type,
 const char* label,uint64_t* out){
 if(out)*out=0;
 if(!t||!type||!label||!out)return CHAPE_INVALID;
 try{return result(t->document.add(parent,type,label,*out));}
 catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_move(CHAPE_Timeline* t,uint64_t id,uint64_t parent,size_t index){
 if(!t)return CHAPE_INVALID;
 try{return result(t->document.move(id,parent,index));}catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_set_base(CHAPE_Timeline* t,uint64_t id,const CHAPE_Value* v){
 if(!t||!v)return CHAPE_INVALID;
 try{return result(t->document.setBase(id,from(*v)));}catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_set_key(CHAPE_Timeline* t,uint64_t id,const CHAPE_Key* k){
 if(!t||!k||k->interpolation>1)return CHAPE_INVALID;
 try{
  Key key{k->tick,from(k->value),static_cast<Interpolation>(k->interpolation)};
  return result(t->document.setKey(id,key));
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_sample(const CHAPE_Timeline* t,uint64_t id,int64_t tick,CHAPE_Value* out){
 if(!t||!out)return CHAPE_INVALID;
 try{
  Value v{};
  auto rc=t->document.sample(id,tick,v);
  if(rc==Code::Ok)*out=into(v);
  return result(rc);
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_evaluate(const CHAPE_Timeline* t,int64_t tick,CHAPE_VisitEvent callback,void* user){
 if(!t||!callback)return CHAPE_INVALID;
 try{
  const auto events=t->document.evaluate(tick);
  for(const auto& event:events){
   uint32_t action=event.kind=="begin"?0u:(event.kind=="property"?1u:2u);
   CHAPE_EvalEvent item{event.id,action,event.matchName.c_str(),into(event.value)};
   const auto rc=callback(&item,user);
   if(rc!=CHAPE_OK)return rc;
  }
  return CHAPE_OK;
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_archive(const CHAPE_Timeline* t,void* output,size_t* bytes){
 if(!t||!bytes)return CHAPE_INVALID;
 try{
  auto data=t->document.archive();
  if(data.empty())return CHAPE_INTERNAL_ERROR;
  const auto available=*bytes;
  *bytes=data.size();
  if(!output||available<data.size())return CHAPE_NO_SPACE;
  std::memcpy(output,data.data(),data.size());
  return CHAPE_OK;
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_restore(const void* input,size_t size,CHAPE_Timeline** output){
 if(!output)return CHAPE_INVALID;
 *output=nullptr;
 if(!input||size==0||size>16u*1024u*1024u)return CHAPE_INVALID;
 try{
  auto value=std::make_unique<CHAPE_Timeline>();
  std::vector<uint8_t> data(static_cast<const uint8_t*>(input),
                             static_cast<const uint8_t*>(input)+size);
  auto code=Document::restore(data,value->document);
  if(code!=Code::Ok)return result(code);
  *output=value.release();return CHAPE_OK;
 }catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_undo(CHAPE_Timeline* t){
 if(!t)return CHAPE_INVALID;
 try{return result(t->document.undo());}catch(...){return CHAPE_INTERNAL_ERROR;}
}
CHAPE_Result chape_timeline_redo(CHAPE_Timeline* t){
 if(!t)return CHAPE_INVALID;
 try{return result(t->document.redo());}catch(...){return CHAPE_INTERNAL_ERROR;}
}
}
