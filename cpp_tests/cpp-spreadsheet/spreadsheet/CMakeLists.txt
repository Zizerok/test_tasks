cmake_minimum_required(VERSION 3.8 FATAL_ERROR)
project(spreadsheet)

set(CMAKE_CXX_STANDARD 17)
if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    set(
        CMAKE_CXX_FLAGS_DEBUG
        "${CMAKE_CXX_FLAGS_DEBUG} /JMC"
    )
else()
    set(
        CMAKE_CXX_FLAGS
        "${CMAKE_CXX_FLAGS} -Wall -Wextra -pedantic -Wno-unused-parameter -Wno-implicit-fallthrough"
    )
endif()

set(
    ANTLR_EXECUTABLE
    "${CMAKE_CURRENT_SOURCE_DIR}/antlr-4.13.2-complete.jar"
    CACHE FILEPATH
    "Path to the ANTLR complete JAR"
)
set(
    ANTLR4_RUNTIME_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/antlr4_runtime"
    CACHE PATH
    "Path to the ANTLR4 C++ runtime source directory"
)

if(NOT EXISTS "${ANTLR_EXECUTABLE}")
    message(FATAL_ERROR
        "ANTLR JAR not found: ${ANTLR_EXECUTABLE}. "
        "Pass -DANTLR_EXECUTABLE=<path-to-antlr-complete.jar>."
    )
endif()

if(NOT EXISTS "${ANTLR4_RUNTIME_DIR}/CMakeLists.txt")
    message(FATAL_ERROR
        "ANTLR4 C++ runtime not found: ${ANTLR4_RUNTIME_DIR}. "
        "Pass -DANTLR4_RUNTIME_DIR=<path-to-antlr4-runtime-source>."
    )
endif()

include(${CMAKE_CURRENT_SOURCE_DIR}/FindANTLR.cmake)

add_definitions(
    -DANTLR4CPP_STATIC
    -D_SILENCE_ALL_CXX17_DEPRECATION_WARNINGS
)

set(WITH_STATIC_CRT OFF CACHE BOOL "Visual C++ static CRT for ANTLR" FORCE)
add_subdirectory(${ANTLR4_RUNTIME_DIR} antlr4_runtime_build)

antlr_target(FormulaParser Formula.g4 LEXER PARSER LISTENER)

include_directories(
    ${ANTLR4_INCLUDE_DIRS}
    ${ANTLR_FormulaParser_OUTPUT_DIR}
    ${ANTLR4_RUNTIME_DIR}/runtime/src
)

file(GLOB sources
    *.cpp
    *.h
)

add_executable(
    spreadsheet
    ${ANTLR_FormulaParser_CXX_OUTPUTS}
    ${sources}
)

target_link_libraries(spreadsheet antlr4_static)

option(ENABLE_ASAN "Enable AddressSanitizer for the spreadsheet target" OFF)
if(ENABLE_ASAN)
    if(MSVC)
        target_compile_options(spreadsheet PRIVATE /fsanitize=address)
        target_compile_options(antlr4_static PRIVATE /fsanitize=address)
    else()
        target_compile_options(spreadsheet PRIVATE -fsanitize=address -fno-omit-frame-pointer)
        target_link_options(spreadsheet PRIVATE -fsanitize=address)
    endif()
endif()

if(MSVC)
    target_compile_options(antlr4_static PRIVATE /W0)
endif()

install(
    TARGETS spreadsheet
    DESTINATION bin
    EXPORT spreadsheet
)

set_directory_properties(PROPERTIES VS_STARTUP_PROJECT spreadsheet)
