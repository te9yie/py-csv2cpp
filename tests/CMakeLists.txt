cmake_minimum_required(VERSION 3.16)
project(csv2cpp_tests)

include(FetchContent)

# Google Test
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest
    GIT_TAG v1.14.x
    GIT_SHALLOW TRUE)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(${PROJECT_NAME} test_csv2cpp.cpp)
target_compile_features(${PROJECT_NAME} PRIVATE
    cxx_std_20)
target_compile_options(${PROJECT_NAME} PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /utf-8 /GR- /EHa->
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-W -Wall -fno-rtti -fno-exceptions>)
target_link_libraries(${PROJECT_NAME} PRIVATE
    GTest::gtest_main)

include(GoogleTest)
gtest_discover_tests(${PROJECT_NAME})
