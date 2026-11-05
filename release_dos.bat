@echo off
REM ===========================================================================
REM release_dos.bat - OpenWatcom 32-bit DOS Build & Packaging Script for jq
REM ===========================================================================

setlocal enabledelayedexpansion

if not exist "C:\usr\WATCOM\binnt" (
    echo Error: OpenWatcom not found at C:\usr\WATCOM
    exit /b 1
)

set "WATCOM=C:\usr\WATCOM"
set "PATH=%WATCOM%\binnt;%WATCOM%\binw;%PATH%"
set "INCLUDE=%WATCOM%\h"

set CMAKE_EXTRA_ARGS=
if exist ..\auto-win-msvc\CMakeLists.txt (
    set CMAKE_EXTRA_ARGS=!CMAKE_EXTRA_ARGS! -DFETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC=..\auto-win-msvc
) else if exist auto-win-msvc\CMakeLists.txt (
    set CMAKE_EXTRA_ARGS=!CMAKE_EXTRA_ARGS! -DFETCHCONTENT_SOURCE_DIR_AUTO_WIN_MSVC=auto-win-msvc
)

set BUILD_DIR=build_dos
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%

echo Configuring 32-bit Protected-Mode DOS build with OpenWatcom...
cmake -G "Watcom WMake" -B %BUILD_DIR% -S . ^
  -DCMAKE_SYSTEM_NAME=DOS ^
  -DCMAKE_SYSTEM_PROCESSOR=I86 ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DBUILD_SHARED_LIBS=OFF ^
  -DBUILD_TESTING=OFF ^
  !CMAKE_EXTRA_ARGS!
if errorlevel 1 exit /b 1

echo Compiling JQ.EXE for 32-bit DOS...
cmake --build %BUILD_DIR% --config Release
if errorlevel 1 exit /b 1

echo Packaging DOS ZIP archive...
cd %BUILD_DIR%
cpack -C Release -G ZIP -D CPACK_PACKAGE_FILE_NAME=jq-1.8.2-dos32
cd ..

echo OpenWatcom 32-bit DOS build complete!
