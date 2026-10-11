cmake_minimum_required(VERSION 3.24)
project(CNLNativeVectorHostProbe LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Local Adobe SDK Examples")
set(CNL_CORE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../native_vector_core" CACHE PATH "CNL independent native vector source")
set(PIPL_PY "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py" CACHE FILEPATH "PiPL generator")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_GeneralPlug.h")
 message(FATAL_ERROR "Adobe AE SDK 25.6 headers missing")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_RC "${CMAKE_CURRENT_BINARY_DIR}/CNLVectorHostBridge_PiPL.rc")
add_custom_command(OUTPUT "${PIPL_RC}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_PY}"
  --cl "${CMAKE_CXX_COMPILER}"
  --sdk "${AE_SDK_EXAMPLES}"
  --source "${CMAKE_CURRENT_SOURCE_DIR}/CNLVectorHostBridge_PiPL.r"
  --output "${PIPL_RC}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/CNLVectorHostBridge_PiPL.r" "${PIPL_PY}"
 VERBATIM)
add_library(CNLNativeVectorHostProbe SHARED
 CNLVectorHostBridge.cpp
 "${CNL_CORE_DIR}/CNLNativeVectorCore.cpp"
 "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
 "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp"
 "${PIPL_RC}")
target_compile_features(CNLNativeVectorHostProbe PRIVATE cxx_std_17)
target_compile_definitions(CNLNativeVectorHostProbe PRIVATE
 MSWindows WIN32 _WINDOWS CNL_VECTOR_CORE_EXPORTS)
target_include_directories(CNLNativeVectorHostProbe PRIVATE
 "${CNL_CORE_DIR}"
 "${AE_SDK_EXAMPLES}/Headers"
 "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win"
 "${AE_SDK_EXAMPLES}/Util")
target_link_libraries(CNLNativeVectorHostProbe PRIVATE Advapi32)
set_target_properties(CNLNativeVectorHostProbe PROPERTIES PREFIX "" SUFFIX ".aex")
