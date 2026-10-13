#include "ChapeNativeTimeline.h"
#include <algorithm>
#include <cstdio>
#include <cstring>
#include <limits>
#include <vector>
#include <string>
using namespace chape::timeline;
#define CHECK(x) do{if(!(x)){std::fprintf(stderr,"FAIL at %d: %s\n",__LINE__,#x);return 2;}}while(0)
static Value scalar(double x){Value v;v.items[0]=x;return v;}
static Value pair(double x,double y){Value v;v.items[0]=x;v.items[1]=y;return v;}
static Value color(double r,double g,double b,double a){Value v;v.items={r,g,b,a};return v;}
int main(){
 Document document;
 CHECK(document.node(Document::Stage));
 CHECK(document.registerType({"CNL:VectorLayer",Kind::Group,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:TextLayer",Kind::Group,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:ShapeGroup",Kind::Group,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:TextAnimator",Kind::Group,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:Position",Kind::Vector2,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:Opacity",Kind::Float,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:Color",Kind::Color,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:Enabled",Kind::Boolean,{}})==Code::Ok);
 CHECK(document.registerType({"CNL:VectorLayer",Kind::Group,{}})==Code::Duplicate);
 CHECK(document.permit("CNL:Stage",{"CNL:VectorLayer","CNL:TextLayer"})==Code::Ok);
 CHECK(document.permit("CNL:VectorLayer",{"CNL:ShapeGroup","CNL:Position","CNL:Opacity"})==Code::Ok);
 CHECK(document.permit("CNL:TextLayer",{"CNL:TextAnimator","CNL:Position"})==Code::Ok);
 CHECK(document.permit("CNL:ShapeGroup",{"CNL:Position","CNL:Color","CNL:ShapeGroup"})==Code::Ok);
 CHECK(document.permit("CNL:TextAnimator",{"CNL:Opacity","CNL:Enabled"})==Code::Ok);
 CHECK(document.permit("CNL:Opacity",{"CNL:Color"})==Code::WrongKind);
 uint64_t vectorLayer=0,textLayer=0,geo=0,pos=0,col=0,anim=0,opacity=0,onoff=0;
 CHECK(document.add(Document::Stage,"CNL:VectorLayer","Vector",vectorLayer)==Code::Ok); // typed custom native object 1
 CHECK(document.add(Document::Stage,"CNL:TextLayer","Type",textLayer)==Code::Ok); // typed custom native object 2
 CHECK(document.add(vectorLayer,"CNL:ShapeGroup","Geometry",geo)==Code::Ok);
 CHECK(document.add(geo,"CNL:Position","Path Coordinates",pos)==Code::Ok);
 CHECK(document.add(geo,"CNL:Color","Fill",col)==Code::Ok);
 CHECK(document.add(textLayer,"CNL:TextAnimator","Animator 1",anim)==Code::Ok);
 CHECK(document.add(anim,"CNL:Opacity","Opacity",opacity)==Code::Ok);
 CHECK(document.add(anim,"CNL:Enabled","Enabled",onoff)==Code::Ok);
 uint64_t bad=55;
 CHECK(document.add(textLayer,"CNL:ShapeGroup","Not allowed",bad)==Code::Forbidden);
 CHECK(bad==0);
 CHECK(document.add(geo,"CNL:Opacity","Not allowed",bad)==Code::Forbidden);
 CHECK(document.move(geo,geo,0)==Code::Cycle);
 CHECK(document.move(vectorLayer,geo,0)==Code::Cycle);
 CHECK(document.move(col,textLayer,0)==Code::Forbidden);
 CHECK(document.permit("CNL:ShapeGroup",{"CNL:Color"})==Code::Forbidden);
 CHECK(document.setOrder("CNL:ShapeGroup",Order::Reverse)==Code::Ok);
 CHECK(document.setBase(pos,pair(9,12))==Code::Ok);
 CHECK(document.setBase(col,color(.2,.4,.6,1))==Code::Ok);
 CHECK(document.setBase(opacity,scalar(40))==Code::Ok);
 CHECK(document.setBase(onoff,scalar(1))==Code::Ok);
 CHECK(document.setBase(geo,pair(1,2))==Code::WrongKind);
 Value nan=scalar(std::numeric_limits<double>::quiet_NaN());
 CHECK(document.setBase(pos,nan)==Code::Invalid);
 CHECK(document.setKey(pos,Key{-100,pair(-10,20),Interpolation::Linear})==Code::Ok);
 CHECK(document.setKey(pos,Key{100,pair(10,40),Interpolation::Linear})==Code::Ok);
 CHECK(document.setKey(opacity,Key{0,scalar(0),Interpolation::Hold})==Code::Ok);
 CHECK(document.setKey(opacity,Key{100,scalar(100),Interpolation::Linear})==Code::Ok);
 CHECK(document.setKey(onoff,Key{0,scalar(0),Interpolation::Linear})==Code::Ok);
 CHECK(document.setKey(onoff,Key{100,scalar(1),Interpolation::Linear})==Code::Ok);
 Value sample{};
 CHECK(document.sample(pos,0,sample)==Code::Ok && sample.items[0]==0&&sample.items[1]==30);
 CHECK(document.sample(pos,-500,sample)==Code::Ok&&sample.items[0]==-10);
 CHECK(document.sample(pos,500,sample)==Code::Ok&&sample.items[0]==10);
 CHECK(document.sample(opacity,50,sample)==Code::Ok&&sample.items[0]==0); // Hold
 CHECK(document.sample(onoff,50,sample)==Code::Ok&&sample.items[0]==0); // Bool is always discrete
 auto trace=document.evaluate(0);
 CHECK(!trace.empty());
 CHECK(trace.front().kind=="begin" && trace.front().matchName=="CNL:Stage");
 CHECK(trace.back().kind=="end");
 size_t cix=0,pix=0;
 for(size_t i=0;i<trace.size();++i){
   if(trace[i].id==col)cix=i;
   if(trace[i].id==pos)pix=i;
 }
 CHECK(cix>0&&pix>0&&cix<pix); // group reverse order affects typed evaluation
 auto saved=document.archive();
 CHECK(saved.size()>250);
 auto again=document.archive();CHECK(again==saved); // deterministic byte layout
 Document loaded;
 CHECK(Document::restore(saved,loaded)==Code::Ok);
 CHECK(loaded.archive()==saved);
 CHECK(loaded.undoDepth()==0&&loaded.redoDepth()==0);
 CHECK(loaded.node(vectorLayer)&&loaded.node(textLayer));
 CHECK(loaded.sample(pos,0,sample)==Code::Ok&&sample.items[1]==30);
 auto damaged=saved;
 damaged[damaged.size()/2]^=0x80;
 Document untouched;
 CHECK(Document::restore(damaged,untouched)==Code::Corrupt);
 CHECK(untouched.node(Document::Stage)!=nullptr);
 auto truncated=saved;truncated.resize(saved.size()-20);
 CHECK(Document::restore(truncated,untouched)==Code::Corrupt);
 CHECK(Document::restore({0,0,0,0},untouched)==Code::Corrupt);
 // Invalid and malicious archive bytes must never partially replace a document.
 for(size_t i=0;i<saved.size();i+=std::max(size_t(1),saved.size()/131)){
   auto fuzz=saved;fuzz[i]^=uint8_t(1u<<(i%8));
   CHECK(Document::restore(fuzz,untouched)==Code::Corrupt);
   CHECK(untouched.node(Document::Stage));
 }
 for(size_t n=0;n<saved.size();n+=std::max(size_t(1),saved.size()/97)){
   std::vector<uint8_t> fuzz(saved.begin(),saved.begin()+n);
   CHECK(Document::restore(fuzz,untouched)==Code::Corrupt);
 }
 CHECK(document.setOrder("CNL:ShapeGroup",Order::Forward)==Code::Ok);
 CHECK(document.archive()!=saved);
 CHECK(document.undo()==Code::Ok);
 CHECK(document.archive()==saved);
 CHECK(document.redo()==Code::Ok);
 CHECK(document.archive()!=saved);
 CHECK(document.undo()==Code::Ok);
 CHECK(document.setKey(pos,Key{0,pair(55,66),Interpolation::Linear})==Code::Ok);
 CHECK(document.redo()==Code::EmptyHistory);
 CHECK(document.sample(pos,0,sample)==Code::Ok&&sample.items[0]==55);
 CHECK(document.move(col,geo,0)==Code::Ok);
 CHECK(document.move(pos,geo,0)==Code::Ok);
 // Modifying schema after children exist must not strand existing children.
 CHECK(document.permit("CNL:VectorLayer",{"CNL:Opacity"})==Code::Forbidden);
 CHECK(document.permit("CNL:VectorLayer",{"CNL:ShapeGroup","CNL:Opacity","CNL:Position"})==Code::Ok);
 CHECK(document.registerType({"CNL:CustomCompositor",Kind::Group,{}})==Code::Ok);
 CHECK(document.permit("CNL:Stage",{"CNL:VectorLayer","CNL:TextLayer","CNL:CustomCompositor"})==Code::Ok);
 uint64_t compositor=0; CHECK(document.add(Document::Stage,"CNL:CustomCompositor","Novel Layer Family",compositor)==Code::Ok);
 CHECK(document.node(compositor)->id>textLayer);
 // Mixed named and indexed groups, independent schema, multiple native typed owner models.
 std::printf("PASS generic native Timeline grammar: 3 layer families, custom nested Contents,\n 4 parameter kinds, Hold/Linear keyframes, order, rule admission, rollback, deterministic\n archive, checksum/cycle validation. archive=%zu bytes, events=%zu\n",saved.size(),trace.size());
 return 0;
}
