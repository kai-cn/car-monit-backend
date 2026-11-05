#pragma once
// 内置 INFLATE（RFC 1951）与 zlib 外层（RFC 1950）解码器。
//
// 为什么需要它：xlsx / docx 都是 zip 包，而 zip 里的成员默认是 deflate 压缩的。
// 本工程要求零第三方依赖，写 xlsx 时用的是 store（不压缩），所以只实现了 deflate；
// 读 xlsx（Excel 导入类接口）就必须能解 deflate —— 这个文件补的就是这一半。
//
// 系统里若装了 zlib（CMake 定义 CM_HAVE_ZLIB）也**仍然走这套内置实现**：
// 两条路径的解码结果必须一致，否则会出现在有/无 zlib 的两台机器上行为不同。
#include <cstdint>
#include <string>
#include <string_view>

namespace cm::utils {

/** 解一段裸 DEFLATE 数据。成功返回 true；失败返回 false 并把原因写进 err（可为 nullptr） */
bool inflateRaw(std::string_view in, std::string& out, std::string* err = nullptr);

/** 解 zlib 流：跳过 CMF/FLG，校验 Adler-32 尾。POI/PNG 用的就是这个格式 */
bool inflateZlib(std::string_view in, std::string& out, std::string* err = nullptr);

/** 校验用：gzip 外壳（RFC 1952）里的 DEFLATE 段，供 xlsx 之外的场景复用 */
bool inflateGzip(std::string_view in, std::string& out, std::string* err = nullptr);

} // namespace cm::utils
