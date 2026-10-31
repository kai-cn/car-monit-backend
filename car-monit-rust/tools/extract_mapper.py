#!/usr/bin/env python3
"""把 mapper XML 压缩成移植用的摘要：展开 <include>，保留 <if>/<where>/<foreach> 语义。"""
import re
import sys
import xml.etree.ElementTree as ET


def text_of(node):
    return (node.text or "").strip() if node is not None else ""


def render(node, sql_frags):
    parts = []
    if node.text:
        parts.append(node.text)
    for child in node:
        tag = child.tag
        if tag == "include":
            frag = sql_frags.get(child.get("refid"))
            if frag is not None:
                parts.append(render(frag, sql_frags))
        elif tag == "if":
            inner = render(child, sql_frags)
            parts.append("\n  [if %s] %s" % (child.get("test"), " ".join(inner.split())))
        elif tag == "where":
            inner = render(child, sql_frags)
            parts.append("\n  [where] %s" % " ".join(inner.split()))
        elif tag == "trim":
            inner = render(child, sql_frags)
            parts.append("\n  [trim p=%r s=%r] %s" % (child.get("prefix"), child.get("suffix"), " ".join(inner.split())))
        elif tag == "foreach":
            sep = child.get("separator")
            inner = render(child, sql_frags)
            parts.append("\n  [foreach %s sep=%s] %s" % (child.get("collection"), sep, " ".join(inner.split())))
        elif tag == "choose":
            parts.append("\n  [choose] %s" % render(child, sql_frags))
        elif tag == "when":
            parts.append("\n  [when %s] %s" % (child.get("test"), " ".join(render(child, sql_frags).split())))
        elif tag == "otherwise":
            parts.append("\n  [otherwise] %s" % render(child, sql_frags))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def main(path):
    root = ET.parse(path).getroot()
    sql_frags = {n.get("id"): n for n in root.findall("sql")}
    for node in root:
        if node.tag not in ("select", "insert", "update", "delete"):
            continue
        body = render(node, sql_frags)
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\n\s*\n", "\n", body)
        print("### %s %s" % (node.tag, node.get("id")))
        print(body.strip())
        print()


if __name__ == "__main__":
    main(sys.argv[1])
