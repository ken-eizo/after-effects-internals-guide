#include "ChapeHierarchyRules.h"
#include <algorithm>
#include <utility>

namespace chape {
namespace {
constexpr size_t kMaxTypes=256,kMaxNodes=10000,kMaxDepth=128;
bool validName(const std::string& x) {return !x.empty()&&x.size()<=160;}
}
Hierarchy::Hierarchy(){
    types_.emplace("CNL:Document",Type{"CNL:Document",{},true,Order::Forward});
    nodes_.emplace(Root,Node{Root,0,"CNL:Document","ChapeLayer",{}});
}
Result Hierarchy::registerType(Type type){
    if(!validName(type.matchName))return Result::UnknownType;
    if(types_.count(type.matchName))return Result::DuplicateType;
    if(types_.size()>=kMaxTypes||type.permittedChildren.size()>kMaxTypes)return Result::Limit;
    if(!type.container&&!type.permittedChildren.empty())return Result::NotAContainer;
    for(const auto& allowed:type.permittedChildren)if(!validName(allowed))return Result::UnknownType;
    types_.emplace(type.matchName,std::move(type));
    return Result::Ok;
}
Result Hierarchy::setChildren(const std::string& parentType,std::vector<std::string> allowed){
    const auto it=types_.find(parentType);
    if(it==types_.end())return Result::UnknownType;
    if(!it->second.container)return Result::NotAContainer;
    if(allowed.size()>kMaxTypes)return Result::Limit;
    for(const auto& id:allowed)if(!validName(id))return Result::UnknownType;
    // A schema change must never orphan already-created children.
    for(const auto& item:nodes_){
        if(item.second.type!=parentType)continue;
        for(const uint64_t childId:item.second.children){
            const Node* child=get(childId);
            if(!child || std::find(allowed.begin(),allowed.end(),child->type)==allowed.end())
                return Result::DisallowedChild;
        }
    }
    it->second.permittedChildren=std::move(allowed);
    return Result::Ok;
}
Result Hierarchy::setOrder(const std::string& type,Order order){
    const auto it=types_.find(type);
    if(it==types_.end())return Result::UnknownType;
    if(!it->second.container)return Result::NotAContainer;
    it->second.evaluationOrder=order;return Result::Ok;
}
const Node* Hierarchy::get(uint64_t id) const{
    const auto it=nodes_.find(id);return it==nodes_.end()?nullptr:&it->second;
}
bool Hierarchy::canAdd(uint64_t parent,const std::string& type) const{
    const Node* p=get(parent);
    if(!p||!types_.count(type))return false;
    auto pit=types_.find(p->type);
    if(pit==types_.end()||!pit->second.container)return false;
    const auto& v=pit->second.permittedChildren;
    return std::find(v.begin(),v.end(),type)!=v.end();
}
Result Hierarchy::add(uint64_t parent,const std::string& type,std::string label,uint64_t& newId){
    newId=0;
    if(!get(parent))return Result::InvalidParent;
    if(!types_.count(type))return Result::UnknownType;
    if(!canAdd(parent,type))return Result::DisallowedChild;
    if(nodes_.size()>=kMaxNodes || nextId_==UINT64_MAX)return Result::Limit;
    const uint64_t id=nextId_++;
    nodes_.emplace(id,Node{id,parent,type,std::move(label),{}});
    nodes_.at(parent).children.push_back(id);
    newId=id;
    return Result::Ok;
}
bool Hierarchy::isAncestor(uint64_t possibleAncestor,uint64_t nodeId) const{
    for(size_t n=0;n<=nodes_.size();++n){
        const Node* ptr=get(nodeId);
        if(!ptr)return false;
        if(ptr->id==possibleAncestor)return true;
        if(ptr->parent==0)return false;
        nodeId=ptr->parent;
    }
    return true; // malformed cycle: fail closed
}
Result Hierarchy::reorder(uint64_t node,size_t targetIndex){
    const Node* child=get(node);
    if(!child||child->parent==0)return Result::InvalidParent;
    auto& siblings=nodes_.at(child->parent).children;
    if(targetIndex>=siblings.size())return Result::InvalidPosition;
    auto it=std::find(siblings.begin(),siblings.end(),node);
    if(it==siblings.end())return Result::InvalidParent;
    siblings.erase(it);
    siblings.insert(siblings.begin()+targetIndex,node);
    return Result::Ok;
}
Result Hierarchy::reparent(uint64_t node,uint64_t parent,size_t index){
    const Node* src=get(node);
    if(!src||!src->parent||!get(parent))return Result::InvalidParent;
    if(isAncestor(node,parent))return Result::Cycle;
    if(!canAdd(parent,src->type))return Result::DisallowedChild;
    const auto& dest=nodes_.at(parent).children;
    if(index>dest.size())return Result::InvalidPosition;
    if(src->parent==parent){
        if(index==dest.size())index=dest.size()-1;
        return reorder(node,index);
    }
    const uint64_t oldParent=src->parent;
    auto& old=nodes_.at(oldParent).children;
    const auto it=std::find(old.begin(),old.end(),node);
    if(it==old.end())return Result::InvalidParent;
    old.erase(it);
    nodes_.at(parent).children.insert(nodes_.at(parent).children.begin()+index,node);
    nodes_.at(node).parent=parent;
    return Result::Ok;
}
void Hierarchy::evaluate(uint64_t id,std::vector<std::string>& trace,unsigned depth) const{
    if(depth>kMaxDepth||trace.size()>kMaxNodes*3)return;
    const Node* ptr=get(id);
    if(!ptr)return;
    const auto type=types_.find(ptr->type);
    if(type==types_.end())return;
    if(!type->second.container){
        trace.push_back("emit:"+ptr->type+":"+ptr->label);return;
    }
    trace.push_back("begin:"+ptr->type+":"+ptr->label);
    const auto emit=[&](uint64_t child){evaluate(child,trace,depth+1);};
    if(type->second.evaluationOrder==Order::Forward)
        for(uint64_t child:ptr->children)emit(child);
    else
        for(auto iter=ptr->children.rbegin();iter!=ptr->children.rend();++iter)emit(*iter);
    trace.push_back("end:"+ptr->type+":"+ptr->label);
}
std::vector<std::string> Hierarchy::evaluationTrace() const{
    std::vector<std::string> trace;
    trace.reserve(nodes_.size()*2+1);
    evaluate(Root,trace,0);
    return trace;
}
}
