// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/IpUtils.java
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/AddressUtils.java
//       ruoyi-admin/src/main/java/com/ruoyi/web/util/CommonUtil.java#checkPassword
//       ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/IdUtils.java
// 职责: 与登录审计、令牌、验证码相关的纯函数。
// 对应关系: IpUtils.getIpAddr -> client_ip；UserAgentUtils -> parse_user_agent（近似）；
//           AddressUtils.getRealAddressByIP -> real_address；CommonUtil.checkPassword -> password_invalid。

use std::net::SocketAddr;

use axum::http::HeaderMap;
use uuid::Uuid;

/// Java: UserAgentUtils.parseUserAgentString 的结果在登录审计中的两个字段。
#[derive(Debug, Clone, Default)]
pub struct ClientMeta {
    pub ip: String,
    pub login_location: String,
    pub browser: String,
    pub os: String,
}

/// Java: IpUtils.getIpAddr(request)
pub fn client_ip(headers: &HeaderMap, addr: Option<SocketAddr>) -> String {
    const UNKNOWN: &str = "unknown";
    let header = |name: &str| -> Option<String> {
        headers
            .get(name)
            .and_then(|v| v.to_str().ok())
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty() && !s.eq_ignore_ascii_case(UNKNOWN))
    };

    let candidates = [
        "x-forwarded-for",
        "x-real-ip",
        "proxy-client-ip",
        "wl-proxy-client-ip",
        "http_client_ip",
        "http_x_forwarded_for",
    ];
    for name in candidates {
        if let Some(value) = header(name) {
            // Java 取逗号分隔的第一个地址
            let first = value.split(',').next().unwrap_or("").trim();
            if first.eq_ignore_ascii_case(UNKNOWN) {
                continue;
            }
            return first.to_string();
        }
    }
    match addr {
        Some(a) => a.ip().to_string(),
        None => UNKNOWN.to_string(),
    }
}

/// Java: IpUtils.internalIp(ip)
pub fn internal_ip(ip: &str) -> bool {
    if ip.eq_ignore_ascii_case("127.0.0.1")
        || ip.eq_ignore_ascii_case("localhost")
        || ip == "0:0:0:0:0:0:0:1"
        || ip == "::1"
    {
        return true;
    }
    match ip.parse::<std::net::IpAddr>() {
        Ok(std::net::IpAddr::V4(v4)) => v4.is_private() || v4.is_loopback() || v4.is_link_local(),
        Ok(std::net::IpAddr::V6(v6)) => v6.is_loopback(),
        Err(_) => false,
    }
}

/// Java: AddressUtils.getRealAddressByIP(String)
/// 内网固定 "内网IP"；addressEnabled=false 或查询失败固定 "XX XX"。
/// Java 在开启时请求 whois.pconline.com.cn；Rust 侧保持同样的失败回退，实际查询留待接入。
pub fn real_address(ip: &str, address_enabled: bool) -> String {
    if internal_ip(ip) {
        return "内网IP".to_string();
    }
    if address_enabled {
        // Java 使用外部 HTTP 接口；为避免启动路径阻塞，这里返回同样的未知回退。
        // 远端解析在后续 OSS/Forest 切片补齐（见 docs/02-JAVA-RUST-MAPPING.md D9）。
        return "XX XX".to_string();
    }
    "XX XX".to_string()
}

/// Java: new WebAuthenticationDetailsSource().buildDetails(request) 在审计中只用到这些。
pub fn client_meta(
    headers: &HeaderMap,
    addr: Option<SocketAddr>,
    address_enabled: bool,
) -> ClientMeta {
    let ip = client_ip(headers, addr);
    let user_agent = headers
        .get("user-agent")
        .and_then(|v| v.to_str().ok())
        .unwrap_or_default();
    let (browser, os) = parse_user_agent(user_agent);
    ClientMeta {
        login_location: real_address(&ip, address_enabled),
        ip,
        browser,
        os,
    }
}

/// 近似 UserAgentUtils：只保留审计/展示需要的浏览器与系统名称。
pub fn parse_user_agent(ua: &str) -> (String, String) {
    let browser = if ua.contains("Edg/") || ua.contains("Edge/") {
        "Edge"
    } else if ua.contains("OPR/") || ua.contains("Opera") {
        "Opera"
    } else if ua.contains("Chrome/") {
        "Chrome"
    } else if ua.contains("Firefox/") {
        "Firefox"
    } else if ua.contains("MSIE") || ua.contains("Trident/") {
        "Internet Explorer"
    } else if ua.contains("Safari/") {
        "Safari"
    } else {
        "Unknown"
    };

    let os = if ua.contains("Windows NT 10.0") {
        "Windows 10"
    } else if ua.contains("Windows NT 6.3") {
        "Windows 8.1"
    } else if ua.contains("Windows NT 6.2") {
        "Windows 8"
    } else if ua.contains("Windows NT 6.1") {
        "Windows 7"
    } else if ua.contains("Windows") {
        "Windows"
    } else if ua.contains("iPhone") || ua.contains("iPad") {
        "iOS"
    } else if ua.contains("Android") {
        "Android"
    } else if ua.contains("Mac OS X") {
        "Mac OS X"
    } else if ua.contains("Linux") {
        "Linux"
    } else {
        "Unknown"
    };

    (browser.to_string(), os.to_string())
}

/// Java: IdUtils.simpleUUID() -> 32 位无连字符 UUID
pub fn simple_uuid() -> String {
    Uuid::new_v4().simple().to_string()
}

/// Java: IdUtils.fastUUID()
pub fn fast_uuid() -> String {
    Uuid::new_v4().to_string()
}

/// Java: CommonUtil.checkPassword(String)
/// 正则要求 8-20 位、仅 ASCII 字母/数字/特殊符号，且四类字符全部出现。
/// Rust regex 不支持 lookahead，改为等价的逐类判断。
pub fn password_invalid(raw: &str) -> bool {
    let len = raw.chars().count();
    if !(8..=20).contains(&len) {
        return true;
    }
    let mut has_upper = false;
    let mut has_lower = false;
    let mut has_digit = false;
    let mut has_special = false;
    for c in raw.chars() {
        if c.is_ascii_uppercase() {
            has_upper = true;
        } else if c.is_ascii_lowercase() {
            has_lower = true;
        } else if c.is_ascii_digit() {
            has_digit = true;
        } else if c.is_ascii() && c != '_' {
            // 对应 [a-zA-Z0-9\W]：ASCII 非字母数字且非下划线
            has_special = true;
        } else {
            // 下划线、中文等不在 Java 正则允许范围内
            return true;
        }
    }
    !(has_upper && has_lower && has_digit && has_special)
}

/// Java: StringUtils.isNotBlank
pub fn is_not_blank(value: &str) -> bool {
    !value.trim().is_empty()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn password_rule_matches_java_regex() {
        assert!(!password_invalid("Abcd@1234"));
        assert!(password_invalid("localhost")); // 缺大写/数字/特殊符号
        assert!(password_invalid("A1!aaaa")); // 7 位
        assert!(password_invalid("Admin_2025")); // 下划线不在字符集内
        assert!(password_invalid("Aa1!中文Aa")); // 非 ASCII
    }

    #[test]
    fn internal_ip_ranges() {
        assert!(internal_ip("127.0.0.1"));
        assert!(internal_ip("192.168.1.2"));
        assert!(internal_ip("10.0.0.8"));
        assert!(!internal_ip("8.8.8.8"));
    }
}
