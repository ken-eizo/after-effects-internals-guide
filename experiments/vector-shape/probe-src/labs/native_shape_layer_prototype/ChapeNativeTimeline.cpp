#include "ChapeNativeTimeline.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <functional>
#include <limits>
#include <set>
#include <utility>
namespace chape::timeline {
namespace {
constexpr size_t MaxTypes=256,MaxNodes=8192,MaxKeys=32768,MaxBlob=16u*1024u*1024u,MaxDepth=128;
bool nameOk(const std::string& s){return !s.empty()&&s.size()<256;}
bool finite(const Value& v){for(double x:v.items)if(!std::isfinite(x))return false;return true;}
bool group(Kind k){return k==Kind::Group;}
bool kindOk(Kind k){return static_cast<unsigned>(k)<=static_cast<unsigned>(Kind::Boolean);}
bool orderOk(Order k){return static_cast<unsigned>(k)<=1;}
bool interpOk(Interpolation k){return static_cast<unsigned>(k)<=1;}
uint32_t hash(const uint8_t* s,size_t n){
 uint32_t h=2166136261u;
 for(size_t i=0;i<n;++i){h^=s[i];h*=16777619u;}
 return h;
}
struct Writer{
 std::vector<uint8_t> bytes;
 void u8(uint8_t x){bytes.push_back(x);}
 void u32(uint32_t x){for(int i=0;i<4;++i)u8(static_cast<uint8_t>(x>>(8*i)));}
 void u64(uint64_t x){for(int i=0;i<8;++i)u8(static_cast<uint8_t>(x>>(8*i)));}
 void str(const std::string& s){u32(static_cast<uint32_t>(s.size()));bytes.insert(bytes.end(),s.begin(),s.end());}
 void value(const Value& v){for(double f:v.items){uint64_t bits=0;std::memcpy(&bits,&f,8);u64(bits);}}
};
struct Reader{
 const uint8_t* data;size_t size;size_t at=0;bool valid=true;
 uint8_t u8(){if(at>=size){valid=false;return 0;}return data[at++];}
 uint32_t u32(){uint32_t x=0;for(int i=0;i<4;++i)x|=uint32_t(u8())<<(8*i);return x;}
 uint64_t u64(){uint64_t x=0;for(int i=0;i<8;++i)x|=uint64_t(u8())<<(8*i);return x;}
 std::string str(){auto n=u32();if(!valid||n>255||n>size-at){valid=false;return {};}auto s=std::string(reinterpret_cast<const char*>(data+at),n);at+=n;return s;}
 Value value(){Value v;for(double& f:v.items){auto bits=u64();std::memcpy(&f,&bits,8);}return v;}
};
}
Document::Document(){
 state_.types.emplace("CNL:Stage",Type{"CNL:Stage",Kind::Group,{},Order::Forward});
 state_.nodes.emplace(Stage,Node{Stage,0,"CNL:Stage","Timeline",{}, {}, {}});
}
const Node* Document::node(uint64_t id)const{
 auto it=state_.nodes.find(id);return it==state_.nodes.end()?nullptr:&it->second;
}
const Type* Document::type(const std::string& name)const{
 auto it=state_.types.find(name);return it==state_.types.end()?nullptr:&it->second;
}
void Document::record(State&& old){
 undo_.push_back(std::move(old));
 if(undo_.size()>MaxHistory)undo_.erase(undo_.begin());
 redo_.clear();
}
Code Document::registerType(Type spec){
 if(!nameOk(spec.matchName)||!kindOk(spec.kind)||!orderOk(spec.order))return Code::Invalid;
 if(type(spec.matchName))return Code::Duplicate;
 if(state_.types.size()>=MaxTypes||spec.allowed.size()>MaxTypes)return Code::Limit;
 if(!group(spec.kind)&&!spec.allowed.empty())return Code::WrongKind;
 for(const auto& x:spec.allowed)if(!nameOk(x))return Code::Invalid;
 auto before=state_;
 state_.types.emplace(spec.matchName,std::move(spec));
 record(std::move(before));return Code::Ok;
}
Code Document::permit(std::string parentType,std::vector<std::string> allowed){
 auto t=type(parentType);
 if(!t)return Code::UnknownType;
 if(!group(t->kind))return Code::WrongKind;
 if(allowed.size()>MaxTypes)return Code::Limit;
 for(const auto& name:allowed)if(!type(name))return Code::UnknownType;
 for(const auto& [id,n]:state_.nodes){
  if(n.type!=parentType)continue;
  for(auto child:n.children){
   auto p=node(child);
   if(!p||std::find(allowed.begin(),allowed.end(),p->type)==allowed.end())return Code::Forbidden;
  }
 }
 if(t->allowed==allowed)return Code::Ok;
 auto before=state_;
 state_.types.at(parentType).allowed=std::move(allowed);
 record(std::move(before));return Code::Ok;
}
Code Document::setOrder(const std::string& name,Order value){
 auto t=type(name);
 if(!t)return Code::UnknownType;
 if(!group(t->kind))return Code::WrongKind;
 if(!orderOk(value))return Code::Invalid;
 if(t->order==value)return Code::Ok;
 auto before=state_;
 state_.types.at(name).order=value;
 record(std::move(before));return Code::Ok;
}
bool Document::canAdd(uint64_t parent,const std::string& child)const{
 auto p=node(parent);if(!p||!type(child))return false;
 auto t=type(p->type);if(!t||!group(t->kind))return false;
 return std::find(t->allowed.begin(),t->allowed.end(),child)!=t->allowed.end();
}
Code Document::add(uint64_t parent,const std::string& matchName,const std::string& label,uint64_t& id){
 id=0;if(!node(parent))return Code::Missing;
 if(!type(matchName))return Code::UnknownType;
 if(!canAdd(parent,matchName))return Code::Forbidden;
 if(state_.nodes.size()>=MaxNodes||state_.nextId==UINT64_MAX||label.size()>255)return Code::Limit;
 auto before=state_;
 id=state_.nextId++;
 state_.nodes.emplace(id,Node{id,parent,matchName,label,{},{},{}});
 state_.nodes.at(parent).children.push_back(id);
 record(std::move(before));return Code::Ok;
}
bool Document::descendant(uint64_t maybeAncestor,uint64_t candidate)const{
 for(size_t i=0;i<=state_.nodes.size();++i){
  if(candidate==maybeAncestor)return true;
  auto p=node(candidate);if(!p||p->parent==0)return false;
  candidate=p->parent;
 }
 return true;
}
Code Document::move(uint64_t id,uint64_t newParent,size_t position){
 auto child=node(id);if(!child||child->parent==0||!node(newParent))return Code::Missing;
 if(descendant(id,newParent))return Code::Cycle;
 if(!canAdd(newParent,child->type))return Code::Forbidden;
 auto currentParent=child->parent;
 const auto& target=state_.nodes.at(newParent).children;
 if(position>target.size())return Code::Range;
 auto before=state_;
 auto& previous=state_.nodes.at(currentParent).children;
 previous.erase(std::find(previous.begin(),previous.end(),id));
 auto& dest=state_.nodes.at(newParent).children;
 if(currentParent==newParent&&position>dest.size())position=dest.size();
 dest.insert(dest.begin()+position,id);
 state_.nodes.at(id).parent=newParent;
 record(std::move(before));return Code::Ok;
}
Code Document::setRawBase(uint64_t id,Value value){
 auto n=node(id);if(!n)return Code::Missing;
 auto t=type(n->type);if(!t||group(t->kind))return Code::WrongKind;
 if(!finite(value))return Code::Invalid;
 auto before=state_;state_.nodes.at(id).base=value;
 record(std::move(before));return Code::Ok;
}
Code Document::setBase(uint64_t id,Value v){return setRawBase(id,v);}
Code Document::setKey(uint64_t id,Key k){
 auto n=node(id);if(!n)return Code::Missing;
 auto t=type(n->type);if(!t||group(t->kind))return Code::WrongKind;
 if(!finite(k.value)||!interpOk(k.mode))return Code::Invalid;
 size_t total=0;for(const auto& [id,node]:state_.nodes)total+=node.keys.size();
 auto& keys=state_.nodes.at(id).keys;
 auto position=std::lower_bound(keys.begin(),keys.end(),k.tick,[](const Key& a,int64_t n){return a.tick<n;});
 if(position==keys.end()||position->tick!=k.tick){
  if(total>=MaxKeys)return Code::Limit;
 }
 auto before=state_;
 auto& mutableKeys=state_.nodes.at(id).keys;
 auto it=std::lower_bound(mutableKeys.begin(),mutableKeys.end(),k.tick,[](const Key& a,int64_t n){return a.tick<n;});
 if(it!=mutableKeys.end()&&it->tick==k.tick)*it=k;
 else mutableKeys.insert(it,k);
 record(std::move(before));return Code::Ok;
}
Code Document::sample(uint64_t id,int64_t time,Value& out)const{
 auto n=node(id);if(!n)return Code::Missing;
 auto t=type(n->type);if(!t||group(t->kind))return Code::WrongKind;
 if(n->keys.empty()){out=n->base;return Code::Ok;}
 auto upper=std::upper_bound(n->keys.begin(),n->keys.end(),time,
     [](int64_t x,const Key& v){return x<v.tick;});
 if(upper==n->keys.begin()){out=upper->value;return Code::Ok;}
 if(upper==n->keys.end()){out=n->keys.back().value;return Code::Ok;}
 const auto& b=*upper;const auto& a=*(upper-1);
 if(a.mode==Interpolation::Hold||t->kind==Kind::Boolean){out=a.value;return Code::Ok;}
 long double num=static_cast<long double>(time)-static_cast<long double>(a.tick);
 long double den=static_cast<long double>(b.tick)-static_cast<long double>(a.tick);
 long double ratio=num/den;
 for(size_t i=0;i<4;++i)out.items[i]=static_cast<double>(a.value.items[i]+ratio*(b.value.items[i]-a.value.items[i]));
 return Code::Ok;
}
void Document::visit(uint64_t id,int64_t tick,std::vector<Event>& out,size_t depth)const{
 if(depth>MaxDepth||out.size()>MaxNodes*2)return;
 auto n=node(id);if(!n)return;
 auto t=type(n->type);if(!t)return;
 if(group(t->kind)){
  out.push_back(Event{id,"begin",n->type,{}});
  if(t->order==Order::Forward)for(auto child:n->children)visit(child,tick,out,depth+1);
  else for(auto i=n->children.rbegin();i!=n->children.rend();++i)visit(*i,tick,out,depth+1);
  out.push_back(Event{id,"end",n->type,{}});
 }else{
  Value v{};if(sample(id,tick,v)==Code::Ok)out.push_back(Event{id,"property",n->type,v});
 }
}
std::vector<Event> Document::evaluate(int64_t tick)const{
 std::vector<Event> result;result.reserve(state_.nodes.size()*2);
 visit(Stage,tick,result,0);return result;
}
Code Document::undo(){
 if(undo_.empty())return Code::EmptyHistory;
 redo_.push_back(std::move(state_));
 if(redo_.size()>MaxHistory)redo_.erase(redo_.begin());
 state_=std::move(undo_.back());undo_.pop_back();return Code::Ok;
}
Code Document::redo(){
 if(redo_.empty())return Code::EmptyHistory;
 undo_.push_back(std::move(state_));
 if(undo_.size()>MaxHistory)undo_.erase(undo_.begin());
 state_=std::move(redo_.back());redo_.pop_back();return Code::Ok;
}
bool Document::validate(const State& s)const{
 if(s.types.empty()||s.types.size()>MaxTypes||s.nodes.empty()||s.nodes.size()>MaxNodes)return false;
 auto base=s.types.find("CNL:Stage");auto root=s.nodes.find(Stage);
 if(base==s.types.end()||!group(base->second.kind)||root==s.nodes.end()||root->second.parent!=0||root->second.type!="CNL:Stage")return false;
 for(const auto& [name,t]:s.types){
  if(name!=t.matchName||!nameOk(name)||!kindOk(t.kind)||!orderOk(t.order))return false;
  if(!group(t.kind)&&!t.allowed.empty())return false;
  for(const auto& allowed:t.allowed)if(s.types.find(allowed)==s.types.end())return false;
 }
 uint64_t maxID=0;size_t keyCount=0;
 for(const auto& [id,n]:s.nodes){
  if(id!=n.id||n.label.size()>255||s.types.find(n.type)==s.types.end())return false;
  maxID=std::max(maxID,id);
  const auto& t=s.types.at(n.type);
  if(group(t.kind)&&!n.keys.empty())return false;
  if(!group(t.kind)&&!n.children.empty())return false;
  if(!finite(n.base))return false;
  keyCount+=n.keys.size();if(keyCount>MaxKeys)return false;
  for(size_t i=0;i<n.keys.size();++i){
   if(!finite(n.keys[i].value)||!interpOk(n.keys[i].mode))return false;
   if(i>0&&n.keys[i-1].tick>=n.keys[i].tick)return false;
  }
  std::set<uint64_t> seen;
  for(auto child:n.children){
   auto c=s.nodes.find(child);if(c==s.nodes.end()||c->second.parent!=id||!seen.insert(child).second)return false;
   if(std::find(t.allowed.begin(),t.allowed.end(),c->second.type)==t.allowed.end())return false;
  }
  if(id!=Stage){
   auto parent=s.nodes.find(n.parent);if(parent==s.nodes.end())return false;
   if(std::find(parent->second.children.begin(),parent->second.children.end(),id)==parent->second.children.end())return false;
  }
 }
 if(s.nextId<=maxID)return false;
 // Every node must be reachable exactly once from the Stage root and no cycles.
 std::set<uint64_t> visited;
 std::function<bool(uint64_t,size_t)> dfs=[&](uint64_t id,size_t depth){
  if(depth>MaxDepth||!visited.insert(id).second)return false;
  for(auto child:s.nodes.at(id).children)if(!dfs(child,depth+1))return false;
  return true;
 };
 return dfs(Stage,0)&&visited.size()==s.nodes.size();
}
std::vector<uint8_t> Document::archive()const{
 if(!validate(state_))return {};
 Writer w;
 const uint8_t magic[8]={'C','N','L','T','L','N','0','1'};
 w.bytes.insert(w.bytes.end(),magic,magic+8);
 w.u32(1);w.u64(state_.nextId);
 w.u32(static_cast<uint32_t>(state_.types.size()));
 for(const auto& [name,t]:state_.types){
  w.str(name);w.u8(static_cast<uint8_t>(t.kind));w.u8(static_cast<uint8_t>(t.order));
  w.u32(static_cast<uint32_t>(t.allowed.size()));
  for(const auto& child:t.allowed)w.str(child);
 }
 w.u32(static_cast<uint32_t>(state_.nodes.size()));
 for(const auto& [id,n]:state_.nodes){
  w.u64(id);w.u64(n.parent);w.str(n.type);w.str(n.label);
  w.u32(static_cast<uint32_t>(n.children.size()));for(auto child:n.children)w.u64(child);
  w.value(n.base);
  w.u32(static_cast<uint32_t>(n.keys.size()));
  for(const auto& key:n.keys){w.u64(static_cast<uint64_t>(key.tick));w.u8(static_cast<uint8_t>(key.mode));w.value(key.value);}
 }
 if(w.bytes.size()+4>MaxBlob)return {};
 auto sum=hash(w.bytes.data(),w.bytes.size());w.u32(sum);
 return std::move(w.bytes);
}
Code Document::restore(const std::vector<uint8_t>& data,Document& output){
 if(data.size()<36||data.size()>MaxBlob)return Code::Corrupt;
 Reader r{data.data(),data.size()-4};
 const uint8_t magic[8]={'C','N','L','T','L','N','0','1'};
 for(auto c:magic)if(r.u8()!=c)return Code::Corrupt;
 if(r.u32()!=1)return Code::Corrupt;
 State tmp;tmp.nextId=r.u64();
 auto tcount=r.u32();if(!r.valid||tcount==0||tcount>MaxTypes)return Code::Corrupt;
 for(uint32_t i=0;i<tcount;++i){
  Type t;t.matchName=r.str();t.kind=static_cast<Kind>(r.u8());t.order=static_cast<Order>(r.u8());
  auto num=r.u32();if(!r.valid||num>MaxTypes)return Code::Corrupt;
  for(uint32_t j=0;j<num;++j)t.allowed.push_back(r.str());
  if(!r.valid||!tmp.types.emplace(t.matchName,t).second)return Code::Corrupt;
 }
 auto count=r.u32();if(!r.valid||count==0||count>MaxNodes)return Code::Corrupt;
 size_t keyCount=0;
 for(uint32_t i=0;i<count;++i){
  Node n;n.id=r.u64();n.parent=r.u64();n.type=r.str();n.label=r.str();
  auto children=r.u32();if(!r.valid||children>MaxNodes)return Code::Corrupt;
  for(uint32_t j=0;j<children;++j)n.children.push_back(r.u64());
  n.base=r.value();
  auto keys=r.u32();keyCount+=keys;if(!r.valid||keyCount>MaxKeys)return Code::Corrupt;
  for(uint32_t j=0;j<keys;++j){
   Key k;k.tick=static_cast<int64_t>(r.u64());k.mode=static_cast<Interpolation>(r.u8());k.value=r.value();n.keys.push_back(k);
  }
  if(!r.valid||!tmp.nodes.emplace(n.id,std::move(n)).second)return Code::Corrupt;
 }
 if(!r.valid||r.at!=r.size)return Code::Corrupt;
 uint32_t actual=0;for(int i=0;i<4;++i)actual|=uint32_t(data[r.size+i])<<(8*i);
 if(actual!=hash(data.data(),r.size))return Code::Corrupt;
 Document test; if(!test.validate(tmp))return Code::Corrupt;
 output.state_=std::move(tmp);output.undo_.clear();output.redo_.clear();
 return Code::Ok;
}
} // namespace chape::timeline
