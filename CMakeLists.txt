# =============================================================================
# CMakeLists.txt - jq Native Windows (MSVC) & OpenWatcom 32-bit DOS Build
#
# Orchestrates fetching upstream jq (1.8.2) and Oniguruma (6.9.9), build-time
# header generation (version.h, config.h, config_opts.inc, builtin.inc),
# C99-to-C89 AST source transformation via auto-win-msvc, POSIX/BSD/Linux
# polyfill linking, CPack installer packaging (ZIP, NSIS, WiX), and CTest
# functional verification.
#
# Parameters / Cache Variables:
#   JQ_SOURCE_DIR                         - Path to upstream jq source tree.
#   FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC - Path to local auto-win-msvc tree.
#   BUILD_TESTING                         - Enables CTest functional tests.
# =============================================================================

cmake_minimum_required(VERSION 3.24)
cmake_policy(SET CMP0135 NEW)
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)

project(jq-windows VERSION 1.8.2 LANGUAGES C)

set(JQ_VERSION "1.8.2")

set(CMAKE_C_STANDARD 90)
if(NOT (CMAKE_C_COMPILER_ID MATCHES "Watcom"))
    set(CMAKE_C_STANDARD_REQUIRED ON)
endif()
set(CMAKE_C_EXTENSIONS OFF)

include(FetchContent)
include(CTest)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

if(CMAKE_SYSTEM_NAME STREQUAL "DOS" OR (CMAKE_C_COMPILER_ID MATCHES "Watcom" AND NOT WIN32))
    set(AUTO_WIN_MSVC_SINGLE_THREADED ON CACHE BOOL "Single-threaded DOS mode" FORCE)
    set(JQ_TARGET_DOS TRUE)
else()
    set(JQ_TARGET_DOS FALSE)
endif()

set(BUILD_TESTING_SAVED "${BUILD_TESTING}")
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)

# -----------------------------------------------------------------------------
# 1. Fetch Oniguruma (Regular Expression Engine)
# -----------------------------------------------------------------------------
add_compile_definitions(inline=__inline)
set(ENABLE_POSIX_API OFF CACHE BOOL "" FORCE)
set(ENABLE_BINARY_COMPATIBLE_POSIX_API OFF CACHE BOOL "" FORCE)
set(INSTALL_DOCUMENTATION OFF CACHE BOOL "" FORCE)
set(INSTALL_EXAMPLES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    oniguruma
    URL https://github.com/kkos/oniguruma/releases/download/v6.9.9/onig-6.9.9.tar.gz
)
FetchContent_MakeAvailable(oniguruma)

# -----------------------------------------------------------------------------
# 2. Load auto-win-msvc Compatibility Layer
# -----------------------------------------------------------------------------
if(NOT DEFINED FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/auto-win-msvc/CMakeLists.txt")
        get_filename_component(_awm_dir "${CMAKE_CURRENT_SOURCE_DIR}/auto-win-msvc" ABSOLUTE)
        set(FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC "${_awm_dir}" CACHE PATH "" FORCE)
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../auto-win-msvc/CMakeLists.txt")
        get_filename_component(_awm_dir "${CMAKE_CURRENT_SOURCE_DIR}/../auto-win-msvc" ABSOLUTE)
        set(FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC "${_awm_dir}" CACHE PATH "" FORCE)
    endif()
endif()

FetchContent_Declare(
    auto_win_msvc
    GIT_REPOSITORY https://github.com/SamuelMarks/auto-win-msvc.git
    GIT_TAG        master
)
FetchContent_MakeAvailable(auto_win_msvc)

# -----------------------------------------------------------------------------
# 3. Upstream jq Source Location Discovery
# -----------------------------------------------------------------------------
if(NOT DEFINED JQ_SOURCE_DIR)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/jq/src/builtin.jq")
        get_filename_component(JQ_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/jq" ABSOLUTE)
    elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/../jq/src/builtin.jq")
        get_filename_component(JQ_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../jq" ABSOLUTE)
    endif()
endif()

if(NOT DEFINED JQ_SOURCE_DIR OR NOT EXISTS "${JQ_SOURCE_DIR}/src/builtin.jq")
    FetchContent_Declare(
        jq_upstream
        URL https://github.com/jqlang/jq/releases/download/jq-1.8.2/jq-1.8.2.tar.gz
    )
    FetchContent_MakeAvailable(jq_upstream)
    set(JQ_SOURCE_DIR "${jq_upstream_SOURCE_DIR}")
endif()

set(BUILD_TESTING "${BUILD_TESTING_SAVED}" CACHE BOOL "" FORCE)

# -----------------------------------------------------------------------------
# 4. Generate Build-Time Headers & Transform C99 Sources
# -----------------------------------------------------------------------------
include("${auto_win_msvc_SOURCE_DIR}/cmake/AutoWinMsvcTransform.cmake")

set(JQ_GEN_DIR "${CMAKE_CURRENT_BINARY_DIR}/jq_generated")
file(MAKE_DIRECTORY "${JQ_GEN_DIR}")

execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m scripts.generate_jq_headers
            "--builtin-jq" "${JQ_SOURCE_DIR}/src/builtin.jq"
            "--out-dir" "${JQ_GEN_DIR}"
            "--version" "${JQ_VERSION}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    RESULT_VARIABLE _builtin_rc
)
if(NOT _builtin_rc EQUAL 0)
    message(FATAL_ERROR "Failed to generate jq headers and builtin.inc")
endif()

set(JQ_RAW_SOURCES
    "${JQ_SOURCE_DIR}/src/builtin.c"
    "${JQ_SOURCE_DIR}/src/bytecode.c"
    "${JQ_SOURCE_DIR}/src/compile.c"
    "${JQ_SOURCE_DIR}/src/execute.c"
    "${JQ_SOURCE_DIR}/src/jq_test.c"
    "${JQ_SOURCE_DIR}/src/jv.c"
    "${JQ_SOURCE_DIR}/src/jv_alloc.c"
    "${JQ_SOURCE_DIR}/src/jv_aux.c"
    "${JQ_SOURCE_DIR}/src/jv_dtoa.c"
    "${JQ_SOURCE_DIR}/src/jv_dtoa_tsd.c"
    "${JQ_SOURCE_DIR}/src/jv_file.c"
    "${JQ_SOURCE_DIR}/src/jv_parse.c"
    "${JQ_SOURCE_DIR}/src/jv_print.c"
    "${JQ_SOURCE_DIR}/src/jv_unicode.c"
    "${JQ_SOURCE_DIR}/src/lexer.c"
    "${JQ_SOURCE_DIR}/src/linker.c"
    "${JQ_SOURCE_DIR}/src/locfile.c"
    "${JQ_SOURCE_DIR}/src/main.c"
    "${JQ_SOURCE_DIR}/src/parser.c"
    "${JQ_SOURCE_DIR}/src/util.c"
    "${JQ_SOURCE_DIR}/vendor/decNumber/decContext.c"
    "${JQ_SOURCE_DIR}/vendor/decNumber/decNumber.c"
)

auto_win_msvc_transform_sources(
    OUTPUT_VAR JQ_TRANSFORMED_SOURCES
    SOURCES ${JQ_RAW_SOURCES}
    INCLUDE_DIRS "${JQ_SOURCE_DIR}/src" "${JQ_SOURCE_DIR}/vendor/decNumber"
)

add_executable(jq ${JQ_TRANSFORMED_SOURCES})
if(CMAKE_C_COMPILER_ID MATCHES "Watcom")
    target_compile_options(jq PRIVATE -za99)
else()
    set_target_properties(jq PROPERTIES C_STANDARD 99 C_EXTENSIONS ON)
endif()

target_include_directories(jq PRIVATE
    "${JQ_GEN_DIR}"
    "${JQ_SOURCE_DIR}/src"
    "${JQ_SOURCE_DIR}/vendor"
    "${JQ_SOURCE_DIR}/vendor/decNumber"
    "${oniguruma_SOURCE_DIR}/src"
    "${auto_win_msvc_SOURCE_DIR}/include"
)

target_compile_definitions(jq PRIVATE
    HAVE_CONFIG_H=1
    HAVE_LIBONIG=1
    USE_DECNUM=1
    IEEE_8087=1
    ONIG_STATIC=1
    HAVE_STRPTIME=1
    HAVE_GMTIME_R=1
    HAVE_LOCALTIME_R=1
    HAVE_GETTIMEOFDAY=1
    HAVE_ISATTY=1
    HAVE_SETENV=1
    HAVE_PTHREAD_KEY_CREATE=1
    HAVE_PTHREAD_ONCE=1
    posix_fopen=jq_posix_fopen
)

if(JQ_TARGET_DOS)
    target_compile_definitions(jq PRIVATE
        HAVE_FORK=0
        HAVE_PIPE=0
        _SINGLE_THREAD=1
    )
endif()

target_link_libraries(jq PRIVATE
    onig
    posix-core
    posix-time
    posix-libgen
    posix-stat
    posix-pthread
    posix-stdint
    posix-inttypes
    posix-stdbool
    posix-alloca
    posix-types
    bsd-string
    linux-getopt
)

if(WIN32)
    target_link_libraries(jq PRIVATE shlwapi)
endif()

# -----------------------------------------------------------------------------
# 5. Install Rules & CPack Configuration
# -----------------------------------------------------------------------------
install(TARGETS jq RUNTIME DESTINATION bin)
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/README.md")
    install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/README.md" DESTINATION .)
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-APACHE")
    install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-APACHE" DESTINATION .)
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-MIT")
    install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-MIT" DESTINATION .)
endif()
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-CC0")
    install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-CC0" DESTINATION .)
endif()

include("${CMAKE_CURRENT_SOURCE_DIR}/CPackConfig.cmake")
include("${CMAKE_CURRENT_SOURCE_DIR}/CPackSourceConfig.cmake")
include(CPack)

# -----------------------------------------------------------------------------
# 6. CTest Functional Verification Suite
# -----------------------------------------------------------------------------
if(BUILD_TESTING)
    add_test(NAME jq_version COMMAND jq --version)
    add_test(NAME jq_null_input COMMAND jq -n "{a: 1, b: [2, 3]}")
    add_test(NAME jq_math_filter COMMAND jq -n "[1, 2, 3] | map(. * 2) | add")
    add_test(NAME jq_iso8601_date COMMAND jq -n "[\"2026-11-05T14:30:45Z\"][0] | fromdateiso8601")
    add_test(NAME jq_regex_test COMMAND jq -e -n "[\"hello-123\"][0] | test(\"^[a-z]+-[0-9]+$\")")
endif()
