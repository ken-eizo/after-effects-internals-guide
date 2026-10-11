cmake_minimum_required(VERSION 3.24)
project(CNLVectorBridgeLab LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Adobe SDK root")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_Effect.h")
  message(FATAL_ERROR "Missing Adobe AE SDK")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_GEN "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py")
foreach(target_name IN ITEMS VectorBridgeAEGP VectorBridgeConsumer)
  set(rc "${CMAKE_CURRENT_BINARY_DIR}/${target_name}_PiPL.rc")
  add_custom_command(OUTPUT "${rc}"
    COMMAND "${Python3_EXECUTABLE}" "${PIPL_GEN}"
       --cl "${CMAKE_CXX_COMPILER}"
       --sdk "${AE_SDK_EXAMPLES}"
       --source "${CMAKE_CURRENT_SOURCE_DIR}/${target_name}_PiPL.r"
       --output "${rc}"
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${target_name}_PiPL.r" "${PIPL_GEN}"
    VERBATIM COMMENT "Generate ${target_name} PiPL")
  add_library("${target_name}" SHARED "${target_name}.cpp" "${rc}")
  target_compile_features("${target_name}" PRIVATE cxx_std_17)
  target_compile_definitions("${target_name}" PRIVATE MSWindows WIN32 _WINDOWS)
  target_include_directories("${target_name}" PRIVATE
    "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
    "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util")
  set_target_properties("${target_name}" PROPERTIES PREFIX "" SUFFIX ".aex")
endforeach()

# Standalone test runner: loads the two actual AEX DLLs under a minimal PICA mock.
add_executable(VectorBridgeHostMock VectorBridgeHostMock.cpp)
target_compile_features(VectorBridgeHostMock PRIVATE cxx_std_17)
target_compile_definitions(VectorBridgeHostMock PRIVATE MSWindows WIN32 _WINDOWS)
target_include_directories(VectorBridgeHostMock PRIVATE
  "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
  "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util")
