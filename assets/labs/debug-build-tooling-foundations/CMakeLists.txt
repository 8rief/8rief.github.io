cmake_minimum_required(VERSION 3.24)
project(DebugBuildToolingFoundations LANGUAGES CXX)

option(ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(debuglab src/debug_lab.cpp)
target_include_directories(debuglab PUBLIC src)
target_compile_options(debuglab PRIVATE -Wall -Wextra -Wpedantic -Werror)

add_executable(debug_lab_cli src/debug_lab_cli.cpp)
target_link_libraries(debug_lab_cli PRIVATE debuglab)
target_compile_options(debug_lab_cli PRIVATE -Wall -Wextra -Wpedantic -Werror)

add_executable(debug_lab_tests tests/test_debug_lab.cpp)
target_link_libraries(debug_lab_tests PRIVATE debuglab)
target_compile_options(debug_lab_tests PRIVATE -Wall -Wextra -Wpedantic -Werror)

if(ENABLE_SANITIZERS)
  foreach(target debuglab debug_lab_cli debug_lab_tests)
    target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
  endforeach()
endif()

include(CTest)
if(BUILD_TESTING)
  add_test(NAME debug_lab_tests COMMAND debug_lab_tests)
endif()
