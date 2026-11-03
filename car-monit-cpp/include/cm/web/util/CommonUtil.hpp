#pragma once
// 对应 Java: com.ruoyi.web.util.CommonUtil（ruoyi-admin 模块里的那份）
//
// 放在 include/cm/web/util/ 下，是为了让 Java 同学按包名就能找到：
//   com.ruoyi.web.util.CommonUtil  ->  cm::web::util::CommonUtil
#include <string>

namespace cm::web::util {

class CommonUtil {
public:
    /**
     * 对应 CommonUtil.checkPassword：返回 true 表示**不合法**（与 Java 语义一致）。
     * Java 正则：^(?![A-Za-z0-9]+$)(?![a-z0-9\W]+$)(?![A-Za-z\W]+$)(?![A-Z0-9\W]+$)[a-zA-Z0-9\W]{8,20}$
     * 即 8~20 位，且必须同时含大写、小写、数字、特殊符号；下划线属于 \w 但不在字符集内，故直接判负。
     */
    static bool checkPassword(const std::string& password) {
        size_t len = 0;
        for (unsigned char c : password) {
            if ((c & 0xC0) != 0x80) ++len;  // UTF-8 码点计数（近似 Java 的 char 数）
        }
        if (len < 8 || len > 20) return true;

        bool lower = false, upper = false, digit = false, special = false;
        for (unsigned char c : password) {
            if (c == '_') return true;
            if (c >= 'a' && c <= 'z') {
                lower = true;
            } else if (c >= 'A' && c <= 'Z') {
                upper = true;
            } else if (c >= '0' && c <= '9') {
                digit = true;
            } else {
                special = true;
            }
        }
        return !(lower && upper && digit && special);
    }
};

} // namespace cm::web::util
