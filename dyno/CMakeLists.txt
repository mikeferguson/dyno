cmake_minimum_required(VERSION 3.8)
project(dyno)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

ament_python_install_package(${PROJECT_NAME})
ament_package()
