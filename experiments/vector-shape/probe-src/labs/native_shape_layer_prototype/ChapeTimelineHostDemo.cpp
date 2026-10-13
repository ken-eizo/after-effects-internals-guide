// Public AEGP menu-only demonstrator for native CNL typed Timeline grammar.
// No Project mutation, no Adobe native TDB/BEE Layer insertion.
#define _CRT_SECURE_NO_WARNINGS
#include "AEConfig.h"
#include "AE_GeneralPlug.h"
#include "AEGP_SuiteHandler.h"
#include "ChapeNativeTimeline.h"
#include <Windows.h>
#include <cstdio>
#include <string>
#include <vector>
using chape::timeline::Document;
using chape::timeline::Code;
using chape::timeline::Kind;
using chape::timeline::Key;
using chape::timeline::Interpolation;
using chape::timeline::Value;
namespace {
Value val(double a,double b=0,double c=0,double d=0){
 Value v;v.items={a,b,c,d};return v;
}
void info(SPBasicSuite* b,AEGP_PluginID id,const char* message){
 AEGP_SuiteHandler suites(b);
 suites.UtilitySuite3()->AEGP_ReportInfo(id,message);
}
}
A_Err CNL_RunTypedTimelineProbe(SPBasicSuite* basic,AEGP_PluginID plugin){
 char tmp[MAX_PATH+2]{};
 DWORD length=GetTempPathA(MAX_PATH,tmp);
 if(!length || length>MAX_PATH)return A_Err_NONE;
 const auto report=std::string(tmp)+"ChapeLayer_TypedTimelineDemo.tsv";
 FILE* out=fopen(report.c_str(),"wb");
 if(!out){info(basic,plugin,"ChapeLayer: Could not write typed timeline TEMP report.");return A_Err_NONE;}
 fprintf(out,"format\tCNL Native Timeline Grammar v1\n");
 fprintf(out,"adobe_layer_registered\t0\nadobe_contents_registered\t0\n");
 fprintf(out,"host_project_changed\t0\nprivate_BEE_TDB_used\t0\n");
 Document timeline;
 auto OK=[](Code c){return c==Code::Ok;};
 bool pass=
 OK(timeline.registerType({"CNL:VectorLayer",Kind::Group,{}}))&&
 OK(timeline.registerType({"CNL:TextLayer",Kind::Group,{}}))&&
 OK(timeline.registerType({"CNL:ShapeGroup",Kind::Group,{}}))&&
 OK(timeline.registerType({"CNL:TextAnimator",Kind::Group,{}}))&&
 OK(timeline.registerType({"CNL:Position",Kind::Vector2,{}}))&&
 OK(timeline.registerType({"CNL:Opacity",Kind::Float,{}}))&&
 OK(timeline.permit("CNL:Stage",{"CNL:VectorLayer","CNL:TextLayer"}))&&
 OK(timeline.permit("CNL:VectorLayer",{"CNL:ShapeGroup"}))&&
 OK(timeline.permit("CNL:ShapeGroup",{"CNL:Position"}))&&
 OK(timeline.permit("CNL:TextLayer",{"CNL:TextAnimator"}))&&
 OK(timeline.permit("CNL:TextAnimator",{"CNL:Opacity"}));
 uint64_t layer=0,group=0,position=0,text=0,anim=0,opacity=0;
 if(pass)pass=OK(timeline.add(Document::Stage,"CNL:VectorLayer","Custom Vector",layer));
 if(pass)pass=OK(timeline.add(layer,"CNL:ShapeGroup","Contents",group));
 if(pass)pass=OK(timeline.add(group,"CNL:Position","Position",position));
 if(pass)pass=OK(timeline.add(Document::Stage,"CNL:TextLayer","Custom Text",text));
 if(pass)pass=OK(timeline.add(text,"CNL:TextAnimator","Animator",anim));
 if(pass)pass=OK(timeline.add(anim,"CNL:Opacity","Opacity",opacity));
 if(pass)pass=OK(timeline.setKey(position,Key{0,val(0,10),Interpolation::Linear}));
 if(pass)pass=OK(timeline.setKey(position,Key{100,val(80,30),Interpolation::Linear}));
 if(pass)pass=OK(timeline.setKey(opacity,Key{0,val(20),Interpolation::Hold}));
 if(pass)pass=OK(timeline.setKey(opacity,Key{100,val(70),Interpolation::Linear}));
 Value atMiddle{};
 if(pass)pass=OK(timeline.sample(position,50,atMiddle))&&atMiddle.items[0]==40&&atMiddle.items[1]==20;
 const auto archive=timeline.archive();
 Document restored;
 if(pass)pass=!archive.empty()&&Document::restore(archive,restored)==Code::Ok&&restored.archive()==archive;
 const auto emitted=restored.evaluate(50);
 if(pass)pass=emitted.size()==12; // 5 group enter/leave pairs, 2 typed property events
 fprintf(out,"typed_timeline_pass\t%d\n",pass?1:0);
 fprintf(out,"independent_layer_families\t2\n");
 fprintf(out,"archive_size_bytes\t%zu\n",archive.size());
 fprintf(out,"sample_position_x_at_tick50\t%.2f\n",atMiddle.items[0]);
 fprintf(out,"sample_position_y_at_tick50\t%.2f\n",atMiddle.items[1]);
 fprintf(out,"evaluation_events\t%zu\n",emitted.size());
 for(const auto& event:emitted)
   fprintf(out,"event\t%llu\t%s\t%s\t%.3f,%.3f,%.3f,%.3f\n",
    (unsigned long long)event.id,event.kind.c_str(),event.matchName.c_str(),
    event.value.items[0],event.value.items[1],event.value.items[2],event.value.items[3]);
 fclose(out);
 info(basic,plugin,
  pass?"ChapeLayer native typed Timeline engine PASS. Report in TEMP\\ChapeLayer_TypedTimelineDemo.tsv. No Adobe Timeline Layer created.":
  "ChapeLayer typed Timeline engine FAILED. Report in TEMP\\ChapeLayer_TypedTimelineDemo.tsv.");
 return A_Err_NONE;
}
