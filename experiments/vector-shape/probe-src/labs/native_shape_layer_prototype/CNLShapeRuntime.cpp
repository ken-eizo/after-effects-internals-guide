// Independently owned native Shape data and vector command output.
// This implementation NEVER calls Adobe private APIs, and never constructs
// a Mask, built-in Shape Layer, PF_World or custom TDB_Stream subclass.
#include "CNLShapeRuntime.h"
#include <algorithm>
#include <deque>
#include <iomanip>
#include <locale>
#include <memory>
#include <new>
#include <sstream>
#include <string>
#include <vector>
#include <cstring>

struct CNL_ShapeLayer {
    CNL_Document* doc=nullptr;
    std::deque<std::vector<unsigned char>> undo,redo;
    ~CNL_ShapeLayer(){cnl_document_destroy(doc);}
};
namespace {
constexpr size_t kHistory=64;
constexpr size_t kSvgMax=16u*1024u*1024u;
CNL_Status capture(const CNL_Document* doc,std::vector<unsigned char>& dst){
    size_t n=0;
    CNL_Status st=cnl_document_serialize(doc,nullptr,&n);
    if(st!=CNL_NO_SPACE || n==0 || n>64u*1024u*1024u)return CNL_INTERNAL_ERROR;
    dst.resize(n);
    return cnl_document_serialize(doc,dst.data(),&n);
}
void push(std::deque<std::vector<unsigned char>>& history,std::vector<unsigned char>&& state){
    history.push_back(std::move(state));
    if(history.size()>kHistory) history.pop_front();
}
template<typename F>
CNL_Status mutate(CNL_ShapeLayer* layer,F&& f){
    if(!layer||!layer->doc)return CNL_INVALID_ARGUMENT;
    try {
        std::vector<unsigned char> prior;
        CNL_Status s=capture(layer->doc,prior);
        if(s!=CNL_OK)return s;
        s=f();
        if(s!=CNL_OK)return s;
        push(layer->undo,std::move(prior));
        layer->redo.clear();
        return CNL_OK;
    }catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status restore(CNL_ShapeLayer* layer,bool backward){
    if(!layer||!layer->doc)return CNL_INVALID_ARGUMENT;
    auto& src=backward?layer->undo:layer->redo;
    auto& dst=backward?layer->redo:layer->undo;
    if(src.empty())return CNL_OUT_OF_RANGE;
    try{
        std::vector<unsigned char> current;
        if(capture(layer->doc,current)!=CNL_OK)return CNL_INTERNAL_ERROR;
        CNL_Document* next=nullptr;
        CNL_Status s=cnl_document_deserialize(src.back().data(),src.back().size(),&next);
        if(s!=CNL_OK)return s;
        std::unique_ptr<CNL_Document,void(*)(CNL_Document*)> keep(next,cnl_document_destroy);
        push(dst,std::move(current));
        cnl_document_destroy(layer->doc);
        layer->doc=keep.release();
        src.pop_back();
        return CNL_OK;
    }catch(...){return CNL_INTERNAL_ERROR;}
}
void svg_tree(const CNL_Document* doc,std::ostringstream& o){
    struct Frame{CNL_NodeId id;bool closing;};
    std::vector<Frame> stack{{cnl_document_root(doc),false}};
    size_t visited=0;
    while(!stack.empty()){
        Frame frame=stack.back();stack.pop_back();
        if(frame.closing){o<<"</g>\n";continue;}
        if(++visited>100000 || static_cast<size_t>(o.tellp())>kSvgMax)throw std::bad_alloc();
        CNL_NodeKind kind{};
        if(cnl_document_get_kind(doc,frame.id,&kind)!=CNL_OK)throw std::bad_alloc();
        if(kind==CNL_NODE_GROUP){
            o<<"<g data-cnl-id=\""<<frame.id<<"\">\n";
            stack.push_back({frame.id,true});
            uint32_t count=0;
            if(cnl_document_get_child_count(doc,frame.id,&count)!=CNL_OK)throw std::bad_alloc();
            for(uint32_t i=count;i>0;--i){
                CNL_NodeId child=0;
                if(cnl_document_get_child(doc,frame.id,i-1,&child)!=CNL_OK)throw std::bad_alloc();
                stack.push_back({child,false});
            }
        }else if(kind==CNL_NODE_PATH){
            int closed=0;uint32_t vertices=0;
            if(cnl_document_get_path_info(doc,frame.id,&closed,&vertices)!=CNL_OK)throw std::bad_alloc();
            uint32_t n=0;
            if(cnl_document_copy_cubics(doc,frame.id,nullptr,&n)!=CNL_NO_SPACE||!n)throw std::bad_alloc();
            std::vector<CNL_CubicBezier> cubics(n);
            if(cnl_document_copy_cubics(doc,frame.id,cubics.data(),&n)!=CNL_OK)throw std::bad_alloc();
            o<<"<path data-cnl-id=\""<<frame.id<<"\" d=\"M "<<cubics[0].x0<<" "<<cubics[0].y0;
            for(const auto& c:cubics)
                o<<" C "<<c.x1<<" "<<c.y1<<" "<<c.x2<<" "<<c.y2<<" "<<c.x3<<" "<<c.y3;
            if(closed)o<<" Z";
            o<<"\" fill=\"none\" stroke=\"#87c6ff\" stroke-width=\"2\"/>\n";
        }
    }
}
} // namespace

extern "C" {
CNL_ShapeFeatures cnl_shape_features(void){return {1,1,1,1,1,1,0,0,0,0};}
CNL_ShapeLayer* cnl_shape_create(void){
    try {
        auto layer=std::make_unique<CNL_ShapeLayer>();
        layer->doc=cnl_document_create();
        if(!layer->doc)return nullptr;
        return layer.release();
    }catch(...){return nullptr;}
}
void cnl_shape_destroy(CNL_ShapeLayer* s){delete s;}
CNL_NodeId cnl_shape_contents_root(const CNL_ShapeLayer* s){return s?cnl_document_root(s->doc):0;}
CNL_Status cnl_shape_add_group(CNL_ShapeLayer* s,CNL_NodeId parent,const char* name,CNL_NodeId* id){
    if(!s||!id)return CNL_INVALID_ARGUMENT;
    return mutate(s,[&](){return cnl_document_add_group(s->doc,parent,name,id);});
}
CNL_Status cnl_shape_add_path(CNL_ShapeLayer* s,CNL_NodeId parent,const char* name,int closed,const CNL_PathVertex* points,uint32_t count,CNL_NodeId* id){
    if(!s||!id)return CNL_INVALID_ARGUMENT;
    return mutate(s,[&](){return cnl_document_add_path(s->doc,parent,name,closed,points,count,id);});
}
CNL_Status cnl_shape_add_ellipse(CNL_ShapeLayer* s,CNL_NodeId parent,const char* name,double x,double y,double rx,double ry,CNL_NodeId* id){
    if(!s||!id)return CNL_INVALID_ARGUMENT;
    return mutate(s,[&](){return cnl_document_add_ellipse(s->doc,parent,name,x,y,rx,ry,id);});
}
CNL_Status cnl_shape_set_vertex(CNL_ShapeLayer* s,CNL_NodeId path,uint32_t i,const CNL_PathVertex* vertex){
    if(!s||!vertex)return CNL_INVALID_ARGUMENT;
    return mutate(s,[&](){return cnl_document_set_vertex(s->doc,path,i,vertex);});
}
CNL_Status cnl_shape_move_node(CNL_ShapeLayer* s,CNL_NodeId node,CNL_NodeId parent){
    if(!s)return CNL_INVALID_ARGUMENT;
    return mutate(s,[&](){return cnl_document_move_node(s->doc,node,parent);});
}
CNL_Status cnl_shape_get_vertex(const CNL_ShapeLayer* s,CNL_NodeId path,uint32_t i,CNL_PathVertex* vertex){
    if(!s)return CNL_INVALID_ARGUMENT;
    return cnl_document_get_vertex(s->doc,path,i,vertex);
}
uint32_t cnl_shape_undo_depth(const CNL_ShapeLayer* s){return s?static_cast<uint32_t>(s->undo.size()):0;}
uint32_t cnl_shape_redo_depth(const CNL_ShapeLayer* s){return s?static_cast<uint32_t>(s->redo.size()):0;}
CNL_Status cnl_shape_undo(CNL_ShapeLayer* s){return restore(s,true);}
CNL_Status cnl_shape_redo(CNL_ShapeLayer* s){return restore(s,false);}
CNL_Status cnl_shape_archive(const CNL_ShapeLayer* s,void* out,size_t* n){
    if(!s)return CNL_INVALID_ARGUMENT;
    return cnl_document_serialize(s->doc,out,n);
}
CNL_Status cnl_shape_from_archive(const void* input,size_t n,CNL_ShapeLayer** output){
    if(!output)return CNL_INVALID_ARGUMENT;
    *output=nullptr;
    try{
        CNL_Document* doc=nullptr;
        CNL_Status s=cnl_document_deserialize(input,n,&doc);
        if(s!=CNL_OK)return s;
        std::unique_ptr<CNL_Document,void(*)(CNL_Document*)> owned(doc,cnl_document_destroy);
        auto layer=std::make_unique<CNL_ShapeLayer>();
        layer->doc=owned.release();
        *output=layer.release();
        return CNL_OK;
    }catch(...){return CNL_INTERNAL_ERROR;}
}
CNL_Status cnl_shape_svg(const CNL_ShapeLayer* s,char* dst,size_t* n){
    if(!s||!n)return CNL_INVALID_ARGUMENT;
    try{
        std::ostringstream svg;
        svg.imbue(std::locale::classic());
        svg<<std::fixed<<std::setprecision(6);
        svg<<"<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 640 360\">\n";
        svg_tree(s->doc,svg);
        svg<<"</svg>\n";
        const std::string output=svg.str();
        if(output.size()>kSvgMax)return CNL_LIMIT_EXCEEDED;
        const size_t required=output.size()+1,provided=*n;
        *n=required;
        if(!dst||provided<required)return CNL_NO_SPACE;
        std::memcpy(dst,output.c_str(),required);
        return CNL_OK;
    }catch(...){return CNL_INTERNAL_ERROR;}
}
}
