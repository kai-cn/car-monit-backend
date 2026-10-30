"""easypoi Word 模板导出（``WordExportUtil`` + ``ImageEntity``）.

# Migrated from: cn.afterturn.easypoi.word.WordExportUtil
# Migrated from: cn.afterturn.easypoi.entity.ImageEntity

Java 侧用法（本工程只有 ``CarSuspiciousController#exportAbnormalPassage`` 一处）::

    Map<String, Object> map = new HashMap<>();
    map.put("carNo", "...");
    ImageEntity image = new ImageEntity(byteObject, 250, 250);
    image.setType(ImageEntity.Data);
    map.put("susImg" + i, image);

    XWPFDocument workbook = WordExportUtil.exportWord07(
        "templates/export/carSuspicious.docx", map);

模板长什么样
------------
``templates/export/carSuspicious.docx`` 是 ``.docx``（一个 zip），占位符写在
``word/document.xml`` 的 ``<w:t>`` 里：

* 标量 ``{{carNo}}`` / ``{{chargeAmount}}`` / … —— **经常被 Word 拆到多个 run**，
  所以必须先把整段的 ``<w:t>`` 文本拼起来再匹配，否则一个都替换不到；
* 图片 ``{{susImg1}}`` … ``{{susImg7}}`` —— 单独一个 run。

与 easypoi 的差异（这里只有三处，都是有意的）
---------------------------------------------
1. **未知占位符原样留下** —— easypoi 也只替换 map 里有的 key，模板里多写的
   ``{{xxx}}`` 会原样输出。照抄。
2. **图片只支持"占位符独占一个 run"** —— 本工程的模板确实如此；跨 run 的图片
   占位符会退化成一个文本占位符（原样留下）。
3. 不处理 ``{{!var}}``、``fn:`` 函数、``$fe`` 循环行、页眉页脚 —— 模板里没有，
   引擎不装。

宽度高度单位
------------
``ImageEntity(byte[], width, height)`` 的 ``width`` / ``height`` 是**像素**，
``docx`` 的 ``wp:extent`` 用 EMU（1 px = 9525 EMU），这里显式换算。
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from app.common.utils.image_utils import content_type_of
from app.settings import PROJECT_ROOT

#: classpath 根 ``templates/export/xxx.docx`` 在 Python 侧的对应目录
#: （与 :mod:`app.common.utils.poi.template_export` 同一个根）。
TEMPLATES_ROOT: Path = PROJECT_ROOT / "config"

#: 1 px = 9525 EMU（``docx`` 的 EMU 定义）
EMU_PER_PIXEL = 9525

#: ``<w:t>`` 元素（``<w:tbl>`` / ``<w:tr>`` / ``<w:tc>`` 等不会被误匹配）。
_WT_RE = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.DOTALL)
#: 一个完整的 ``<w:r ...>…</w:r>``。
_RUN_RE = re.compile(r"<w:r(?:\s[^>]*)?>.*?</w:r>", re.DOTALL)
#: ``{{name}}``
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

_XML_ESCAPES = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
)


class ImageEntity:
    """Java: ``cn.afterturn.easypoi.entity.ImageEntity`` —— 只保留本工程用到的形式."""

    #: Java: ``ImageEntity.Data`` —— 直接给 ``byte[]``
    DATA = "data"
    #: Java: ``ImageEntity.Url`` —— 给一个 URL（本工程未使用）
    URL = "url"

    def __init__(self, data: Optional[bytes] = None, width: int = 0, height: int = 0) -> None:
        self.data = data
        self.width = width
        self.height = height
        #: Java: ``image.setType(ImageEntity.Data)``
        self.type = ImageEntity.DATA
        #: 图片后缀（``png`` / ``jpg`` …）—— Java 侧由 easypoi 从魔数推断。
        self.extension = "png"

    def set_type(self, image_type: str) -> None:
        """Java: ``image.setType(String)``."""
        self.type = image_type

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        size = 0 if self.data is None else len(self.data)
        return f"ImageEntity({size} bytes, {self.width}x{self.height}, {self.extension!r})"


class WordDocument:
    """``XWPFDocument`` 的最小替身：只管 ``write(OutputStream)``."""

    def __init__(self, parts: Mapping[str, bytes], order: List[str]) -> None:
        self._parts = dict(parts)
        self._order = list(order)

    def write(self, output: Any) -> None:
        """把 zip 写进 ``output``（``io.BytesIO`` 或文件对象）."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in self._order:
                archive.writestr(name, self._parts[name])
        payload = buffer.getvalue()
        output.write(payload)

    def to_bytes(self) -> bytes:
        buffer = io.BytesIO()
        self.write(buffer)
        return buffer.getvalue()


class WordExportUtil:
    """Java: ``static XWPFDocument exportWord07(String url, Map<String,Object> map)``."""

    @staticmethod
    def export_word07(template_url: str, data: Mapping[str, Any]) -> WordDocument:
        path = TEMPLATES_ROOT / template_url
        with zipfile.ZipFile(path) as archive:
            order = list(archive.namelist())
            parts = {name: archive.read(name) for name in order}

        #: 累计的图片序号 —— 决定 ``media/imageN.png`` 与 ``rIdN`` 的编号。
        images = _ImageCollector()
        document = parts["word/document.xml"].decode("utf-8")

        document = _render_images(document, data, images)
        document = _render_text(document, data)
        parts["word/document.xml"] = document.encode("utf-8")

        if images.count:
            _attach_images(parts, order, images)
        return WordDocument(parts, order)


# --------------------------------------------------------------------------- 图片


class _ImageCollector:
    """收集本次导出要嵌入的图片（有序，序号从 1 开始）."""

    def __init__(self) -> None:
        self.items: List[Tuple[int, bytes, str]] = []

    @property
    def count(self) -> int:
        return len(self.items)

    def add(self, data: bytes, extension: str) -> int:
        index = len(self.items) + 1
        self.items.append((index, data, extension))
        return index


def _render_images(
    document: str, data: Mapping[str, Any], images: _ImageCollector
) -> str:
    """把"独占一个 run"的 ``{{susImgN}}`` 换成 ``<w:drawing>``."""
    image_keys = {
        key: value
        for key, value in data.items()
        if isinstance(value, ImageEntity) and value.type == ImageEntity.DATA
    }
    if not image_keys:
        return document

    def replace_run(match: "re.Match[str]") -> str:
        run = match.group(0)
        texts = _WT_RE.findall(run)
        if len(texts) != 1:
            return run
        name = _sole_placeholder(texts[0])
        if name is None or name not in image_keys:
            return run
        entity = image_keys[name]
        if not entity.data:
            return run
        index = images.add(entity.data, entity.extension)
        return _drawing_run(index, entity)

    return _RUN_RE.sub(replace_run, document)


def _sole_placeholder(text: str) -> Optional[str]:
    """``"{{susImg1}}"`` -> ``"susImg1"``；不是"只含一个占位符"就返回 ``None``."""
    match = _PLACEHOLDER_RE.fullmatch(text.strip())
    return None if match is None else match.group(1)


def _drawing_run(index: int, entity: ImageEntity) -> str:
    cx = max(1, entity.width) * EMU_PER_PIXEL
    cy = max(1, entity.height) * EMU_PER_PIXEL
    return (
        "<w:r><w:drawing>"
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        '<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{index + 100}" name="Picture {index}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks'
        ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
        ' noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{index}" name="image{index}.{entity.extension}"/>'
        "<pic:cNvPicPr/></pic:nvPicPr>"
        f'<pic:blipFill><a:blip r:embed="rIdImg{index}"/>'
        "<a:stretch><a:fillRect/></a:stretch></pic:blipFill>"
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
    )


def _attach_images(
    parts: Dict[str, bytes], order: List[str], images: _ImageCollector
) -> None:
    """补 ``word/media/*``、``document.xml.rels`` 与 ``[Content_Types].xml``."""
    rels_name = "word/_rels/document.xml.rels"
    rels = parts[rels_name].decode("utf-8")
    content_types = parts["[Content_Types].xml"].decode("utf-8")
    missing_defaults: List[str] = []

    for index, data, extension in images.items:
        media_name = f"word/media/image{index}.{extension}"
        parts[media_name] = data
        order.append(media_name)
        rels = rels.replace(
            "</Relationships>",
            f'<Relationship Id="rIdImg{index}"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"'
            f' Target="media/image{index}.{extension}"/></Relationships>',
        )
        if f'Extension="{extension}"' not in content_types:
            missing_defaults.append(extension)

    for extension in dict.fromkeys(missing_defaults):
        content_types = content_types.replace(
            "</Types>",
            f'<Default Extension="{extension}"'
            f' ContentType="{content_type_of(extension)}"/></Types>',
        )

    parts[rels_name] = rels.encode("utf-8")
    parts["[Content_Types].xml"] = content_types.encode("utf-8")


# --------------------------------------------------------------------------- 文本


class _TextGroup:
    """``word/document.xml`` 里的一个 ``<w:t>`` —— 记录它在 XML 与拼接文本中的位置."""

    def __init__(self, start: int, end: int, open_tag: str, text: str) -> None:
        self.start = start
        self.end = end
        self.open_tag = open_tag
        self.text = text
        #: 这段文本在拼接串里的起点（:func:`_render_text` 填）。
        self.offset = 0


def _render_text(document: str, data: Mapping[str, Any]) -> str:
    groups: List[_TextGroup] = []
    for match in _WT_RE.finditer(document):
        open_tag = match.group(0)[: match.group(0).index(">") + 1]
        groups.append(_TextGroup(match.start(), match.end(), open_tag, match.group(1)))
    if not groups:
        return document

    joined: List[str] = []
    owners: List[int] = []
    cursor = 0
    for index, group in enumerate(groups):
        group.offset = cursor
        joined.append(group.text)
        owners.extend([index] * len(group.text))
        cursor += len(group.text)
    full = "".join(joined)

    replacements = [
        match
        for match in _PLACEHOLDER_RE.finditer(full)
        if isinstance(data.get(match.group(1)), (str, int, float))
    ]
    # 从后往前替换 —— 同一个 ``<w:t>`` 里有多处占位符时，前面的下标不会被打乱。
    for match in reversed(replacements):
        value = str(data[match.group(1)])
        _apply(owners, groups, match.start(), match.end(), value)

    pieces: List[str] = []
    cursor = 0
    for group in groups:
        pieces.append(document[cursor : group.start])
        pieces.append(group.open_tag)
        pieces.append(_escape(group.text))
        pieces.append("</w:t>")
        cursor = group.end
    pieces.append(document[cursor:])
    return "".join(pieces)


def _apply(
    owners: List[int],
    groups: List[_TextGroup],
    start: int,
    end: int,
    value: str,
) -> None:
    """把 ``joined[start:end]`` 换成 ``value``，只写进**第一个**受影响的 ``<w:t>``."""
    spans: List[Tuple[int, int, int]] = []
    for position in range(start, end):
        owner = owners[position]
        local = position - groups[owner].offset
        if spans and spans[-1][0] == owner:
            previous = spans[-1]
            spans[-1] = (owner, previous[1], local + 1)
        else:
            spans.append((owner, local, local + 1))

    for index, (owner, local_start, local_end) in enumerate(spans):
        group = groups[owner]
        insert = value if index == 0 else ""
        group.text = group.text[:local_start] + insert + group.text[local_end:]


def _escape(text: str) -> str:
    for raw, encoded in _XML_ESCAPES:
        text = text.replace(raw, encoded)
    return text


__all__ = [
    "EMU_PER_PIXEL",
    "ImageEntity",
    "TEMPLATES_ROOT",
    "WordDocument",
    "WordExportUtil",
]
