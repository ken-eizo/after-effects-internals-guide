#pragma once
// HOST ABI SIMULATOR: this header is NOT Adobe BEE or TDB.
// It models necessary C++ cross-DLL RTTI, virtual clone and owner lifetime.
#include <cstdint>
#ifdef _WIN32
 #ifdef CHAPE_MOCK_HOST_ABI_BUILD
  #define MOCK_HOST_API __declspec(dllexport)
 #else
  #define MOCK_HOST_API __declspec(dllimport)
 #endif
#else
 #define MOCK_HOST_API
#endif
struct MOCK_HOST_API MockTDB_StreamBase {
 virtual ~MockTDB_StreamBase() noexcept;
 virtual MockTDB_StreamBase* clone() const =0;
 virtual std::uint32_t typeId() const noexcept =0;
};
struct MOCK_HOST_API MockBEE_Layer : MockTDB_StreamBase {
 ~MockBEE_Layer() noexcept override;
 virtual std::uint64_t stableId() const noexcept =0;
};
inline constexpr std::uint32_t CHAPE_MOCK_ABI_VERSION=0x00010001u;
