cmake_minimum_required(VERSION 3.24)
project(CNLNativeOwnerAdmission LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "AE SDK")
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_GEN "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py")
set(RES "${CMAKE_CURRENT_BINARY_DIR}/NativeOwnerAdmission_PiPL.rc")
add_custom_command(OUTPUT "${RES}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_GEN}" --cl "${CMAKE_CXX_COMPILER}"
 --sdk "${AE_SDK_EXAMPLES}"
 --source "${CMAKE_CURRENT_SOURCE_DIR}/NativeOwnerAdmission_PiPL.r"
 --output "${RES}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/NativeOwnerAdmission_PiPL.r" "${PIPL_GEN}"
 VERBATIM)
add_library(CNLNativeOwnerAdmission SHARED
 NativeOwnerAdmission.cpp
 "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
 "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp" "${RES}")
target_compile_features(CNLNativeOwnerAdmission PRIVATE cxx_std_17)
target_compile_options(CNLNativeOwnerAdmission PRIVATE /utf-8)
target_compile_definitions(CNLNativeOwnerAdmission PRIVATE MSWindows WIN32 _WINDOWS)
target_include_directories(CNLNativeOwnerAdmission PRIVATE
 "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util")
set_target_properties(CNLNativeOwnerAdmission PROPERTIES PREFIX "" SUFFIX ".aex")
