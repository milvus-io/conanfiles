cmake_minimum_required(VERSION 3.15)

project(fortran_check NONE)

include(CheckLanguage)
check_language(Fortran)
if(CMAKE_Fortran_COMPILER)
  enable_language(Fortran)
  string(REPLACE "." ";" _versions ${CMAKE_Fortran_COMPILER_VERSION})
  list (LENGTH _versions _len)
  if(_len GREATER 0)
    list(GET _versions 0 _version_major)
    set(_version_major "-${_version_major}.")
  endif()
  if(_len GREATER 1)
    list(GET _versions 1 _version_minor)
  endif()

  set(_compiler_id ${CMAKE_Fortran_COMPILER_ID}${_version_major}${_version_minor})
  message(STATUS ${_compiler_id})
  file(WRITE ${CMAKE_BINARY_DIR}/FORTRAN_COMPILER ${_compiler_id})
  message(STATUS ${CMAKE_BINARY_DIR})
else()
  message(STATUS "Unknown fortran compiler")
  file(WRITE ${CMAKE_BINARY_DIR}/FORTRAN_COMPILER 0)
endif()
