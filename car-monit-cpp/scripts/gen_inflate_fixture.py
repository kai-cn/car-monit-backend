#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成 tests/wip/data_inflate.h（INFLATE 单测的参照数据）。

为什么要有这个脚本：参照数据必须能用标准库复算，否则"C++ 和自己的单测互相印证"没有意义。
分别产出三种 DEFLATE 块形态（RFC 1951）：
  * Dynamic  默认策略，内容够长 ⇒ BTYPE=10
  * Fixed    strategy=Z_FIXED ⇒ BTYPE=01
  * Stored   level=0 ⇒ BTYPE=00
外加 zlib（RFC 1950）与 gzip（RFC 1952）两种外壳。

用法：python scripts/gen_inflate_fixture.py
"""
import io
import os
import random
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "wip", "data_inflate.h")

random.seed(7)
TEXT = "".join(random.choice("abcdefghij klmn0123456789opqrstuvwxyz 中文测试ABC")
               for _ in range(3000))
DATA = TEXT.encode("utf-8")


def raw_stream(level, strategy=zlib.Z_DEFAULT_STRATEGY):
    co = zlib.compressobj(level, zlib.DEFLATED, -15, 8, strategy)
    return co.compress(DATA) + co.flush()


def emit(out, name, blob):
    out.write("inline const std::string kInflate%s() {\n    static const unsigned char v[] = {%s};\n"
              "    return std::string(reinterpret_cast<const char*>(v), sizeof v);\n}\n\n"
              % (name, ",".join(str(b) for b in blob)))


def main():
    dyn = raw_stream(6)
    fix = raw_stream(6, zlib.Z_FIXED)
    stored = raw_stream(0)
    for label, blob in (("dynamic", dyn), ("fixed", fix), ("stored", stored)):
        print("%-8s BTYPE=%d" % (label, blob[0] >> 1 & 3))
    io.open(OUT, "w", encoding="utf-8").write(
        "// 由 scripts/gen_inflate_fixture.py 调 python zlib 生成，供 tests/wip/inflate_test.cpp 对拍。\n"
        "// 全部按字节数组写死，避免把非 ASCII 文本直接嵌进 C++ 源码带来编码问题。别手改。\n"
        "#pragma once\n#include <string>\n\n")
    with io.open(OUT, "a", encoding="utf-8") as out:
        emit(out, "Expected", DATA)
        emit(out, "Deflate", dyn)
        emit(out, "Fixed", fix)
        emit(out, "Stored", stored)
        emit(out, "Zlib", zlib.compress(DATA, 6))
        g = zlib.compressobj(6, zlib.DEFLATED, 31)
        emit(out, "Gzip", g.compress(DATA) + g.flush())
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
