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

# 本工程自带 SHA-1/SHA-256/SHA-512/HMAC/RSA-OAEP 与 DEFLATE 实现
# （src/cm/common/utils/crypto/*、src/cm/common/utils/Deflate.cpp），
# 所以 OpenSSL 与 zlib 都不再是必需依赖 —— 这是为了让 “clone 即可构建” 成立
# （Windows 上装 OpenSSL 开发包是 Java 同学的第一道坎）。
# 如果系统里存在 zlib，则优先用系统 zlib 出更小的 PNG。
find_package(ZLIB QUIET)
if (ZLIB_FOUND)
    set(CAR_MONIT_HAVE_ZLIB ON)
endif()

# ---------------------------------------------------------------------------
# 第三方库（vendored）
# ---------------------------------------------------------------------------
set(BCRYPT_SOURCES
    third_party/bcrypt/src/bcrypt.c
    third_party/bcrypt/src/crypt_blowfish.c
    third_party/bcrypt/src/crypt_gensalt.c
    third_party/bcrypt/src/wrapper.c
)
# x86.S 是 elf 平台的手写汇编（.globl/.type 语法）；Windows 的 pe 目标用 C 回退实现
if (NOT WIN32)
    list(APPEND BCRYPT_SOURCES third_party/bcrypt/src/x86.S)
endif()

add_library(bcrypt STATIC ${BCRYPT_SOURCES})
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
    Threads::Threads
    ${CMAKE_DL_LIBS}
)

if (CAR_MONIT_HAVE_ZLIB)
    target_link_libraries(carmonit_core PUBLIC ZLIB::ZLIB)
    target_compile_definitions(carmonit_core PUBLIC CM_HAVE_ZLIB=1)
endif()

if (WIN32)
    # Winsock2：Server / RedisClient / MySqlConnection 的 socket 封装
    target_link_libraries(carmonit_core PUBLIC ws2_32)
endif()

# ---------------------------------------------------------------------------
# mbedTLS（vendored，Apache-2.0）：出站 HTTPS 的 TLS 实现
#
# 为什么 vendor 而不是 find_package(OpenSSL)：
#   * 与本工程 "clone 即可构建" 的目标一致，Windows 上不需要额外装 OpenSSL 开发包；
#   * 明文与 TLS 共用 cm::net 的 socket，只需把 mbedtls 的 BIO 回调接到 readSome/writeSome。
# 只编 library/*.c 与 include/，不含 programs / tests / docs（那部分占 30MB+）。
# ---------------------------------------------------------------------------
file(GLOB MBEDTLS_SOURCES CONFIGURE_DEPENDS
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/mbedtls/library/*.c
)
add_library(mbedtls_cm STATIC ${MBEDTLS_SOURCES})
target_include_directories(mbedtls_cm PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/mbedtls/include
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/mbedtls/library
)
set_target_properties(mbedtls_cm PROPERTIES C_STANDARD 99)
if (WIN32)
    # 熵源走 CNG。⚠️ 必须写 bcrypt.lib 全名：只写 bcrypt 会被解析成上面的 third_party/bcrypt 目标
    target_link_libraries(mbedtls_cm PUBLIC ws2_32 bcrypt.lib)
endif()
target_link_libraries(carmonit_core PUBLIC mbedtls_cm)
target_compile_definitions(carmonit_core PUBLIC CM_HAVE_TLS=1)

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
    # 测试若要读仓库内文件（如 third_party/cacert.pem），用源码目录而不是运行时工作目录
    target_compile_definitions(carmonit_tests PRIVATE
        CM_TEST_SOURCE_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
    add_test(NAME carmonit_tests COMMAND carmonit_tests)
endif()

# ---------------------------------------------------------------------------
# 真库验收工具（默认不构建）：参数绑定 vs 手工拼接的对照 + 基准
#   cmake -B build -DCAR_MONIT_BUILD_DB_VERIFY=ON
#   需要一台可写的测试 MySQL；库名/端口由 CM_VERIFY_DB_* 环境变量指定。
# ---------------------------------------------------------------------------
option(CAR_MONIT_BUILD_DB_VERIFY "构建真库验收工具 carmonit_db_verify" OFF)
if (CAR_MONIT_BUILD_DB_VERIFY)
    add_executable(carmonit_db_verify tools/db_verify/main.cpp)
    target_link_libraries(carmonit_db_verify PRIVATE carmonit_core)
endif()

# Redis 连接模型验收工具（默认不构建）：多线程连接/AUTH/自愈/回收/降级
option(CAR_MONIT_BUILD_REDIS_VERIFY "构建 Redis 验收工具 carmonit_redis_verify" OFF)
if (CAR_MONIT_BUILD_REDIS_VERIFY)
    add_executable(carmonit_redis_verify tools/redis_verify/main.cpp)
    target_link_libraries(carmonit_redis_verify PRIVATE carmonit_core)
endif()

# 出站 HTTPS 验收工具（默认不构建）：真实站点握手 + 证书校验 + 失败路径
#   cmake -B build -DCAR_MONIT_BUILD_HTTP_VERIFY=ON
option(CAR_MONIT_BUILD_HTTP_VERIFY "构建 HTTPS 验收工具 carmonit_http_verify" OFF)
if (CAR_MONIT_BUILD_HTTP_VERIFY)
    add_executable(carmonit_http_verify tools/http_verify/main.cpp)
    target_link_libraries(carmonit_http_verify PRIVATE carmonit_core)
endif()
