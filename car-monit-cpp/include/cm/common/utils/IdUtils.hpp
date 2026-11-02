#pragma once
// 对应 Java: com.ruoyi.common.utils.uuid.IdUtils + com.ruoyi.common.utils.ip.IpUtils
#include <string>

namespace cm::utils {

/** 对应 IdUtils.fastUUID()：UUID v4，带 '-'，小写 */
std::string uuid();
/** 对应 IdUtils.fastSimpleUUID()：无 '-' */
std::string simpleUuid();
/** 32 位十六进制随机串（对应 request.getSession().getId() 的形态） */
std::string sessionId();

std::string ipAddr(const std::string& remoteAddr,
                   const std::string& xForwardedFor,
                   const std::string& proxyClientIp,
                   const std::string& wlProxyClientIp,
                   const std::string& xRealIp);
bool internalIp(const std::string& ip);

} // namespace cm::utils
