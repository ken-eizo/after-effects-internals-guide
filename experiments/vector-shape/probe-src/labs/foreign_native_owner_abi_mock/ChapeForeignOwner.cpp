#include "MockHostABI.h"
#include <atomic>
#include <cstdint>
#include <new>
namespace{
std::atomic<int> live{0};
struct ChapeNativeLayer final:MockBEE_Layer {
 std::uint64_t id;
 explicit ChapeNativeLayer(std::uint64_t x):id(x){++live;}
 ChapeNativeLayer(const ChapeNativeLayer& x):id(x.id){++live;}
 ~ChapeNativeLayer() noexcept override{--live;}
 MockTDB_StreamBase* clone() const override{return new ChapeNativeLayer(*this);}
 std::uint32_t typeId() const noexcept override{return 42;}
 std::uint64_t stableId() const noexcept override{return id;}
};
struct CustomNonLayer final:MockTDB_StreamBase{
 CustomNonLayer(){++live;}
 ~CustomNonLayer() noexcept override{--live;}
 MockTDB_StreamBase* clone() const override{return new CustomNonLayer();}
 std::uint32_t typeId() const noexcept override{return 9001;}
};
}
extern "C" {
__declspec(dllexport) std::uint32_t chape_mock_abi_version(){return CHAPE_MOCK_ABI_VERSION;}
__declspec(dllexport) MockTDB_StreamBase* chape_mock_create_layer(std::uint64_t id){
 try{return new ChapeNativeLayer(id);}catch(...){return nullptr;}
}
__declspec(dllexport) MockTDB_StreamBase* chape_mock_create_nonlayer(){
 try{return new CustomNonLayer();}catch(...){return nullptr;}
}
__declspec(dllexport) int chape_mock_live_objects(){return live.load();}
}
