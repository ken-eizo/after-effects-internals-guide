cmake_minimum_required(VERSION 3.24)
project(CNLNativeEditablePathBridge LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "AE SDK root")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_GeneralPlug.h")
  message(FATAL_ERROR "Required AE SDK 25.6 not found")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_GEN "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py")
set(RC "${CMAKE_CURRENT_BINARY_DIR}/NativeEditablePathBridge_PiPL.rc")
add_custom_command(OUTPUT "${RC}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_GEN}"
   --cl "${CMAKE_CXX_COMPILER}" --sdk "${AE_SDK_EXAMPLES}"
   --source "${CMAKE_CURRENT_SOURCE_DIR}/NativeEditablePathBridge_PiPL.r"
   --output "${RC}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/NativeEditablePathBridge_PiPL.r" "${PIPL_GEN}"
 VERBATIM COMMENT "Generate AEGP PiPL")
add_library(NativeEditablePathBridge SHARED
 NativeEditablePathBridge.cpp
 "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
 "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp"
 "${RC}")
target_compile_features(NativeEditablePathBridge PRIVATE cxx_std_17)
target_compile_definitions(NativeEditablePathBridge PRIVATE MSWindows WIN32 _WINDOWS)
target_include_directories(NativeEditablePathBridge PRIVATE
 "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util"
 "${CMAKE_CURRENT_SOURCE_DIR}")
set_target_properties(NativeEditablePathBridge PROPERTIES PREFIX "" SUFFIX ".aex")
