#!/usr/bin/env python3

"""
@description 历史脚本 find-lzma-refs.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python find-lzma-refs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Locate class files whose constant pool references LZMAInputStream.



Scans a Spring Boot fat jar (BOOT-INF/lib/*.jar + BOOT-INF/classes) in memory.

Usage: python find-lzma-refs.py <fat-jar> [needle]

"""

import io

import os

import sys

import zipfile



NEEDLES = [b"LZMAInputStream", b"tukaani/xz", b"pulsar/shade/org/tukaani"]





def main():

    jar = sys.argv[1] if len(sys.argv) > 1 else ""

    if not jar or not os.path.isfile(jar):

        print("USAGE: python find-lzma-refs.py <fat-jar>")

        return 2

    extra = sys.argv[2:] 

    needles = [n.encode() for n in (extra or ["LZMAInputStream"])]

    hits = []

    with zipfile.ZipFile(jar) as z:

        names = z.namelist()

        # inlined classes

        for n in names:

            if n.endswith(".class") and n.startswith("BOOT-INF/classes/"):

                data = z.read(n)

                if any(x in data for x in needles):

                    hits.append(("fatjar:" + n, [x.decode() for x in needles if x in data]))

        # nested jars

        for n in names:

            if not (n.startswith("BOOT-INF/lib/") and n.endswith(".jar")):

                continue

            data = z.read(n)

            try:

                inner = zipfile.ZipFile(io.BytesIO(data))

            except Exception as e:

                print("SKIP nested jar", n, e)

                continue

            for cn in inner.namelist():

                if cn.endswith(".class"):

                    cdata = inner.read(cn)

                    if any(x in cdata for x in needles):

                        hits.append((n + "!" + cn, [x.decode() for x in needles if x in cdata]))

    print("HITS=%d" % len(hits))

    for loc, matched in hits:

        print(loc, "->", ",".join(matched))

    return 0





if __name__ == "__main__":

    sys.exit(main())

