cmake_minimum_required(VERSION 3.24)
project(CNLPrivateTDBDisposable LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Local Adobe SDK Examples")
set(PIPL_PY "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py" CACHE FILEPATH "Existing PiPL generator")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_GeneralPlug.h")
 message(FATAL_ERROR "Adobe AE 25.6 SDK headers missing")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_RC "${CMAKE_CURRENT_BINARY_DIR}/CNLPrivateTDBDisposable_PiPL.rc")
add_custom_command(OUTPUT "${PIPL_RC}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_PY}"
 --cl "${CMAKE_CXX_COMPILER}"
 --sdk "${AE_SDK_EXAMPLES}"
 --source "${CMAKE_CURRENT_SOURCE_DIR}/CNLPrivateTDBDisposable_PiPL.r"
 --output "${PIPL_RC}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/CNLPrivateTDBDisposable_PiPL.r" "${PIPL_PY}"
 VERBATIM)
add_library(CNLPrivateTDBDisposable SHARED
 CNLPrivateTDBDisposable.cpp
 "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
 "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp"
 "${PIPL_RC}")
target_compile_features(CNLPrivateTDBDisposable PRIVATE cxx_std_17)
target_compile_definitions(CNLPrivateTDBDisposable PRIVATE MSWindows WIN32 _WINDOWS)
target_include_directories(CNLPrivateTDBDisposable PRIVATE
 "${AE_SDK_EXAMPLES}/Headers"
 "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win"
 "${AE_SDK_EXAMPLES}/Util")
target_link_libraries(CNLPrivateTDBDisposable PRIVATE Advapi32)
set_target_properties(CNLPrivateTDBDisposable PROPERTIES PREFIX "" SUFFIX ".aex")
