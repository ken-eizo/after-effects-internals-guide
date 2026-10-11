cmake_minimum_required(VERSION 3.24)
project(ShapeLayerAE LANGUAGES CXX RC)
set(AE_SDK_EXAMPLES "E:/ae25.6_61.64bit.AfterEffectsSDK/Examples" CACHE PATH "Local Adobe After Effects SDK Examples directory")
if(NOT EXISTS "${AE_SDK_EXAMPLES}/Headers/AE_GeneralPlug.h")
  message(FATAL_ERROR "AE 25.6 SDK not found: ${AE_SDK_EXAMPLES}")
endif()
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(PIPL_RC "${CMAKE_CURRENT_BINARY_DIR}/ShapeLayerProbe_PiPL.rc")
add_custom_command(
  OUTPUT "${PIPL_RC}"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_pipl.py"
    --cl "${CMAKE_CXX_COMPILER}"
    --sdk "${AE_SDK_EXAMPLES}"
    --source "${CMAKE_CURRENT_SOURCE_DIR}/src/ShapeLayerProbe_PiPL.r"
    --output "${PIPL_RC}"
  DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/ShapeLayerProbe_PiPL.r"
          "${CMAKE_CURRENT_SOURCE_DIR}/tools/build_pipl.py"
  VERBATIM
  COMMENT "Generating AEGP PiPL resource from Adobe SDK PiPLTool"
)
add_library(ShapeLayerAE SHARED
  src/ShapeLayerProbe.cpp
  "${AE_SDK_EXAMPLES}/Util/AEGP_SuiteHandler.cpp"
  "${AE_SDK_EXAMPLES}/Util/MissingSuiteError.cpp"
  "${PIPL_RC}"
)
target_compile_features(ShapeLayerAE PRIVATE cxx_std_17)
target_compile_definitions(ShapeLayerAE PRIVATE MSWindows WIN32 _WINDOWS)
target_include_directories(ShapeLayerAE PRIVATE
  "${AE_SDK_EXAMPLES}/Headers"
  "${AE_SDK_EXAMPLES}/Headers/SP"
  "${AE_SDK_EXAMPLES}/Headers/Win"
  "${AE_SDK_EXAMPLES}/Util"
)
set_target_properties(ShapeLayerAE PROPERTIES PREFIX "" SUFFIX ".aex")
