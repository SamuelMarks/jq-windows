# =============================================================================
# CPackConfig.cmake - Binary Package Configuration for jq Windows & DOS
#
# Configures CPack to produce standalone portable ZIP archives, NSIS (.exe),
# and WiX (.msi) Windows installers containing the compiled jq executable
# and licenses.
# =============================================================================

set(CPACK_PACKAGE_NAME "jq")
set(CPACK_PACKAGE_VENDOR "jqlang")
set(CPACK_PACKAGE_VERSION "1.8.2")
set(CPACK_PACKAGE_VERSION_MAJOR "1")
set(CPACK_PACKAGE_VERSION_MINOR "8")
set(CPACK_PACKAGE_VERSION_PATCH "2")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Command-line JSON processor for native Windows (MSVC) and 32-bit DOS (OpenWatcom).")
set(CPACK_PACKAGE_HOMEPAGE_URL "https://jqlang.org/")
set(CPACK_PACKAGE_CONTACT "Samuel Marks")
set(CPACK_PACKAGE_INSTALL_DIRECTORY "jq")
set(CPACK_GENERATOR "ZIP;NSIS;WIX")

set(_cpack_license_src "")
if(DEFINED JQ_SOURCE_DIR AND EXISTS "${JQ_SOURCE_DIR}/COPYING")
    set(_cpack_license_src "${JQ_SOURCE_DIR}/COPYING")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-MIT")
    set(_cpack_license_src "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE-MIT")
endif()

if(_cpack_license_src)
    if(DEFINED CMAKE_CURRENT_BINARY_DIR AND NOT "${CMAKE_CURRENT_BINARY_DIR}" STREQUAL "${CMAKE_CURRENT_SOURCE_DIR}")
        configure_file("${_cpack_license_src}" "${CMAKE_CURRENT_BINARY_DIR}/LICENSE.txt" COPYONLY)
        set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_BINARY_DIR}/LICENSE.txt")
    else()
        set(CPACK_RESOURCE_FILE_LICENSE "${_cpack_license_src}")
    endif()
endif()

set(CPACK_NSIS_DISPLAY_NAME "jq for Windows")
set(CPACK_NSIS_PACKAGE_NAME "jq for Windows")
set(CPACK_NSIS_MODIFY_PATH ON)

set(CPACK_WIX_UPGRADE_GUID "4A9C1E72-8B3D-4F1A-9C62-3D5E8F9A2041")
