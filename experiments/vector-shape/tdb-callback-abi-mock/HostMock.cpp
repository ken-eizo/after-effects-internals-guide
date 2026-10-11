#include "HostABI.h"
#include <map>
#include <memory>
#include <mutex>
#include <atomic>
#include <tuple>
#define HOST_EXPORTS
namespace {
struct Entry{
 NativeCreatorLike creator;
 std::unique_ptr<StreamLike> canonical;
};
std::map<std::pair<uint64_t,uint64_t>,Entry> entries;
std::mutex lock;
int layouts=0;
int destruction=0;
using Key=std::pair<uint64_t,uint64_t>;
Key key(const MatchNameLike& n){return {n.guid_a,n.guid_b};}
struct TrackedProxy final : StreamLike {
 StreamLike* real=nullptr;
 explicit TrackedProxy(StreamLike* p):real(p){}
 ~TrackedProxy() override{delete real;++destruction;}
 bool IsLeaf() const override{return real&&real->IsLeaf();}
 StreamLike* GetAsLeaf() override{return real?real->GetAsLeaf():nullptr;}
 void SetupCanonicalLayout() override{if(real){real->SetupCanonicalLayout();++layouts;}}
};
}
extern "C" {
MOCK_API bool MockRegister(const MatchNameLike& name,NativeCreatorLike creator,bool layout){
 std::lock_guard<std::mutex> g(lock);
 if(!creator||entries.count(key(name)))return false;
 // This mimics observed synchronous canonical stream creation.
 auto stream=std::unique_ptr<StreamLike>(creator(name,nullptr,true,77,false));
 if(!stream)return false;
 if(stream->IsLeaf()&&!stream->GetAsLeaf())return false;
 if(layout)stream->SetupCanonicalLayout(),++layouts;
 Entry e; e.creator=std::move(creator);
 e.canonical=std::make_unique<TrackedProxy>(stream.release());
 entries.emplace(key(name),std::move(e));
 return true;
}
MOCK_API bool MockUnregister(const MatchNameLike& name){
 std::lock_guard<std::mutex> g(lock);
 return entries.erase(key(name))!=0;
}
MOCK_API bool MockIsRegistered(const MatchNameLike& name){
 std::lock_guard<std::mutex> g(lock);return entries.count(key(name))!=0;
}
MOCK_API bool MockHasCanonical(const MatchNameLike& name){
 std::lock_guard<std::mutex> g(lock);
 auto it=entries.find(key(name));return it!=entries.end()&&it->second.canonical!=nullptr;
}
MOCK_API size_t MockCount(){std::lock_guard<std::mutex> g(lock);return entries.size();}
MOCK_API int MockCanonicalLayoutCalls(){return layouts;}
MOCK_API int MockStreamDestructors(){return destruction;}
}
