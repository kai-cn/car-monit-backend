// EncryptUtils 的移植，逐行对照 ruoyi-system/src/main/java/com/ruoyi/base/util/EncryptUtils.java
#include "cm/common/utils/EncryptUtils.hpp"

#include <algorithm>
#include <vector>

#include "cm/common/utils/crypto/Digest.hpp"

namespace cm::crypto {

std::string signatureSource(const std::string& appid, const std::string& timestamp,
                            const std::string& nonce, const std::string& secretKey,
                            const std::string& jsonStr) {
    // Java: Arrays.asList(appid.replace("[","").replace("]",""), timestamp…, nonce…, secretKey)
    //       再 Collections.sort(...)。replace 对这几个值是空操作，但 replace("[","") 是
    //       String.replace(char,char)？不是 —— 是 replace(CharSequence,CharSequence)，
    //       删掉所有 '[' 与 ']'。这里照做，避免"看起来没用就省掉"。
    auto strip = [](std::string s) {
        std::string o;
        for (char c : s) {
            if (c != '[' && c != ']') o.push_back(c);
        }
        return o;
    };
    std::vector<std::string> list = {strip(appid), strip(timestamp), strip(nonce), secretKey};
    std::sort(list.begin(), list.end());   // Java 的 Collections.sort 是同序（UTF-8 字节序）

    // 复刻 publicStr.append(publicStr) 的翻倍 bug：每轮先把当前累加量再拼一遍，再 & 下一段
    std::string publicStr;
    for (const auto& str : list) {
        if (publicStr.empty()) {
            publicStr = str;
        } else {
            publicStr = publicStr + publicStr + "&" + str;
        }
    }
    // Java: jsonStr.replace("\n","").replace(" ","")
    std::string body;
    for (char c : jsonStr) {
        if (c != '\n' && c != ' ') body.push_back(c);
    }
    return publicStr + "&" + body;
}

std::string createSignature(const std::string& appid, const std::string& timestamp,
                            const std::string& nonce, const std::string& secretKey,
                            const std::string& jsonStr) {
    const std::string src = signatureSource(appid, timestamp, nonce, secretKey, jsonStr);
    return hex(md5(src));   // 对应 DigestUtils.md5DigestAsHex(bytes)
}

std::string getCiphertext(const std::string& appid, const std::string& secretKey,
                          const std::string& nonce, const std::string& timestamp) {
    return createSignature(appid, timestamp, nonce, secretKey, nonce);
}

} // namespace cm::crypto
