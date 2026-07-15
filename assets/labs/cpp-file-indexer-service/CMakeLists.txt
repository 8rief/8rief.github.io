cmake_minimum_required(VERSION 3.24)
project(cpp_file_indexer_service VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)
set(FETCHCONTENT_QUIET OFF)

FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.12.0
)
FetchContent_Declare(
  CLI11
  GIT_REPOSITORY https://github.com/CLIUtils/CLI11.git
  GIT_TAG v2.5.0
)
FetchContent_Declare(
  spdlog
  GIT_REPOSITORY https://github.com/gabime/spdlog.git
  GIT_TAG v1.15.3
)
FetchContent_Declare(
  cpp_httplib
  GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
  GIT_TAG v0.20.0
)
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG v3.8.1
)
FetchContent_MakeAvailable(nlohmann_json CLI11 spdlog cpp_httplib Catch2)

add_library(file_indexer
  src/indexer.cpp
)
target_include_directories(file_indexer PUBLIC include)
target_link_libraries(file_indexer PUBLIC nlohmann_json::nlohmann_json)
target_compile_options(file_indexer PRIVATE -Wall -Wextra -Wpedantic)

add_executable(file-indexer src/main.cpp)
target_include_directories(file-indexer PRIVATE ${cpp_httplib_SOURCE_DIR})
target_link_libraries(file-indexer PRIVATE file_indexer CLI11::CLI11 spdlog::spdlog)
target_compile_options(file-indexer PRIVATE -Wall -Wextra -Wpedantic)

include(CTest)
if(BUILD_TESTING)
  add_executable(file_indexer_tests tests/test_indexer.cpp)
  target_link_libraries(file_indexer_tests PRIVATE file_indexer Catch2::Catch2WithMain)
  target_compile_options(file_indexer_tests PRIVATE -Wall -Wextra -Wpedantic)
  target_compile_definitions(file_indexer_tests PRIVATE CMAKE_SOURCE_DIR="${CMAKE_SOURCE_DIR}")
  include(Catch)
  catch_discover_tests(file_indexer_tests)
endif()
