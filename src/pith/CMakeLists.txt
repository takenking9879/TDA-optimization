cmake_minimum_required(VERSION 3.16)
project(pith LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_CXX_COMPILER)
  set(CMAKE_CXX_COMPILER g++)
endif()

find_package(Threads REQUIRED)

add_executable(pith src/main.cpp src/redzed_bridge.cpp)
target_include_directories(pith PRIVATE include)
target_compile_options(pith PRIVATE -O3 -Wall -Wextra)
# I230: RedZeD's own build is -O3 -DNDEBUG. asserts in the vendor TU
# are a real tax on the blobs/sphere reduce path (I229 reduce_ms=313 of 394).
set_source_files_properties(src/redzed_bridge.cpp PROPERTIES COMPILE_FLAGS "-DNDEBUG")
target_link_libraries(pith PRIVATE Threads::Threads)

add_executable(pith_test tests/test_collapse.cpp src/redzed_bridge.cpp)
target_include_directories(pith_test PRIVATE include)
target_compile_options(pith_test PRIVATE -O2 -Wall -Wextra)
target_link_libraries(pith_test PRIVATE Threads::Threads)

enable_testing()
add_test(NAME collapse COMMAND pith_test)
