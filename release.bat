@echo off
REM ===========================================================================
REM release.bat - Native Windows MSVC Build, Test, and Packaging Script for jq
REM ===========================================================================

setlocal enabledelayedexpansion

set JQ_REF=%~1
if "%JQ_REF%"=="" set JQ_REF=jq-1.8.2

echo ==============================================
echo Building jq Windows Release (%JQ_REF%)
echo ==============================================

set CMAKE_EXTRA_ARGS=

if exist ..\auto-win-msvc\CMakeLists.txt (
    echo Using local ..\auto-win-msvc repository...
    set CMAKE_EXTRA_ARGS=!CMAKE_EXTRA_ARGS! -DFETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC=..\auto-win-msvc
) else if exist auto-win-msvc\CMakeLists.txt (
    set CMAKE_EXTRA_ARGS=!CMAKE_EXTRA_ARGS! -DFETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC=auto-win-msvc
)

set BUILD_DIR=build_release
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%

echo Configuring with CMake...
cmake -B %BUILD_DIR% -S . -DCMAKE_BUILD_TYPE=Release !CMAKE_EXTRA_ARGS!
if errorlevel 1 exit /b 1

echo Compiling jq Release...
cmake --build %BUILD_DIR% --config Release
if errorlevel 1 exit /b 1

echo Testing jq...
ctest --test-dir %BUILD_DIR% -C Release --output-on-failure
if errorlevel 1 exit /b 1

echo Packaging with CPack...
cd %BUILD_DIR%
cpack -C Release -G ZIP
cpack -C Release -G NSIS
cpack -C Release -G WIX
cd ..

echo Build and packaging complete!
