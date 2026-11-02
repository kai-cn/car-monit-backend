cmake_minimum_required(VERSION 3.16)
project(car_monit_cpp VERSION 1.0.0 LANGUAGES C CXX)

# ---------------------------------------------------------------------------
# car-monit-backend 的 C++20 1:1 迁移工程
#
# 设计目标：
#   * 不依赖网络即可构建（第三方库已 vendor 到 third_party/）
#   * 只依赖系统自带的 OpenSSL / zlib / pthread
#   * 目录结构尽量与 Java 包名一一对应，方便 Java 开发人员对照
# ---------------------------------------------------------------------------

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

option(CAR_MONIT_BUILD_TESTS "Build unit tests" ON)
option(CAR_MONIT_BUILD_ASAN "Build with AddressSanitizer" OFF)

find_package(Threads REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(ZLIB REQUIRED)

# ---------------------------------------------------------------------------
# 第三方库（vendored）
# ---------------------------------------------------------------------------
add_library(bcrypt STATIC
    third_party/bcrypt/src/bcrypt.c
    third_party/bcrypt/src/crypt_blowfish.c
    third_party/bcrypt/src/crypt_gensalt.c
    third_party/bcrypt/src/wrapper.c
    third_party/bcrypt/src/x86.S
)
target_include_directories(bcrypt PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/bcrypt/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/bcrypt/include/bcrypt
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/bcrypt/src
)
set_target_properties(bcrypt PROPERTIES C_STANDARD 99)
if (CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64")
    target_compile_options(bcrypt PRIVATE -U__i386__)
endif()

# ---------------------------------------------------------------------------
# 主工程
# ---------------------------------------------------------------------------
file(GLOB_RECURSE CAR_MONIT_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_CURRENT_SOURCE_DIR}/src/cm/*.cpp
)
list(FILTER CAR_MONIT_SOURCES EXCLUDE REGEX ".*/src/cm/main\\.cpp$")

add_library(carmonit_core STATIC ${CAR_MONIT_SOURCES})
target_include_directories(carmonit_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)
target_link_libraries(carmonit_core PUBLIC
    bcrypt
    OpenSSL::SSL
    OpenSSL::Crypto
    ZLIB::ZLIB
    Threads::Threads
    ${CMAKE_DL_LIBS}
)

if (CAR_MONIT_BUILD_ASAN)
    target_compile_options(carmonit_core PUBLIC -fsanitize=address -fno-omit-frame-pointer)
    target_link_options(carmonit_core PUBLIC -fsanitize=address)
endif()

if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(carmonit_core PRIVATE -Wall -Wextra -Wno-unused-parameter)
endif()

add_executable(car-monit-cpp src/cm/main.cpp)
target_link_libraries(car-monit-cpp PRIVATE carmonit_core)

install(TARGETS car-monit-cpp RUNTIME DESTINATION bin)
install(DIRECTORY config/ DESTINATION config)

# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------
if (CAR_MONIT_BUILD_TESTS)
    enable_testing()
    file(GLOB_RECURSE CAR_MONIT_TEST_SOURCES CONFIGURE_DEPENDS
        ${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp
    )
    add_executable(carmonit_tests ${CAR_MONIT_TEST_SOURCES})
    target_link_libraries(carmonit_tests PRIVATE carmonit_core)
    target_include_directories(carmonit_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/tests)
    add_test(NAME carmonit_tests COMMAND carmonit_tests)
endif()
