"""HTML 过滤器 —— Java ``HTMLFilter`` 的 1:1 移植.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/html/HTMLFilter.java

为什么整段照搬
--------------
Java 的 ``EscapeUtil.clean`` 不是简单的 HTML 转义，而是调用 ``HTMLFilter``：
它**保留** ``a`` / ``b`` / ``strong`` / ``i`` / ``em`` / ``img`` 这些白名单标签，
剥离 ``script`` 等不允许的标签（标签内的文本保留），检查 ``href`` / ``src`` 的协议，
并把注释整段删除。直接换成 ``html.escape`` 会让入库内容与 Java 不一致。

移植时保留的可观察细节：

* ``filter`` 的顺序：注释 -> 平衡尖括号 -> 处理标签 -> 删除空标签；
* 允许标签的属性和协议：``a`` 只允许 ``href`` / ``target``，``img`` 只允许
  ``src`` / ``width`` / ``height`` / ``alt``，协议只允许 ``http`` / ``mailto`` / ``https``；
* 非白名单标签输出空串（标签被删、文本保留）；
* 注释标签在 ``check_tags`` 阶段被删除（``stripComment=True``）；
* 属性值的引号按 Java 源码原样输出为 ``=\\"value\\"``（源码里就是
  ``"=\\\""``，不是笔误；这是为了与 Java 的字节输出一致）；
* 未闭合标签会在末尾补 ``</tag>``，补全顺序按 Java ``HashMap`` 的桶序（最多
  5 个键，容量 16，不会触发扩容）。

刻意不做的
----------
Java ``HTMLFilter`` 还支持通过 ``Map`` 构造器改配置；本项目只用默认构造器，
所以这里只保留默认配置。``encodeQuotes`` 在 Java 里是一个空操作（源码注释说明
不把双引号替换成 ``&quot;``，否则 JSON 会失效），这里同样返回原串。
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.common.core.domain.java_hash_map import bucket_index

#: Java: ``REGEX_FLAGS_SI = Pattern.CASE_INSENSITIVE | Pattern.DOTALL``
_SI = re.IGNORECASE | re.DOTALL

_P_COMMENTS = re.compile(r"<!--(.*?)-->", re.DOTALL)
_P_COMMENT = re.compile(r"^!--(.*)--$", _SI)
_P_TAGS = re.compile(r"<(.*?)>", re.DOTALL)
_P_END_TAG = re.compile(r"^/([a-z0-9]+)", _SI)
_P_START_TAG = re.compile(r"^([a-z0-9]+)(.*?)(/?)$", _SI)
_P_QUOTED_ATTRIBUTES = re.compile(r"([a-z0-9]+)=([\"'])(.*?)\2", _SI)
_P_UNQUOTED_ATTRIBUTES = re.compile(r"([a-z0-9]+)(=)([^\"\s']+)", _SI)
_P_PROTOCOL = re.compile(r"^([^:]+):", _SI)
_P_ENTITY = re.compile(r"&#(\d+);?")
_P_ENTITY_UNICODE = re.compile(r"&#x([0-9a-f]+);?")
_P_ENCODE = re.compile(r"%([0-9a-f]{2});?")
_P_VALID_ENTITIES = re.compile(r"&([^&;]*)(?=(;|&|$))")
_P_END_ARROW = re.compile(r"^>")
_P_BODY_TO_END = re.compile(r"<([^>]*?)(?=<|$)")
_P_XML_CONTENT = re.compile(r"(^|>)([^<]*?)(?=>)")
_P_STRAY_LEFT_ARROW = re.compile(r"<([^>]*?)(?=<|$)")
_P_STRAY_RIGHT_ARROW = re.compile(r"(^|>)([^<]*?)(?=>)")
_P_BOTH_ARROWS = re.compile(r"<>")
_P_AMP = re.compile(r"&")
_P_QUOTE = re.compile(r"\"")
_P_LEFT_ARROW = re.compile(r"<")
_P_RIGHT_ARROW = re.compile(r">")

_ALLOWED: Dict[str, List[str]] = {
    "a": ["href", "target"],
    "img": ["src", "width", "height", "alt"],
    "b": [],
    "strong": [],
    "i": [],
    "em": [],
}
_SELF_CLOSING_TAGS = ("img",)
_NEED_CLOSING_TAGS = ("a", "b", "strong", "i", "em")
_DISALLOWED: Tuple[str, ...] = ()
_ALLOWED_PROTOCOLS = ("http", "mailto", "https")
_PROTOCOL_ATTRS = ("src", "href")
_REMOVE_BLANKS = ("a", "b", "strong", "i", "em")
_ALLOWED_ENTITIES = ("amp", "gt", "lt", "quot")


def html_special_chars(value: str) -> str:
    """Java: ``HTMLFilter.htmlSpecialChars(String)`` —— 注释内容转义。"""
    result = _P_AMP.sub("&amp;", value)
    result = _P_QUOTE.sub("&quot;", result)
    result = _P_LEFT_ARROW.sub("&lt;", result)
    result = _P_RIGHT_ARROW.sub("&gt;", result)
    return result


def _in_array(value: Optional[str], array: Tuple[str, ...]) -> bool:
    return value is not None and value in array


def _chr(value: int) -> str:
    """Java: ``String.valueOf((char) decimal)``.

    Java 的 ``char`` 是 16 位，超出 BMP 的码点会被截断；这里用 ``chr`` 并在非法码点时
    原样保留匹配文本，避免 Python 抛 ``ValueError`` 打断整个请求。
    """
    try:
        return chr(value)
    except (ValueError, OverflowError):
        return ""


class HTMLFilter:
    """Java: ``HTMLFilter``（默认构造器配置）。"""

    def __init__(self) -> None:
        self.v_allowed = _ALLOWED
        self.v_self_closing_tags = _SELF_CLOSING_TAGS
        self.v_need_closing_tags = _NEED_CLOSING_TAGS
        self.v_disallowed = _DISALLOWED
        self.v_allowed_protocols = _ALLOWED_PROTOCOLS
        self.v_protocol_atts = _PROTOCOL_ATTRS
        self.v_remove_blanks = _REMOVE_BLANKS
        self.v_allowed_entities = _ALLOWED_ENTITIES
        self.strip_comment = True
        self.encode_quotes = True
        self.always_make_tags = False
        self.v_tag_counts: Dict[str, int] = {}

    # Java: public String filter(String input)
    def filter(self, input_text: str) -> str:
        self._reset()
        s = self._escape_comments(input_text)
        s = self._balance_html(s)
        s = self._check_tags(s)
        s = self._process_remove_blanks(s)
        return s

    def _reset(self) -> None:
        self.v_tag_counts.clear()

    # Java: private String escapeComments(String s)
    @staticmethod
    def _escape_comments(s: str) -> str:
        if _P_COMMENTS.search(s) is None:
            return s
        return _P_COMMENTS.sub(
            lambda match: "<!--" + html_special_chars(match.group(1)) + "-->",
            s,
            count=1,
        )

    # Java: private String balanceHTML(String s)
    def _balance_html(self, s: str) -> str:
        if self.always_make_tags:
            s = _P_END_ARROW.sub("", s)
            s = _P_BODY_TO_END.sub(lambda m: "<" + m.group(1) + ">", s)
            s = _P_XML_CONTENT.sub(lambda m: m.group(1) + "<" + m.group(2), s)
        else:
            s = _P_STRAY_LEFT_ARROW.sub(lambda m: "&lt;" + m.group(1), s)
            s = _P_STRAY_RIGHT_ARROW.sub(
                lambda m: m.group(1) + m.group(2) + "&gt;<", s
            )
            s = _P_BOTH_ARROWS.sub("", s)
        return s

    # Java: private String checkTags(String s)
    def _check_tags(self, s: str) -> str:
        s = _P_TAGS.sub(lambda match: self._process_tag(match.group(1)), s)

        # Java 的 HashMap 迭代序：桶号升序，同桶保持插入序。
        keys = sorted(self.v_tag_counts, key=lambda key: bucket_index(key))
        tail = "".join(
            f"</{key}>" * self.v_tag_counts.get(key, 0) for key in keys
        )
        return s + tail

    # Java: private String processTag(String s)
    def _process_tag(self, s: str) -> str:
        # ending tags
        match = _P_END_TAG.match(s)
        if match is not None:
            name = match.group(1).lower()
            if self._allowed(name) and not _in_array(name, self.v_self_closing_tags):
                if name in self.v_tag_counts:
                    self.v_tag_counts[name] = self.v_tag_counts[name] - 1
                    return f"</{name}>"

        # starting tags
        match = _P_START_TAG.match(s)
        if match is not None:
            name = match.group(1).lower()
            body = match.group(2)
            ending = match.group(3)

            if not self._allowed(name):
                return ""

            params = ""
            param_names: List[str] = []
            param_values: List[str] = []
            for quoted in _P_QUOTED_ATTRIBUTES.finditer(body):
                param_names.append(quoted.group(1))
                param_values.append(quoted.group(3))
            for unquoted in _P_UNQUOTED_ATTRIBUTES.finditer(body):
                param_names.append(unquoted.group(1))
                param_values.append(unquoted.group(3))

            for param_name, param_value in zip(param_names, param_values):
                param_name = param_name.lower()
                if not self._allowed_attribute(name, param_name):
                    continue
                if _in_array(param_name, self.v_protocol_atts):
                    param_value = self._process_param_protocol(param_value)
                # Java: append("=\\\"") -> 字面量 =\"
                params += f' {param_name}=\\"{param_value}\\"'

            if _in_array(name, self.v_self_closing_tags):
                ending = " /"
            if _in_array(name, self.v_need_closing_tags):
                ending = ""

            if ending is None or len(ending) < 1:
                self.v_tag_counts[name] = self.v_tag_counts.get(name, 0) + 1
            else:
                ending = " /"

            return f"<{name}{params}{ending}>"

        # comments
        match = _P_COMMENT.match(s)
        if not self.strip_comment and match is not None:
            return f"<{match.group(0)}>"
        return ""

    # Java: private String processParamProtocol(String s)
    def _process_param_protocol(self, s: str) -> str:
        s = self._decode_entities(s)
        match = _P_PROTOCOL.match(s)
        if match is not None:
            protocol = match.group(1)
            if not _in_array(protocol, self.v_allowed_protocols):
                # bad protocol, turn into local anchor link instead
                s = "#" + s[len(protocol) + 1 :]
                if s.startswith("#//"):
                    s = "#" + s[3:]
        return s

    # Java: private String decodeEntities(String s)
    def _decode_entities(self, s: str) -> str:
        s = _P_ENTITY.sub(lambda m: _chr(int(m.group(1))), s)
        s = _P_ENTITY_UNICODE.sub(lambda m: _chr(int(m.group(1), 16)), s)
        s = _P_ENCODE.sub(lambda m: _chr(int(m.group(1), 16)), s)
        return self._validate_entities(s)

    # Java: private String validateEntities(String s)
    def _validate_entities(self, s: str) -> str:
        s = _P_VALID_ENTITIES.sub(
            lambda m: self._check_entity(m.group(1), m.group(2)), s
        )
        return self._encode_quotes(s)

    def _check_entity(self, preamble: str, term: Optional[str]) -> str:
        # Java: return ";".equals(term) && isValidEntity(preamble)
        #               ? '&' + preamble : "&amp;" + preamble;
        if term == ";" and _in_array(preamble, self.v_allowed_entities):
            return "&" + preamble
        return "&amp;" + preamble

    def _encode_quotes(self, s: str) -> str:
        # Java 的实现是空操作（源码注释：不替换双引号，防止 JSON 格式无效）。
        return s

    def _process_remove_blanks(self, s: str) -> str:
        result = s
        for tag in self.v_remove_blanks:
            result = re.sub(
                r"<" + tag + r"(\s[^>]*)?></" + tag + r">", "", result
            )
            result = re.sub(r"<" + tag + r"(\s[^>]*)?/>", "", result)
        return result

    def _allowed(self, name: str) -> bool:
        return (
            (not self.v_allowed or name in self.v_allowed)
            and not _in_array(name, self.v_disallowed)
        )

    def _allowed_attribute(self, name: str, param_name: str) -> bool:
        return self._allowed(name) and (
            not self.v_allowed or param_name in self.v_allowed.get(name, [])
        )


__all__ = ["HTMLFilter", "html_special_chars"]
