#include "ChapeTimelineABI.h"
#include <cstdio>
#include <cstring>
#include <memory>
#include <vector>
struct VisitorState{int begins=0,properties=0,ends=0;double observed=0;};
static CHAPE_Result visitor(const CHAPE_EvalEvent* e,void* data){
 auto* s=static_cast<VisitorState*>(data);
 if(e->action==0)++s->begins;
 else if(e->action==1){++s->properties;s->observed=e->value.components[0];}
 else if(e->action==2)++s->ends;
 else return CHAPE_INVALID;
 return CHAPE_OK;
}
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAILED line %d: %s\n",__LINE__,#x);return 2;}}while(0)
struct Del{void operator()(CHAPE_Timeline* x)const{chape_timeline_destroy(x);}};
int main(){
 CHECK(chape_timeline_abi_version()==1);
 std::unique_ptr<CHAPE_Timeline,Del> timeline(chape_timeline_create());
 CHECK(timeline);
 CHECK(chape_timeline_define_type(timeline.get(),"CNL:ArbitraryLayer",0,0)==CHAPE_OK);
 CHECK(chape_timeline_define_type(timeline.get(),"CNL:Group",0,1)==CHAPE_OK);
 CHECK(chape_timeline_define_type(timeline.get(),"CNL:CustomValue",1,0)==CHAPE_OK);
 CHECK(chape_timeline_define_type(timeline.get(),"CNL:Bad",99,1)==CHAPE_INVALID);
 const char* owners[]={"CNL:ArbitraryLayer"};
 CHECK(chape_timeline_permit(timeline.get(),"CNL:Stage",owners,1)==CHAPE_OK);
 const char* groups[]={"CNL:Group"};
 CHECK(chape_timeline_permit(timeline.get(),"CNL:ArbitraryLayer",groups,1)==CHAPE_OK);
 const char* props[]={"CNL:CustomValue"};
 CHECK(chape_timeline_permit(timeline.get(),"CNL:Group",props,1)==CHAPE_OK);
 uint64_t layer=0,group=0,scalar=0;
 CHECK(chape_timeline_add(timeline.get(),1,"CNL:ArbitraryLayer","Novel Owner",&layer)==CHAPE_OK);
 CHECK(chape_timeline_add(timeline.get(),layer,"CNL:Group","Property Container",&group)==CHAPE_OK);
 CHECK(chape_timeline_add(timeline.get(),group,"CNL:CustomValue","Animated",&scalar)==CHAPE_OK);
 CHECK(layer>1&&group>layer&&scalar>group);
 CHAPE_Value base{{10,0,0,0}};
 CHECK(chape_timeline_set_base(timeline.get(),scalar,&base)==CHAPE_OK);
 CHAPE_Key a{0,{{10,0,0,0}},1},b{100,{{90,0,0,0}},1};
 CHECK(chape_timeline_set_key(timeline.get(),scalar,&a)==CHAPE_OK);
 CHECK(chape_timeline_set_key(timeline.get(),scalar,&b)==CHAPE_OK);
 CHAPE_Value sampled{};
 CHECK(chape_timeline_sample(timeline.get(),scalar,50,&sampled)==CHAPE_OK);
 CHECK(sampled.components[0]==50);
 VisitorState vis{};
 CHECK(chape_timeline_evaluate(timeline.get(),50,visitor,&vis)==CHAPE_OK);
 CHECK(vis.begins==3&&vis.ends==3&&vis.properties==1&&vis.observed==50);
 CHECK(chape_timeline_evaluate(timeline.get(),50,nullptr,&vis)==CHAPE_INVALID);
 CHECK(chape_timeline_set_key(timeline.get(),scalar,nullptr)==CHAPE_INVALID);
 CHECK(chape_timeline_move(timeline.get(),layer,group,0)==CHAPE_CYCLE);
 size_t needed=0;
 CHECK(chape_timeline_archive(timeline.get(),nullptr,&needed)==CHAPE_NO_SPACE && needed>100);
 std::vector<uint8_t> bytes(needed);
 CHECK(chape_timeline_archive(timeline.get(),bytes.data(),&needed)==CHAPE_OK);
 CHAPE_Timeline* restored=nullptr;
 CHECK(chape_timeline_restore(bytes.data(),bytes.size(),&restored)==CHAPE_OK&&restored);
 std::unique_ptr<CHAPE_Timeline,Del> again(restored);
 CHECK(chape_timeline_sample(again.get(),scalar,50,&sampled)==CHAPE_OK&&sampled.components[0]==50);
 bytes[bytes.size()/2]^=1;
 restored=nullptr;
 CHECK(chape_timeline_restore(bytes.data(),bytes.size(),&restored)==CHAPE_CORRUPT);
 CHECK(!restored);
 CHECK(chape_timeline_undo(timeline.get())==CHAPE_OK);
 CHECK(chape_timeline_redo(timeline.get())==CHAPE_OK);
 CHECK(chape_timeline_restore(bytes.data(),bytes.size(),nullptr)==CHAPE_INVALID);
 std::printf("PASS public versioned C ABI v1 for typed Timeline creation, schema, keyframes, archiving and Undo\n");
 return 0;
}
