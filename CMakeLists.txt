# =============================================================================
# CMakeLists.txt - jq Native Windows (MSVC) & OpenWatcom 32-bit DOS Build
#
# Orchestrates fetching upstream jq (1.8.2) and Oniguruma (6.9.9), declarative
# patch application, build-time header generation (version.h, config.h,
# config_opts.inc, builtin.inc), C99-to-C89 AST source transformation via
# auto-win-msvc, POSIX/BSD/Linux polyfill linking, CPack installer packaging
# (ZIP, NSIS, WiX), and CTest functional verification.
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

set(_saved_build_shared_libs "${BUILD_SHARED_LIBS}")
set(_saved_build_testing "${BUILD_TESTING}")
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(BUILD_SHARED_LIBS OFF)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF)
set(AUTO_WIN_MSVC_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(AUTO_WIN_MSVC_BUILD_TESTING OFF)

# -----------------------------------------------------------------------------
# 1. Fetch Oniguruma (Regular Expression Engine)
# -----------------------------------------------------------------------------
add_compile_definitions(inline=__inline)
set(ENABLE_POSIX_API OFF CACHE BOOL "" FORCE)
set(ENABLE_BINARY_COMPATIBLE_POSIX_API OFF CACHE BOOL "" FORCE)
set(INSTALL_DOCUMENTATION OFF CACHE BOOL "" FORCE)
set(INSTALL_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_TEST OFF CACHE BOOL "" FORCE)
set(BUILD_TEST OFF)
FetchContent_Declare(
    oniguruma
    URL https://github.com/kkos/oniguruma/releases/download/v6.9.9/onig-6.9.9.tar.gz
)
FetchContent_MakeAvailable(oniguruma)
target_compile_definitions(onig PUBLIC ONIG_STATIC=1)

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
if(DEFINED FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC AND NOT DEFINED FETCHCONTENT_SOURCE_DIR_AUTO-WIN-MSVC)
    set(FETCHCONTENT_SOURCE_DIR_AUTO-WIN-MSVC "${FETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC}" CACHE PATH "" FORCE)
endif()

if(JQ_TARGET_DOS)
    add_compile_definitions(ETIMEDOUT=60 EWOULDBLOCK=18)
endif()

FetchContent_Declare(
    auto_win_msvc
    GIT_REPOSITORY https://github.com/SamuelMarks/auto-win-msvc.git
    GIT_TAG        e12ccc1e1657eb8d230d7c9d0e9d5ae4f8072326
)
FetchContent_MakeAvailable(auto_win_msvc)

if(JQ_TARGET_DOS)
    if(TARGET auto-win-msvc)
        set_target_properties(auto-win-msvc PROPERTIES EXCLUDE_FROM_ALL TRUE)
    endif()
    set(JQ_DOS_FWD_DIR "${CMAKE_CURRENT_BINARY_DIR}/dos_posix_fwd")
    file(MAKE_DIRECTORY "${JQ_DOS_FWD_DIR}/sys" "${JQ_DOS_FWD_DIR}/bsd")
    foreach(_hdr
        posix-core/include/posix-core.h
        posix-time/include/posix-time.h
        posix-libgen/include/posix-libgen.h
        posix-stat/include/posix-stat.h
        posix-pthread/include/posix-pthread.h
        posix-stdint/include/posix-stdint.h
        posix-inttypes/include/posix-inttypes.h
        posix-stdbool/include/posix-stdbool.h
        posix-types/include/posix-types.h
        linux-getopt/include/linux-getopt.h
    )
        configure_file("${auto_win_msvc_SOURCE_DIR}/${_hdr}" "${JQ_DOS_FWD_DIR}/" COPYONLY)
    endforeach()
    configure_file(
        "${auto_win_msvc_SOURCE_DIR}/bsd-string/include/bsd/string.h"
        "${JQ_DOS_FWD_DIR}/bsd/string.h"
        COPYONLY
    )
    file(WRITE "${JQ_DOS_FWD_DIR}/sys/time.h" "#include \"posix-time.h\"\n")
    file(WRITE "${JQ_DOS_FWD_DIR}/libgen.h" "#include \"posix-libgen.h\"\n")
    file(WRITE "${JQ_DOS_FWD_DIR}/getopt.h" "#include \"linux-getopt.h\"\n")
    file(WRITE "${JQ_DOS_FWD_DIR}/pthread.h"
        "#include <sys/types.h>\n#ifdef SCHED_PARAM_DEFINED\n#ifndef _SCHED_PARAM_DEFINED\n#define _SCHED_PARAM_DEFINED 1\n#endif\n#endif\n#include \"posix-pthread.h\"\n"
    )
    add_library(jq_dos_compat STATIC
        "${auto_win_msvc_SOURCE_DIR}/posix-core/src/posix-core.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-time/src/posix-time.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-libgen/src/posix-libgen.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-stat/src/posix-stat.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-pthread/src/posix-pthread.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-stdint/src/posix-stdint.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-inttypes/src/posix-inttypes.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-stdbool/src/posix-stdbool.c"
        "${auto_win_msvc_SOURCE_DIR}/posix-types/src/posix-types.c"
        "${auto_win_msvc_SOURCE_DIR}/bsd-string/src/bsd_string.c"
        "${auto_win_msvc_SOURCE_DIR}/linux-getopt/src/linux-getopt.c"
    )
    target_include_directories(jq_dos_compat PUBLIC
        "${JQ_DOS_FWD_DIR}"
        "${auto_win_msvc_SOURCE_DIR}/include"
    )
    target_compile_definitions(jq_dos_compat PRIVATE
        _SINGLE_THREAD=1
        AUTO_WIN_MSVC_MEGA_LIBRARY=1
    )
endif()

# -----------------------------------------------------------------------------
# 3. Upstream jq Source Location Discovery & Declarative Patching
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

set(JQ_PATCH_STAMP "${CMAKE_CURRENT_BINARY_DIR}/jq_patches.stamp")
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -m scripts.apply_patches
            "${JQ_SOURCE_DIR}"
            "${CMAKE_CURRENT_SOURCE_DIR}/patches"
            "--stamp" "${JQ_PATCH_STAMP}"
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    RESULT_VARIABLE _patch_rc
)
if(NOT _patch_rc EQUAL 0)
    message(FATAL_ERROR "Failed to apply jq compatibility patches via scripts/apply_patches.py")
endif()

set(BUILD_SHARED_LIBS "${_saved_build_shared_libs}")
set(BUILD_TESTING "${_saved_build_testing}" CACHE BOOL "" FORCE)
set(BUILD_TESTING "${_saved_build_testing}")

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
    target_compile_options(jq PRIVATE
        -za99
        -ze
        -aa
        -fi=${JQ_GEN_DIR}/config.h
        -fi=${JQ_DOS_FWD_DIR}/posix-core.h
    )
    target_link_options(jq PRIVATE option stack=524288)
elseif(MSVC)
    target_compile_options(jq PRIVATE /W0 /FI${JQ_GEN_DIR}/config.h)
else()
    set_target_properties(jq PROPERTIES C_STANDARD 99 C_EXTENSIONS ON)
    target_compile_options(jq PRIVATE -w -include "${JQ_GEN_DIR}/config.h")
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
    HAVE_STRFTIME=1
    HAVE_GMTIME=1
    HAVE_GMTIME_R=1
    HAVE_LOCALTIME=1
    HAVE_LOCALTIME_R=1
    HAVE_GETTIMEOFDAY=1
    HAVE_ISATTY=1
    HAVE_SETENV=1
    HAVE_SETLOCALE=1
    HAVE_ATEXIT=1
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
    target_link_libraries(jq PRIVATE
        onig
        jq_dos_compat
    )
else()
    target_link_libraries(jq PRIVATE
        onig
        auto-win-msvc
    )
endif()

if(WIN32)
    target_link_libraries(jq PRIVATE shlwapi)
endif()

# -----------------------------------------------------------------------------
# 5. Install Rules & CPack Configuration
# -----------------------------------------------------------------------------
install(TARGETS jq RUNTIME DESTINATION bin)
if(JQ_TARGET_DOS AND DEFINED ENV{WATCOM})
    if(EXISTS "$ENV{WATCOM}/binw/dos32a.exe")
        install(FILES "$ENV{WATCOM}/binw/dos32a.exe" DESTINATION bin)
    endif()
    if(EXISTS "$ENV{WATCOM}/binw/dos4gw.exe")
        install(FILES "$ENV{WATCOM}/binw/dos4gw.exe" DESTINATION bin)
    endif()
endif()
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
    add_test(NAME jq_iso8601_date COMMAND jq -n "1793889045 | todateiso8601 | fromdateiso8601")
    add_test(NAME jq_regex_test COMMAND jq -e -n "123 | tostring | test(\"^[0-9]+$\")")
endif()
