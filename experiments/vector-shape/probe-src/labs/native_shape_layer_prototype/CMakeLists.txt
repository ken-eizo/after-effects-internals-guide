cmake_minimum_required(VERSION 3.24)
project(CNLNativeShapeLayerPrototype LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Adobe AE SDK Examples")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_GeneralPlug.h")
 message(FATAL_ERROR "After Effects SDK missing")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_GENERATOR "${CMAKE_CURRENT_SOURCE_DIR}/../../tools/build_pipl.py")
set(RC "${CMAKE_CURRENT_BINARY_DIR}/CNLNativeShapeLayer_PiPL.rc")
add_custom_command(OUTPUT "${RC}"
 COMMAND "${Python3_EXECUTABLE}" "${PIPL_GENERATOR}"
 --cl "${CMAKE_CXX_COMPILER}" --sdk "${AE_SDK_EXAMPLES}"
 --source "${CMAKE_CURRENT_SOURCE_DIR}/NativeShapeLayer_PiPL.r"
 --output "${RC}"
 DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/NativeShapeLayer_PiPL.r" "${PIPL_GENERATOR}"
 VERBATIM)
add_library(CNLShapeObjects OBJECT
 "../native_vector_core/CNLNativeVectorCore.cpp"
 CNLShapeRuntime.cpp CNLShapeRuntime.h
 ChapeHierarchyRules.cpp ChapeHierarchyRules.h
 ChapeNativeTimeline.cpp ChapeNativeTimeline.h
 ChapeTimelineABI.cpp ChapeTimelineABI.h)
set_target_properties(CNLShapeObjects PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_compile_features(CNLShapeObjects PRIVATE cxx_std_17)
target_compile_definitions(CNLShapeObjects PRIVATE CNL_VECTOR_CORE_EXPORTS)
target_compile_options(CNLShapeObjects PRIVATE /utf-8)
add_library(CNLNativeShapeLayer SHARED
 NativeShapeLayerPlugin.cpp ChapeHostAdmissionProbe.cpp ChapeTimelineHostDemo.cpp $<TARGET_OBJECTS:CNLShapeObjects>
 "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
 "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp" "${RC}")
target_compile_features(CNLNativeShapeLayer PRIVATE cxx_std_17)
target_compile_definitions(CNLNativeShapeLayer PRIVATE MSWindows WIN32 _WINDOWS)
target_compile_options(CNLNativeShapeLayer PRIVATE /utf-8)
target_include_directories(CNLNativeShapeLayer PRIVATE
 "${AE_SDK_EXAMPLES}/Headers" "${AE_SDK_EXAMPLES}/Headers/SP"
 "${AE_SDK_EXAMPLES}/Headers/Win" "${AE_SDK_EXAMPLES}/Util")
set_target_properties(CNLNativeShapeLayer PROPERTIES PREFIX "" SUFFIX ".aex")
add_executable(CNLNativeShapeRuntimeTest NativeShapeRuntimeTest.cpp
 $<TARGET_OBJECTS:CNLShapeObjects>)
target_compile_features(CNLNativeShapeRuntimeTest PRIVATE cxx_std_17)
target_compile_options(CNLNativeShapeRuntimeTest PRIVATE /utf-8)
add_executable(CNLChapeHierarchyRulesTest ChapeHierarchyRulesTest.cpp ChapeHierarchyRules.cpp)
target_compile_features(CNLChapeHierarchyRulesTest PRIVATE cxx_std_17)
target_compile_options(CNLChapeHierarchyRulesTest PRIVATE /utf-8)
add_executable(CNLNativeTimelineTest ChapeNativeTimelineTest.cpp ChapeNativeTimeline.cpp)
target_compile_features(CNLNativeTimelineTest PRIVATE cxx_std_17)
target_compile_options(CNLNativeTimelineTest PRIVATE /utf-8)
add_executable(CNLTimelineABITest ChapeTimelineABITest.cpp ChapeTimelineABI.cpp ChapeNativeTimeline.cpp)
target_compile_features(CNLTimelineABITest PRIVATE cxx_std_17)
target_compile_options(CNLTimelineABITest PRIVATE /utf-8)
enable_testing()
add_test(NAME NativeTimelineCABI COMMAND CNLTimelineABITest)
add_test(NAME NativeShapeOwnedRuntime COMMAND CNLNativeShapeRuntimeTest)
add_test(NAME ChapeHierarchyRules COMMAND CNLChapeHierarchyRulesTest)
add_test(NAME NativeTypedTimelineGrammar COMMAND CNLNativeTimelineTest)
