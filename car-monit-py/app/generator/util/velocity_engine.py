"""Velocity 子集解释器.

# Migrated from: org.apache.velocity:velocity-engine-core:2.3（模板引擎，无对应源文件）
# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityInitializer.java

为什么自己实现而不是改用 Jinja2
-------------------------------
``GET /tool/gen/preview/{tableId}`` 的响应是 ``Map<模板路径, 渲染后的源码>``，
``GET /tool/gen/download`` 打出来的 zip 更是逐字节交付给用户下载的文件。要做到
"接口返回结果一致"，渲染结果必须与 Java 侧**逐字符相同** —— 包括 Velocity
的空行吞噬（space gobbling）、未定义引用的字面量回退、以及模板里那些历史遗留的
写法（``$comment不能为空`` 这种把中文吃进变量名的笔误）。

把 24 个 ``.vm`` 手工改写成 Jinja2 模板，等于重新实现一遍并引入 24 处可能的人为
偏差；直接让 **原封不动的 ``.vm`` 文件**在这套解释器上跑，才是可验证的等价。

支持的语法（以模板里实际出现为准，已逐条扫描确认）
-------------------------------------------------
指令::

    #if(expr) / #elseif(expr) / #else / #end
    #foreach($x in $list) ... #end
    #set($x = expr)
    #break
    #[[ ... ]]#            原样输出块
    ## 行注释 / #* 块注释 *#

引用::

    $x  $!x  ${x}  $!{x}  #{${x}}（MyBatis 的 #{} 里套一个引用）
    $x.y  $x.y.z  $x.m(1, "s")  $x.y.substring(0, 1).toUpperCase()

表达式::

    ||  &&  ==  !=  >  >=  <  <=  +  !  ( )  单/双引号字符串  数字

``$foreach.hasNext`` / ``$foreach.index`` / ``$velocityCount`` 在 ``#foreach``
体内可用。

空行吞噬（space gobbling = lines，Velocity 2.3 的默认值）
---------------------------------------------------------
**一整行只由指令与空白组成**时，这一行连同换行一起被丢弃。这正是 RuoYi 生成的
``import`` 之间没有空行、``@Excel`` 紧贴字段注释的原因。注意判定单位是"物理行"，
不是"单个指令"：``#foreach(...) t.$column.columnName#if(...),\n#end#end`` 这一行
含字面量文本，所以**不**吞噬（``t.col1, t.col2`` 会连成一行）。

未定义引用
----------
``$foo`` 求值不到时**原样输出 ``$foo``**（Velocity 的 ``ASTReference`` 行为），
``$!foo`` 输出空串。这条让 ``this.$emit('resSuccess')``、``$comment不能为空``
这类历史写法自然保真 —— 不要"顺手修好"它们。

运算符语义
----------
``==`` 对字符串走 ``equals``（大小写敏感）、对数字走数值比较；``+`` 两侧都是数字时做
加法，否则做字符串拼接（``null`` 视为空串）；``>``/``<`` 任一侧为 ``null`` 时
Velocity 记一条错误并返回 ``null``（进 ``#if`` 即 false），这里同样返回"未定义"。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.common.exception.exceptions import UtilException
from app.common.utils.string_utils import java_trim
from app.settings import CONFIG_DIR

#: Java: classpath 根 —— ``config/`` 对应 ``ruoyi-generator/src/main/resources/``，
#: 所以 ``Velocity.getTemplate("vm/java/domain.java.vm")`` == ``config/vm/java/domain.java.vm``。
TEMPLATE_ROOT: Path = CONFIG_DIR

#: Java: ``Velocity.INPUT_ENCODING`` = ``Constants.UTF8``
TEMPLATE_ENCODING = "utf-8"


class VelocityException(UtilException):
    """Java: ``org.apache.velocity.exception.VelocityException``."""


class _Undefined:
    """``null`` 之外再区分"引用根本不存在"—— 两者都按 null 处理，但便于断言."""

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return "UNDEFINED"


UNDEFINED = _Undefined()


# --------------------------------------------------------------------------- 上下文


class VelocityContext:
    """Java: ``org.apache.velocity.VelocityContext`` —— 一个 ``get/put`` 字典."""

    __slots__ = ("_values",)

    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        self._values: Dict[str, Any] = dict(values) if values else {}

    def put(self, key: str, value: Any) -> None:
        """Java: ``void put(String key, Object value)``（值可以是 null）."""
        self._values[key] = value

    def get(self, key: str) -> Any:
        """Java: ``Object get(String key)`` —— 不存在返回 ``UNDEFINED``."""
        return self._values.get(key, UNDEFINED)

    def contains_key(self, key: str) -> bool:
        """Java: ``boolean containsKey(String key)``."""
        return key in self._values

    def remove(self, key: str) -> None:
        """Java: ``void remove(String key)``."""
        self._values.pop(key, None)

    def keys(self) -> List[str]:
        return list(self._values.keys())


# --------------------------------------------------------------------------- 节点


class _BreakLoop(Exception):
    """``#break`` 的内部信号 —— 由最近一层 ``#foreach`` 捕获."""


class _Node:
    __slots__ = ()

    def render(self, context: VelocityContext, out: List[str]) -> None:  # pragma: no cover
        raise NotImplementedError


class _TextNode(_Node):
    __slots__ = ("text",)

    def __init__(self, text: str) -> None:
        self.text = text

    def render(self, context: VelocityContext, out: List[str]) -> None:
        out.append(self.text)


class _RefNode(_Node):
    """一个引用：根变量 + 属性/方法链."""

    __slots__ = ("raw", "root", "chain", "quiet")

    def __init__(
        self,
        raw: str,
        root: str,
        chain: Sequence[Tuple[str, str, Sequence[Any]]],
        quiet: bool,
    ) -> None:
        self.raw = raw
        self.root = root
        self.chain = list(chain)
        self.quiet = quiet

    def evaluate(self, context: VelocityContext) -> Any:
        value = context.get(self.root)
        for kind, name, args in self.chain:
            if value is UNDEFINED or value is None:
                return UNDEFINED
            if kind == "prop":
                value = _get_property(value, name)
            else:
                value = _call_method(value, name, [_eval(arg, context) for arg in args])
            if value is UNDEFINED:
                return UNDEFINED
        return value

    def render(self, context: VelocityContext, out: List[str]) -> None:
        value = self.evaluate(context)
        if value is UNDEFINED or value is None:
            # Java: ASTReference 求值不到 null 时把**引用原文**写回输出流。
            out.append("" if self.quiet else self.raw)
            return
        out.append(_to_java_string(value))


class _IfNode(_Node):
    __slots__ = ("branches", "else_nodes")

    def __init__(self, branches: Sequence[Tuple[Any, List[_Node]]], else_nodes: List[_Node]) -> None:
        self.branches = list(branches)
        self.else_nodes = else_nodes

    def render(self, context: VelocityContext, out: List[str]) -> None:
        for condition, nodes in self.branches:
            if _truthy(_eval(condition, context)):
                _render_nodes(nodes, context, out)
                return
        _render_nodes(self.else_nodes, context, out)


class _ForeachNode(_Node):
    __slots__ = ("var_name", "iterable", "body")

    def __init__(self, var_name: str, iterable: Any, body: List[_Node]) -> None:
        self.var_name = var_name
        self.iterable = iterable
        self.body = body

    def render(self, context: VelocityContext, out: List[str]) -> None:
        items = _eval(self.iterable, context)
        if items is UNDEFINED or items is None:
            # Java: foreach 迭代 null 集合 —— 循环体一次都不执行。
            return
        if isinstance(items, dict):
            items = list(items.keys())
        if isinstance(items, str):
            # Java 里 String 不是 Iterable，Velocity 直接报错；这里也按报错处理。
            raise VelocityException("#foreach 无法迭代 str")
        if not hasattr(items, "__iter__"):
            raise VelocityException(f"#foreach 无法迭代 {type(items).__name__}")
        items = list(items)

        saved = (context.get(self.var_name), context.get("foreach"), context.get("velocityCount"))
        total = len(items)
        try:
            for index, item in enumerate(items, start=1):
                context.put(self.var_name, item)
                # Java: directive.foreach.counter.name = velocityCount / initial.value = 1
                context.put("velocityCount", index)
                context.put("foreach", _ForeachStatus(index, total))
                try:
                    _render_nodes(self.body, context, out)
                except _BreakLoop:
                    break
        finally:
            context.put(self.var_name, saved[0])
            context.put("foreach", saved[1])
            context.put("velocityCount", saved[2])


class _ForeachStatus:
    """Java: Velocity 注入的 ``$foreach``（``ForeachScope``）."""

    __slots__ = ("index", "count", "has_next", "first", "last")

    def __init__(self, count: int, total: int) -> None:
        #: 从 0 开始的下标
        self.index = count - 1
        #: 从 1 开始的计数
        self.count = count
        self.has_next = count < total
        self.first = count == 1
        self.last = count == total


class _SetNode(_Node):
    __slots__ = ("name", "expr")

    def __init__(self, name: str, expr: Any) -> None:
        self.name = name
        self.expr = expr

    def render(self, context: VelocityContext, out: List[str]) -> None:
        value = _eval(self.expr, context)
        if value is UNDEFINED or value is None:
            # Java: #set 右侧为 null 时**不**赋值（变量保持"未定义"状态）。
            context.remove(self.name)
            return
        context.put(self.name, value)


class _BreakNode(_Node):
    __slots__ = ()

    def render(self, context: VelocityContext, out: List[str]) -> None:
        raise _BreakLoop()


# --------------------------------------------------------------------------- 词法辅助

#: 认识的指令名；其余 ``#xxx`` 一律当普通文本（``#{id}`` / ``#fff`` 靠这条保住）。
_DIRECTIVE_NAMES = frozenset(
    {
        "if",
        "elseif",
        "else",
        "end",
        "foreach",
        "set",
        "break",
        "stop",
    }
)

#: 带括号参数的指令
_WITH_ARGS = frozenset({"if", "elseif", "foreach", "set"})

#: 指令名按**长度降序**排列 —— 前缀匹配时 ``#elseif`` 必须先于 ``#else`` 命中
_DIRECTIVE_ORDER: Tuple[str, ...] = (
    "foreach",
    "elseif",
    "break",
    "else",
    "stop",
    "end",
    "set",
    "if",
)

_FOREACH_PATTERN = re.compile(r"^\s*\$!?\{?([A-Za-z_][A-Za-z0-9_]*)\}?\s+in\s+(.+)$", re.DOTALL)

_SET_LHS_PATTERN = re.compile(r"^\s*\$!?\{?([A-Za-z_][A-Za-z0-9_]*)\}?\s*$")

_SPECIAL = re.compile(r"[#$]")


def _is_identifier_char(char: str) -> bool:
    """Velocity 的标识符只认 ASCII 字母/数字/下划线.

    ``vm/vue/index-tree.vue.vm`` 里的 ``message: "$comment不能为空"`` 就是靠这条规则
    才能渲染成 ``message: "部门名称不能为空"`` —— 如果按 Python 的 ``isalnum()``
    把汉字也吃进标识符，整句就会变成字面的 ``$comment不能为空``。
    """
    return char.isascii() and (char.isalnum() or char == "_")


def _skip_string(text: str, index: int) -> int:
    """跳过一段带引号的字符串，返回收尾引号之后的下标."""
    quote = text[index]
    index += 1
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        index += 1
    raise VelocityException("字符串没有闭合引号")


def _read_balanced(text: str, open_pos: int) -> Tuple[str, int]:
    """读一对配对括号，返回 ``(括号内文本, 右括号之后的下标)``."""
    depth = 0
    index = open_pos
    length = len(text)
    while index < length:
        char = text[index]
        if char in "\"'":
            index = _skip_string(text, index)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_pos + 1:index], index + 1
        index += 1
    raise VelocityException(f"括号没有闭合: {text[open_pos:]!r}")


def _find_close_brace(text: str, start: int) -> int:
    """在 ``${`` 之后找到配对的 ``}``，跳过括号内的 ``()``."""
    index = start
    length = len(text)
    paren = 0
    while index < length:
        char = text[index]
        if char in "\"'":
            index = _skip_string(text, index)
            continue
        if char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "}" and paren == 0:
            return index
        index += 1
    return -1


def _scan_directive(
    text: str, pos: int
) -> Optional[Tuple[str, Optional[str], int]]:
    """识别 ``pos`` 处的 ``#`` 指令，返回 ``(名字, 括号内文本, 结束下标)``.

    ``pos`` 处不是指令时返回 ``None``（调用方按普通文本处理）。
    特殊名字：``"comment"``（``##`` 行注释，不含换行）、``"raw"``（``#[[...]]#``，
    括号内文本就是原样输出内容）。
    """
    if text[pos] != "#":
        return None
    length = len(text)
    if text.startswith("##", pos):
        newline = text.find("\n", pos)
        return "comment", None, length if newline == -1 else newline + 1
    if text.startswith("#[[", pos):
        end = text.find("]]#", pos + 3)
        if end == -1:
            return None
        return "raw", text[pos + 3:end], end + 3
    if text.startswith("#*", pos):
        end = text.find("*#", pos + 2)
        if end == -1:
            return None
        return "comment", None, end + 2

    # JavaCC 按"最长已定义 token"切词，所以 ``#endimport`` 会被拆成 ``#end`` + 文本
    # ``import``。这里必须用已知指令名做前缀匹配，不能把后面的标识符一起吃掉。
    name = ""
    for candidate in _DIRECTIVE_ORDER:
        if text.startswith(candidate, pos + 1):
            name = candidate
            break
    if not name:
        return None
    index = pos + 1 + len(name)
    if name in _WITH_ARGS:
        cursor = index
        while cursor < length and text[cursor] in " \t":
            cursor += 1
        if cursor >= length or text[cursor] != "(":
            # ``#set`` 少了括号 —— 按文本处理，别把整行吃掉。
            return None
        inner, after = _read_balanced(text, cursor)
        return name, inner, after
    return name, None, index


def _is_directive_only_line(line: str) -> bool:
    """判断一整行是否"只由指令与空白组成"（space gobbling = lines）."""
    text = line.rstrip("\r\n")
    index = 0
    length = len(text)
    found = False
    while index < length:
        char = text[index]
        if char in " \t":
            index += 1
            continue
        if char != "#":
            return False
        scanned = _scan_directive(text, index)
        if scanned is None:
            return False
        name, _arg, after = scanned
        if name == "raw":
            # ``#[[...]]#`` 输出的是文本，能决定这一行不会被吞噬。
            return False
        index = after
        found = True
    return found


def _strip_directive_only_lines(source: str) -> str:
    """实现 Velocity 的 ``space.gobbling=lines``.

    对**只含指令与空白**的行：去掉行首缩进与行尾换行，只留下指令本身；对其他行
    原样保留。效果就是那一行"不会在输出里留下空行"，但指令依旧生效。
    """
    kept: List[str] = []
    # 只按 \n 切（\r\n 的 \r 留在行尾，与 \n 一起被丢弃）
    for line in re.split(r"(?<=\n)", source):
        if not line:
            continue
        if _is_directive_only_line(line):
            kept.append(_directives_of(line))
            continue
        kept.append(line)
    return "".join(kept)


def _directives_of(line: str) -> str:
    """把一行里的指令挤成无空白的串（行内 ``##`` 注释之后的内容丢掉）."""
    text = line.rstrip("\r\n")
    parts: List[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] in " \t":
            index += 1
            continue
        scanned = _scan_directive(text, index)
        if scanned is None:  # pragma: no cover - _is_directive_only_line 已经校验过
            parts.append(text[index:])
            break
        name, _arg, after = scanned
        if name == "comment":
            break
        parts.append(text[index:after])
        index = after
    return "".join(parts)


# --------------------------------------------------------------------------- 引用解析


def _parse_args(text: str, open_pos: int, limit: int) -> Tuple[List[Any], int]:
    """解析 ``(`` 起的实参列表，返回 ``(实参表达式列表, 右括号之后的下标)``."""
    inner, after = _read_balanced(text[:limit], open_pos)
    if not inner.strip():
        return [], after
    args = [_ExprParser(part).parse() for part in _split_top_level(inner, ",")]
    return args, after


def _split_top_level(text: str, separator: str) -> List[str]:
    """按分隔符切分，忽略括号/引号内部的分隔符."""
    parts: List[str] = []
    depth = 0
    start = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char in "\"'":
            index = _skip_string(text, index)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
        index += 1
    parts.append(text[start:])
    return parts


def _scan_ref_body(
    text: str, index: int, limit: int
) -> Optional[Tuple[str, List[Tuple[str, str, Sequence[Any]]], int]]:
    """读 ``根标识符`` + ``.属性/.方法()`` 链，返回 ``(根名, 链, 结束下标)``."""
    start = index
    while index < limit and _is_identifier_char(text[index]):
        index += 1
    if index == start:
        return None
    root = text[start:index]
    chain: List[Tuple[str, str, Sequence[Any]]] = []
    while index < limit and text[index] == ".":
        cursor = index + 1
        while cursor < limit and _is_identifier_char(text[cursor]):
            cursor += 1
        if cursor == index + 1:
            # ``$x.`` 后面不是标识符 —— 链到此为止，点号留给文本。
            break
        name = text[index + 1:cursor]
        if cursor < limit and text[cursor] == "(":
            args, after = _parse_args(text, cursor, limit)
            chain.append(("call", name, args))
            index = after
        else:
            chain.append(("prop", name, ()))
            index = cursor
    return root, chain, index


def _parse_reference(text: str, pos: int) -> Tuple[Optional[_RefNode], int]:
    """解析 ``pos`` 处的一个引用，返回 ``(节点, 结束下标)``；不是引用时返回 ``(None, pos)``."""
    length = len(text)
    if pos >= length or text[pos] != "$":
        return None, pos
    index = pos + 1
    quiet = False
    if index < length and text[index] == "!":
        quiet = True
        index += 1
    if index < length and text[index] == "{":
        close = _find_close_brace(text, index + 1)
        if close == -1:
            return None, pos
        body = _scan_ref_body(text, index + 1, close)
        if body is None:
            return None, pos
        root, chain, after = body
        if after != close:
            # ``${...}`` 里必须是**完整**的引用，多出来的部分 Velocity 视为语法错误。
            return None, pos
        return _RefNode(text[pos:close + 1], root, chain, quiet), close + 1
    body = _scan_ref_body(text, index, length)
    if body is None:
        return None, pos
    root, chain, after = body
    return _RefNode(text[pos:after], root, chain, quiet), after


# --------------------------------------------------------------------------- 表达式


def _parse_expression(text: str) -> Any:
    """把指令括号内的表达式文本解析成表达式节点."""
    return _ExprParser(text).parse()


class _ExprParser:
    """递归下降：``|| < && < ==/!= < >/>=/</<= < + < ! < 基本项``."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.length = len(text)

    # ---------------------------------------------------------------- 入口
    def parse(self) -> Any:
        node = self._or()
        self._skip_space()
        if self.pos != self.length:
            raise VelocityException(f"表达式无法解析: {self.text!r}（位置 {self.pos}）")
        return node

    # ---------------------------------------------------------------- 辅助
    def _skip_space(self) -> None:
        while self.pos < self.length and self.text[self.pos] in " \t\r\n":
            self.pos += 1

    def _accept(self, token: str) -> bool:
        self._skip_space()
        if self.text.startswith(token, self.pos):
            self.pos += len(token)
            return True
        return False

    # ---------------------------------------------------------------- 各级
    def _or(self) -> Any:
        node = self._and()
        while self._accept("||"):
            node = ("bin", "||", node, self._and())
        return node

    def _and(self) -> Any:
        node = self._equality()
        while self._accept("&&"):
            node = ("bin", "&&", node, self._equality())
        return node

    def _equality(self) -> Any:
        node = self._relational()
        while True:
            if self._accept("=="):
                node = ("bin", "==", node, self._relational())
            elif self._accept("!="):
                node = ("bin", "!=", node, self._relational())
            else:
                return node

    def _relational(self) -> Any:
        node = self._additive()
        while True:
            for operator in (">=", "<=", ">", "<"):
                if self._accept(operator):
                    node = ("bin", operator, node, self._additive())
                    break
            else:
                return node

    def _additive(self) -> Any:
        node = self._unary()
        while self._accept("+"):
            node = ("bin", "+", node, self._unary())
        return node

    def _unary(self) -> Any:
        self._skip_space()
        if self.pos < self.length and self.text[self.pos] == "!":
            self.pos += 1
            return ("not", self._unary())
        return self._primary()

    def _primary(self) -> Any:
        self._skip_space()
        if self.pos >= self.length:
            raise VelocityException(f"表达式不完整: {self.text!r}")
        char = self.text[self.pos]
        if char == "(":
            self.pos += 1
            node = self._or()
            self._skip_space()
            if self.pos >= self.length or self.text[self.pos] != ")":
                raise VelocityException(f"表达式括号不匹配: {self.text!r}")
            self.pos += 1
            return node
        if char in "\"'":
            content, after = _read_string_literal(self.text, self.pos)
            self.pos = after
            # Java: 单引号串不插值，双引号串插值
            return ("str", content, char == '"')
        if char == "$":
            node, after = _parse_reference(self.text, self.pos)
            if node is None:
                raise VelocityException(f"引用无法解析: {self.text!r}")
            self.pos = after
            return ("ref", node)
        if char.isdigit() or (char == "-" and self.pos + 1 < self.length and self.text[self.pos + 1].isdigit()):
            return self._number()
        if char == "{":
            return self._map_literal()
        if char.isalpha() or char == "_":
            # 裸标识符（例如 ``#foreach`` 里已经单独切走的 in 之外的意外情况）
            start = self.pos
            while self.pos < self.length and _is_identifier_char(self.text[self.pos]):
                self.pos += 1
            return ("str", self.text[start:self.pos], False)
        raise VelocityException(f"表达式无法解析: {self.text!r}（位置 {self.pos}）")

    def _map_literal(self) -> Any:
        """Velocity 2.x 的 map 字面量 ``{"flag": 'add', "id": ''}``.

        ``vm/vue/index.vue.vm`` 里的 ``this.$refs.dialogForm.init({"flag": 'add', "id": ''})``
        会被当成 ``$refs`` 引用的实参解析，所以必须认得 ``{...}`` —— 不认识就会像当初
        那样把整份模板抛 ``ParseErrorException``。
        """
        self.pos += 1
        entries: List[Any] = []
        while True:
            self._skip_space()
            if self.pos >= self.length:
                raise VelocityException(f"map 字面量没有闭合: {self.text!r}")
            if self.text[self.pos] == "}":
                self.pos += 1
                break
            key = self._or()
            self._skip_space()
            if self.pos >= self.length or self.text[self.pos] != ":":
                raise VelocityException(f"map 字面量缺少冒号: {self.text!r}")
            self.pos += 1
            value = self._or()
            entries.append((key, value))
            self._skip_space()
            if self.pos < self.length and self.text[self.pos] == ",":
                self.pos += 1
                continue
            if self.pos < self.length and self.text[self.pos] == "}":
                self.pos += 1
                break
            raise VelocityException(f"map 字面量无法解析: {self.text!r}")
        return ("map", entries)

    def _number(self) -> Any:
        start = self.pos
        if self.text[self.pos] == "-":
            self.pos += 1
        seen_dot = False
        while self.pos < self.length:
            char = self.text[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == "." and not seen_dot:
                seen_dot = True
                self.pos += 1
            else:
                break
        raw = self.text[start:self.pos]
        return ("lit", float(raw) if seen_dot else int(raw))


def _read_string_literal(text: str, pos: int) -> Tuple[str, int]:
    """读带引号的字符串，返回 ``(内容, 结束下标)``；``\\`` 转义按 Java 处理."""
    quote = text[pos]
    index = pos + 1
    length = len(text)
    buffer: List[str] = []
    while index < length:
        char = text[index]
        if char == "\\" and index + 1 < length:
            nxt = text[index + 1]
            buffer.append({"n": "\n", "t": "\t", "r": "\r"}.get(nxt, nxt))
            index += 2
            continue
        if char == quote:
            return "".join(buffer), index + 1
        buffer.append(char)
        index += 1
    raise VelocityException(f"字符串没有闭合引号: {text[pos:]!r}")


# --------------------------------------------------------------------------- 求值


def _eval(node: Any, context: VelocityContext) -> Any:
    kind = node[0]
    if kind == "lit":
        return node[1]
    if kind == "ref":
        return node[1].evaluate(context)
    if kind == "str":
        content, interpolate = node[1], node[2]
        if not interpolate:
            return content
        return render_string(content, context)
    if kind == "not":
        return not _truthy(_eval(node[1], context))
    if kind == "map":
        return {_to_java_string(_eval(key, context)): _eval(value, context) for key, value in node[1]}
    operator = node[1]
    left = _eval(node[2], context)
    # ``&&`` / ``||`` 短路求值（模板里右侧可能有副作用以外的方法调用）
    if operator == "&&":
        return _truthy(left) and _truthy(_eval(node[3], context))
    if operator == "||":
        return _truthy(left) or _truthy(_eval(node[3], context))
    right = _eval(node[3], context)
    if operator == "+":
        return _java_add(left, right)
    if operator == "==":
        return _java_equals(left, right)
    if operator == "!=":
        return not _java_equals(left, right)
    return _java_compare(operator, left, right)


def _truthy(value: Any) -> bool:
    """``#if`` 的真假判定.

    Velocity 2.x：``null`` 为假、``Boolean`` 取自身、其余**非空**对象为真；空串与空
    集合按"空"处理（模板里所有字符串判断都显式写了 ``!= ""``，所以这里与 1.7 的
    差异不可观测）。
    """
    if value is UNDEFINED or value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value != ""
    if isinstance(value, (list, tuple, dict, set, frozenset)):
        return len(value) > 0
    return True


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _java_equals(left: Any, right: Any) -> bool:
    if left is UNDEFINED:
        left = None
    if right is UNDEFINED:
        right = None
    if left is None or right is None:
        return left is None and right is None
    if _is_number(left) and _is_number(right):
        return left == right
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    return _to_java_string(left) == _to_java_string(right)


def _java_compare(operator: str, left: Any, right: Any) -> Any:
    """``>`` ``>=`` ``<`` ``<=`` —— 任一侧为 null 时 Velocity 返回 null（进 #if 即假）."""
    if left is UNDEFINED or left is None or right is UNDEFINED or right is None:
        return UNDEFINED
    if _is_number(left) and _is_number(right):
        a, b = left, right
    else:
        a, b = _to_java_string(left), _to_java_string(right)
    if operator == ">":
        return a > b
    if operator == ">=":
        return a >= b
    if operator == "<":
        return a < b
    return a <= b


def _java_add(left: Any, right: Any) -> Any:
    """``+``：两侧都是数字做加法，否则字符串拼接（null 当空串）."""
    if left is UNDEFINED:
        left = None
    if right is UNDEFINED:
        right = None
    if _is_number(left) and _is_number(right):
        return left + right
    return _to_java_string(left) + _to_java_string(right)


def _to_java_string(value: Any) -> str:
    """Java ``String.valueOf`` / ``toString`` 的近似."""
    if value is UNDEFINED or value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_to_java_string(item) for item in value) + "]"
    return str(value)


def _snake(name: str) -> str:
    """``dialogNumber`` -> ``dialog_number``（只处理小写-大写边界，与 settings 一致）."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def _get_property(target: Any, name: str) -> Any:
    """读属性：先按 Java 名，再按 snake_case 名。"""
    if target is UNDEFINED or target is None:
        return UNDEFINED
    if isinstance(target, dict):
        if name in target:
            return target[name]
        return target.get(_snake(name), UNDEFINED)
    snake = _snake(name)
    candidates = (snake, name) if snake != name else (name,)
    for candidate in candidates:
        if candidate.startswith("_"):
            continue
        try:
            return getattr(target, candidate)
        except AttributeError:
            continue
    return UNDEFINED


def _call_method(target: Any, name: str, args: Sequence[Any]) -> Any:
    """调用方法：先覆盖 Java 字符串/集合 API，再退回同名（或 snake_case）方法."""
    if target is UNDEFINED or target is None:
        return UNDEFINED
    if isinstance(target, str):
        if name == "substring":
            start = int(args[0])
            end = len(target) if len(args) < 2 else int(args[1])
            return target[start:end]
        if name == "indexOf":
            start = 0 if len(args) < 2 else int(args[1])
            return target.find(_to_java_string(args[0]), start)
        if name == "length":
            return len(target)
        if name == "trim":
            return java_trim(target)
        if name == "toUpperCase":
            return target.upper()
        if name == "toLowerCase":
            return target.lower()
        if name == "matches":
            return re.fullmatch(_to_java_string(args[0]), target) is not None
        if name == "equals":
            return target == args[0]
        if name == "equalsIgnoreCase":
            return target.lower() == _to_java_string(args[0]).lower()
        if name == "isEmpty":
            return target == ""
        if name == "contains":
            return _to_java_string(args[0]) in target
        if name == "toString":
            return target
    if isinstance(target, (list, tuple, dict, set, frozenset)):
        if name == "size":
            return len(target)
        if name == "isEmpty":
            return len(target) == 0
        if name == "get":
            try:
                return target[args[0]]
            except (IndexError, KeyError, TypeError):
                return UNDEFINED
        if name == "contains":
            return args[0] in target
    method = getattr(target, _snake(name), None)
    if method is None:
        method = getattr(target, name, None)
    if method is None or not callable(method):
        return UNDEFINED
    return method(*args)


def _render_nodes(nodes: Sequence[_Node], context: VelocityContext, out: List[str]) -> None:
    for node in nodes:
        node.render(context, out)


def render_string(content: str, context: VelocityContext) -> str:
    """渲染"字符串字面量内部"（双引号串的插值）."""
    out: List[str] = []
    _render_nodes(_Parser(content).parse(), context, out)
    return "".join(out)


# --------------------------------------------------------------------------- 解析器


_IF_STOPS = frozenset({"end", "else", "elseif"})
_END_ONLY = frozenset({"end"})


class _Parser:
    """把（已经做过空行吞噬的）模板文本解析成节点树."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.length = len(source)

    def parse(self) -> List[_Node]:
        nodes, terminator, _arg = self._parse_block(frozenset())
        if terminator is not None:  # pragma: no cover - 模板语法本身有问题
            raise VelocityException(f"多余的 #{terminator}")
        return nodes

    # ---------------------------------------------------------------- 块
    def _parse_block(self, stops: frozenset) -> Tuple[List[_Node], Optional[str], Optional[str]]:
        nodes: List[_Node] = []
        while self.pos < self.length:
            char = self.source[self.pos]
            if char == "#":
                scanned = _scan_directive(self.source, self.pos)
                if scanned is None:
                    nodes.append(_TextNode("#"))
                    self.pos += 1
                    continue
                name, arg, after = scanned
                if name == "comment":
                    self.pos = after
                    continue
                if name == "raw":
                    nodes.append(_TextNode(arg or ""))
                    self.pos = after
                    continue
                if name in stops:
                    self.pos = after
                    return nodes, name, arg
                if name == "if":
                    nodes.append(self._parse_if(arg or "", after))
                elif name == "foreach":
                    nodes.append(self._parse_foreach(arg or "", after))
                elif name == "set":
                    nodes.append(self._parse_set(arg or "", after))
                elif name == "break":
                    nodes.append(_BreakNode())
                    self.pos = after
                elif name == "stop":
                    self.pos = self.length
                else:
                    # 游离的 #end / #else —— 原样吐出，别丢字符
                    nodes.append(_TextNode(self.source[self.pos:after]))
                    self.pos = after
                continue
            if char == "$":
                node, after = _parse_reference(self.source, self.pos)
                if node is None:
                    nodes.append(_TextNode("$"))
                    self.pos += 1
                else:
                    nodes.append(node)
                    self.pos = after
                continue
            match = _SPECIAL.search(self.source, self.pos)
            end = match.start() if match else self.length
            nodes.append(_TextNode(self.source[self.pos:end]))
            self.pos = end
        return nodes, None, None

    # ---------------------------------------------------------------- 指令
    def _parse_if(self, arg: str, after: int) -> _IfNode:
        self.pos = after
        branches: List[Tuple[Any, List[_Node]]] = []
        condition = _parse_expression(arg)
        body, terminator, terminator_arg = self._parse_block(_IF_STOPS)
        branches.append((condition, body))
        while terminator == "elseif":
            condition = _parse_expression(terminator_arg or "")
            body, terminator, terminator_arg = self._parse_block(_IF_STOPS)
            branches.append((condition, body))
        else_nodes: List[_Node] = []
        if terminator == "else":
            else_nodes, terminator, _ = self._parse_block(_END_ONLY)
        if terminator != "end":
            raise VelocityException("#if 缺少对应的 #end")
        return _IfNode(branches, else_nodes)

    def _parse_foreach(self, arg: str, after: int) -> _ForeachNode:
        self.pos = after
        match = _FOREACH_PATTERN.match(arg)
        if not match:
            raise VelocityException(f"#foreach 语法错误: {arg!r}")
        var_name = match.group(1)
        iterable = _parse_expression(match.group(2))
        body, terminator, _ = self._parse_block(_END_ONLY)
        if terminator != "end":
            raise VelocityException("#foreach 缺少对应的 #end")
        return _ForeachNode(var_name, iterable, body)

    def _parse_set(self, arg: str, after: int) -> _SetNode:
        self.pos = after
        split_at = _find_assignment(arg)
        if split_at == -1:
            raise VelocityException(f"#set 语法错误: {arg!r}")
        left = arg[:split_at]
        right = arg[split_at + 1:]
        match = _SET_LHS_PATTERN.match(left)
        if not match:
            raise VelocityException(f"#set 左侧必须是简单变量: {left!r}")
        return _SetNode(match.group(1), _parse_expression(right))


def _find_assignment(arg: str) -> int:
    """找 ``#set`` 里的赋值号（跳过 ``==`` / ``!=`` / ``>=`` / ``<=`` 与括号内）."""
    depth = 0
    index = 0
    length = len(arg)
    while index < length:
        char = arg[index]
        if char in "\"'":
            index = _skip_string(arg, index)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "=" and depth == 0:
            previous = arg[index - 1] if index else ""
            following = arg[index + 1] if index + 1 < length else ""
            if previous not in "=!<>" and following != "=":
                return index
        index += 1
    return -1


# --------------------------------------------------------------------------- 模板


class VelocityTemplate:
    """Java: ``org.apache.velocity.Template``."""

    __slots__ = ("name", "_nodes")

    def __init__(self, name: str, source: str) -> None:
        self.name = name
        self._nodes = _Parser(_strip_directive_only_lines(source)).parse()

    def merge(self, context: VelocityContext) -> str:
        """Java: ``void merge(Context context, Writer writer)`` —— 这里直接返回字符串."""
        out: List[str] = []
        _render_nodes(self._nodes, context, out)
        return "".join(out)


#: 模板缓存 —— Java 侧 Velocity 也带 resource loader 缓存，重复预览不会重复读盘。
_TEMPLATE_CACHE: Dict[str, VelocityTemplate] = {}


def get_template(name: str) -> VelocityTemplate:
    """Java: ``Velocity.getTemplate(String name, String encoding)``.

    ``name`` 是 **classpath 相对路径**（``vm/java/domain.java.vm``），在 Python 侧对应
    ``config/vm/java/domain.java.vm``。
    """
    cached = _TEMPLATE_CACHE.get(name)
    if cached is not None:
        return cached
    path = TEMPLATE_ROOT / name
    if not path.is_file():
        # Java: ResourceNotFoundException，被 GenTableServiceImpl 包成 IOException
        raise VelocityException(f"模板不存在: {name}")
    template = VelocityTemplate(name, path.read_text(encoding=TEMPLATE_ENCODING))
    _TEMPLATE_CACHE[name] = template
    return template


def clear_template_cache() -> None:
    """测试辅助：清空模板缓存."""
    _TEMPLATE_CACHE.clear()


__all__ = [
    "TEMPLATE_ROOT",
    "TEMPLATE_ENCODING",
    "UNDEFINED",
    "VelocityContext",
    "VelocityException",
    "VelocityTemplate",
    "get_template",
    "clear_template_cache",
    "render_string",
]
