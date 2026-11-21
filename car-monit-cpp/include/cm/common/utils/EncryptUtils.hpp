#pragma once
// 对应 Java: com.ruoyi.base.util.EncryptUtils（不在 ruoyi-common 里，是 manager 侧自带的）
//
// 这里的 createSignature 含一个**必须照抄的 bug**：拼接待签字符串时写的是
//     publicStr.append(publicStr).append("&").append(str)
// 而不是 publicStr.append("&").append(str) —— 每一轮都把已有的累加量翻倍再追加。
// 服务端要的是同一个 MD5，所以"顺手修好"只会让对端验签失败，因此这里逐字复刻，
// 并把中间串单独暴露成 signatureSource()，方便单测直接钉住它（而不是只测最终的 md5）。
#include <string>

namespace cm::crypto {

/** 排好序的 4 段：appid / timestamp / nonce / secretKey，按 Java String.compareTo 排序
 *  （即按 UTF-8 字节序，数字 < 'Y' < 'b'）。参数顺序与 Java 一致。 */
std::string signatureSource(const std::string& appid, const std::string& timestamp,
                            const std::string& nonce, const std::string& secretKey,
                            const std::string& jsonStr);

/** 完整签名（小写十六进制 MD5）。jsonStr 传的是 nonce —— 上游调用方就是这么给的。 */
std::string createSignature(const std::string& appid, const std::string& timestamp,
                            const std::string& nonce, const std::string& secretKey,
                            const std::string& jsonStr);

/** HenDaServiceImpl 实际用的那层封装：headers={appid,nonce,timestamp}，jsonStr=nonce */
std::string getCiphertext(const std::string& appid, const std::string& secretKey,
                          const std::string& nonce, const std::string& timestamp);

} // namespace cm::crypto
