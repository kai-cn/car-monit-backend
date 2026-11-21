#pragma once
// socket 句柄的平台无关声明。
//
// Linux/macOS 下就是 int；Windows 下 Winsock 的 SOCKET 是 64 位无符号整数。
// 单独抽一个头文件出来，是为了让 RedisClient.hpp / Server.hpp 这类被广泛引用的
// 头文件不必 include <winsock2.h>（它会带进 windows.h 的一堆宏污染）。
//
// 对应 Java: java.net.Socket 的句柄由 JDK 内部持有，业务代码看不到
#ifdef _WIN32
namespace cm::net {
using Fd = unsigned long long;
inline constexpr Fd kInvalid = static_cast<Fd>(~0ull);
} // namespace cm::net
#else
#include <sys/types.h>
namespace cm::net {
using Fd = int;
inline constexpr Fd kInvalid = static_cast<Fd>(-1);
} // namespace cm::net
#endif

namespace cm::net {

// 有些类（RedisClient / MySqlConnection）希望在头文件里持有句柄，但又不想
// 因为 include winsock2.h 而污染所有调用方，于是用 long long 存句柄数值。
// 下面三个函数负责来回转换；Windows 的 INVALID_SOCKET(~0ull) 落到 long long
// 上正好是 -1，两端语义一致。
inline constexpr long long kInvalidStorage = -1;

inline long long toStorage(Fd fd) { return static_cast<long long>(fd); }
inline Fd fromStorage(long long v) { return v == kInvalidStorage ? kInvalid : static_cast<Fd>(v); }
inline bool validStorage(long long v) { return v != kInvalidStorage; }

} // namespace cm::net
