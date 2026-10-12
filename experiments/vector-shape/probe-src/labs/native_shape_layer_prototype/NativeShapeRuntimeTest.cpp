#include "CNLShapeRuntime.h"
#include <cmath>
#include <cstring>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>
#include <limits>
#define CHECK(x) do { if(!(x)){std::fprintf(stderr,"FAIL: %s @%d\n",#x,__LINE__);return 2;} }while(0)
struct Del{void operator()(CNL_ShapeLayer* p)const{cnl_shape_destroy(p);}};
using Ptr=std::unique_ptr<CNL_ShapeLayer,Del>;
static std::string svg(CNL_ShapeLayer* s){
 size_t n=0;
 if(cnl_shape_svg(s,nullptr,&n)!=CNL_NO_SPACE)return {};
 std::vector<char> buffer(n);
 if(cnl_shape_svg(s,buffer.data(),&n)!=CNL_OK)return {};
 return buffer.data();
}
static std::vector<unsigned char> blob(CNL_ShapeLayer* s){
 size_t n=0;
 if(cnl_shape_archive(s,nullptr,&n)!=CNL_NO_SPACE)return {};
 std::vector<unsigned char> ret(n);
 if(cnl_shape_archive(s,ret.data(),&n)!=CNL_OK)return {};
 return ret;
}
int main(){
 const auto f=cnl_shape_features();
 CHECK(f.abi_version==1 && f.supports_undo_redo && f.supports_vector_svg);
 CHECK(f.supports_editable_cubics && f.supports_nested_contents && f.supports_stable_archive);
 CHECK(!f.connected_to_adobe_native_tdb && !f.connected_to_adobe_contents);
 CHECK(!f.connected_to_adobe_pen && !f.connected_to_adobe_vectorart);
 Ptr shape(cnl_shape_create());CHECK(shape);
 CHECK(cnl_shape_contents_root(shape.get())==1);
 CHECK(cnl_shape_undo(shape.get())==CNL_OUT_OF_RANGE);
 CHECK(cnl_shape_redo(shape.get())==CNL_OUT_OF_RANGE);
 CNL_NodeId group=0,nested=0,ellipse=0;
 CHECK(cnl_shape_add_group(shape.get(),1,"CNL Independent Contents",&group)==CNL_OK);
 CHECK(cnl_shape_add_group(shape.get(),group,"Nested Group",&nested)==CNL_OK);
 CHECK(cnl_shape_add_ellipse(shape.get(),nested,"Procedural Ellipse",200,160,75,40,&ellipse)==CNL_OK);
 CHECK(ellipse==4&&cnl_shape_undo_depth(shape.get())==3);
 CNL_PathVertex anchor{};
 CHECK(cnl_shape_get_vertex(shape.get(),ellipse,0,&anchor)==CNL_OK);
 CHECK(anchor.x==275&&anchor.y==160);
 auto before=blob(shape.get());CHECK(!before.empty());
 auto beforeSvg=svg(shape.get());CHECK(beforeSvg.find("<path")!=std::string::npos);
 CHECK(beforeSvg.find("data-cnl-id=\"4\"")!=std::string::npos);
 CHECK(beforeSvg.find("C ")!=std::string::npos);
 CNL_PathVertex bad=anchor;
 bad.x=std::numeric_limits<double>::infinity();
 CHECK(cnl_shape_set_vertex(shape.get(),ellipse,0,&bad)==CNL_INVALID_ARGUMENT);
 CHECK(cnl_shape_undo_depth(shape.get())==3);
 anchor.x+=20;
 anchor.in_dx-=7;
 CHECK(cnl_shape_set_vertex(shape.get(),ellipse,0,&anchor)==CNL_OK);
 CHECK(cnl_shape_undo_depth(shape.get())==4);
 auto changed=blob(shape.get());CHECK(changed!=before);
 CHECK(cnl_shape_undo(shape.get())==CNL_OK);
 CHECK(blob(shape.get())==before);
 CHECK(cnl_shape_redo_depth(shape.get())==1);
 CHECK(cnl_shape_redo(shape.get())==CNL_OK);
 CHECK(blob(shape.get())==changed);
 CHECK(cnl_shape_redo_depth(shape.get())==0);
 CHECK(cnl_shape_undo(shape.get())==CNL_OK);
 CHECK(cnl_shape_undo_depth(shape.get())==3);
 CHECK(cnl_shape_add_ellipse(shape.get(),group,"Second",330,80,25,15,&ellipse)==CNL_OK);
 CHECK(cnl_shape_redo_depth(shape.get())==0);
 CHECK(cnl_shape_redo(shape.get())==CNL_OUT_OF_RANGE);
 auto snapshot=blob(shape.get());CHECK(snapshot.size()>80);
 CNL_ShapeLayer* loaded=nullptr;
 CHECK(cnl_shape_from_archive(snapshot.data(),snapshot.size(),&loaded)==CNL_OK&&loaded);
 Ptr restored(loaded);
 CHECK(cnl_shape_contents_root(restored.get())==1);
 CHECK(blob(restored.get())==snapshot);
 CHECK(cnl_shape_undo_depth(restored.get())==0);
 CHECK(cnl_shape_undo(restored.get())==CNL_OUT_OF_RANGE);
 CHECK(svg(restored.get()).find("data-cnl-id=\"5\"")!=std::string::npos);
 auto corrupt=snapshot;corrupt[52]^=1;
 loaded=nullptr;
 CHECK(cnl_shape_from_archive(corrupt.data(),corrupt.size(),&loaded)==CNL_BAD_ARCHIVE);
 CHECK(!loaded);
 CHECK(cnl_shape_move_node(shape.get(),group,nested)==CNL_CYCLE);
 CHECK(blob(shape.get())==snapshot);
 CHECK(cnl_shape_undo_depth(shape.get())==4);
 CHECK(cnl_shape_add_group(shape.get(),group,"<script>alert(1)</script>",&nested)==CNL_OK);
 auto text=svg(shape.get());
 CHECK(text.find("<script>")==std::string::npos);
 // History is bounded under repeated edits. New paths all retain stable IDs.
 for(int i=0;i<90;++i){
   CNL_NodeId extra=0;
   CHECK(cnl_shape_add_ellipse(shape.get(),group,"Stable Identity",i*3.0,30,1,1,&extra)==CNL_OK);
 }
 CHECK(cnl_shape_undo_depth(shape.get())==64);
 for(int i=0;i<64;++i)CHECK(cnl_shape_undo(shape.get())==CNL_OK);
 CHECK(cnl_shape_undo(shape.get())==CNL_OUT_OF_RANGE);
 CHECK(cnl_shape_redo_depth(shape.get())==64);
 for(int i=0;i<64;++i)CHECK(cnl_shape_redo(shape.get())==CNL_OK);
 CHECK(cnl_shape_redo(shape.get())==CNL_OUT_OF_RANGE);
 // Existing CNL native owner works without any Shape/Mask/Effect fallback.
 std::printf("PASS independent CNL Shape native C++ runtime: nested Contents, stable IDs, "
 "editable Bezier, deterministic archived state, 64-step undo/redo, "
 "vector path output and malformed archives rejected. archive=%zu bytes\n",snapshot.size());
 return 0;
}
