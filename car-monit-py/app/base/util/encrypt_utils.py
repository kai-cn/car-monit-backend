"""恒达（HenDa）接口签名工具.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/util/EncryptUtils.java

只迁移本项目实际用到的两个方法：:meth:`EncryptUtils.get_ciphertext` 与它的私有
依赖 ``createSignature``。``createSignatures``（海康加密）与 ``getSignHeader``
在本工程的 ``base`` 包里没有调用点，留待 ``manager`` / ``flow`` 包再补。

**必须照抄的缺陷**
------------------
``createSignature`` 里的字符串拼接写错了::

    for (String str : list) {
        if (publicStr.toString().isEmpty()) {
            publicStr.append(str);
        } else {
            publicStr.append(publicStr).append("&").append(str);   // 把自身又拼了一遍
        }
    }

于是 4 个元素依次得到 ``a`` -> ``aa&b`` -> ``aa&baa&b&c`` -> ``aa&baa&b&c`` +
``aa&baa&b&c`` + ``&d``。这个"指数增长"的字符串直接参与 MD5，**服务端也是按这个
算法校验的**，所以必须原样复现，不能"修正"成正常的 ``&`` join。
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional


class EncryptUtils:
    """Java: ``public class EncryptUtils``."""

    # Java: private static String createSignature(Map<String,String> headerMap,
    #                                             String secretKey, String jsonStr)
    @staticmethod
    def create_signature(header_map: Dict[str, Optional[str]], secret_key: str, json_str: str) -> str:
        # Java: Arrays.asList(...) 里每个元素都做 replace("[", "").replace("]", "")
        raw = [
            EncryptUtils._strip_brackets(header_map.get("appid")),
            EncryptUtils._strip_brackets(header_map.get("timestamp")),
            EncryptUtils._strip_brackets(header_map.get("nonce")),
            secret_key,
        ]
        # Java: Collections.sort(list) —— 自然序（UTF-16 码位序，与 Python 的 str 比较一致）
        ordered: List[str] = sorted(raw)

        # Java 的 StringBuilder 累加缺陷（见模块 docstring）—— 逐句照抄
        public_str = ""
        for element in ordered:
            if public_str == "":
                public_str = element
            else:
                public_str = public_str + public_str + "&" + element

        # Java: jsonStr.replace("\n", "").replace(" ", "")
        cleaned = json_str.replace("\n", "").replace(" ", "")
        to_sign = public_str + "&" + cleaned
        # Java: DigestUtils.md5DigestAsHex(strAdd.getBytes(UTF_8))
        return hashlib.md5(to_sign.encode("utf-8")).hexdigest()

    # Java: public static String getCiphertext(String appid, String secretKey,
    #                                          String nonce, String timestamp)
    @staticmethod
    def get_ciphertext(appid: str, secret_key: str, nonce: str, timestamp: str) -> str:
        headers: Dict[str, Optional[str]] = {
            "appid": appid,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        # Java: return EncryptUtils.createSignature(headers, secretKey, nonce);
        return EncryptUtils.create_signature(headers, secret_key, nonce)

    @staticmethod
    def _strip_brackets(value: Optional[str]) -> str:
        """Java 的 ``x.replace("[", "").replace("]", "")``；``null`` 会 NPE。

        Java 原文在 ``headerMap.get("appid")`` 为 ``null`` 时抛 ``NullPointerException``
        （调用方 ``HenDaServiceImpl`` 用 ``catch (Exception)`` 吞掉并返回 ``null``）。
        这里把 ``null`` 当成空串，最终结果同样是"拿不到经纬度"。
        """
        if value is None:
            return ""
        return value.replace("[", "").replace("]", "")


__all__ = ["EncryptUtils"]
