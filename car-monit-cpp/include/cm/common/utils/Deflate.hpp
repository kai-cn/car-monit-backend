#pragma once
// zlib 兼容的 DEFLATE 压缩（PNG IDAT 需要 zlib 流：2 字节头 + DEFLATE + Adler-32）。
//
// 对应 Java: java.util.zip.Deflater（Kaptcha 出图、Excel/POI 内部也用得到）
//
// 构建时若找到系统 zlib（CMake 定义 CM_HAVE_ZLIB），直接用它；否则走内置实现：
// 输出 “stored” 块（BTYPE=00），是完全合法的 zlib/DEFLATE 流，任何解码器都能读，
// 只是不压缩、体积比 DEFLATE 大一些。验证码图 160x60，代价约 10KB，可接受。
// ⚠️ 体积差异记录在 COMPATIBILITY.md。
#include <cstdint>
#include <string>
#include <string_view>

namespace cm::utils {

/** level 仅为与 zlib 接口对齐；内置实现忽略它 */
std::string deflateZlib(std::string_view data, int level = 6);

/** 内置实现（无 zlib 时用于兜底，也便于单测对拍） */
std::string deflateZlibStored(std::string_view data);

/** PNG/zlib 多项式的 CRC-32（0xEDB88320，初值 0xFFFFFFFF，结果取反） */
uint32_t crc32(std::string_view data);

} // namespace cm::utils
