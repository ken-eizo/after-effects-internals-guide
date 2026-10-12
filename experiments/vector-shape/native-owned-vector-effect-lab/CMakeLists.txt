cmake_minimum_required(VERSION 3.24)
project(CNLOwnedVectorDocumentEffect LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Local Adobe AE SDK 25.6")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_Effect.h")
 message(FATAL_ERROR "Adobe AE SDK headers missing")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_GEN "${CMAKE_CURRENT_SOURCE_DIR}/build_pipl.py")
set(GENERATED_RC "${CMAKE_CURRENT_BINARY_DIR}/CNLOwnedVectorEffect_PiPL.rc")
add_custom_command(OUTPUT "${GENERATED_RC}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_GEN}"
    --cl "${CMAKE_CXX_COMPILER}" --sdk "${AE_SDK_EXAMPLES}"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/CNLOwnedVectorEffect_PiPL.r"
    --output "${GENERATED_RC}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/CNLOwnedVectorEffect_PiPL.r" "${PIPL_GEN}"
 VERBATIM)
add_library(CNLOwnedVectorEffect SHARED
 CNLOwnedVectorEffect.cpp
 CNLNativeVectorCore.cpp
 "${GENERATED_RC}")
target_include_directories(CNLOwnedVectorEffect PRIVATE
 "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util"
 "${CMAKE_CURRENT_SOURCE_DIR}")
target_compile_definitions(CNLOwnedVectorEffect PRIVATE
 MSWindows WIN32 _WINDOWS CNL_VECTOR_CORE_EXPORTS)
target_compile_features(CNLOwnedVectorEffect PRIVATE cxx_std_17)
set_target_properties(CNLOwnedVectorEffect PROPERTIES PREFIX "" SUFFIX ".aex")

add_executable(OwnedVectorHostMock OwnedVectorHostMock.cpp)
target_include_directories(OwnedVectorHostMock PRIVATE
 "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util")
target_compile_features(OwnedVectorHostMock PRIVATE cxx_std_17)
target_compile_definitions(OwnedVectorHostMock PRIVATE MSWindows WIN32 _WINDOWS)
enable_testing()
add_test(NAME OwnedVectorEffectPublicHostMock
 COMMAND "$<TARGET_FILE:OwnedVectorHostMock>" "$<TARGET_FILE:CNLOwnedVectorEffect>")
