#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HenDa 签名的独立参照实现（Python 标准库），用来钉住 tests/encrypt_utils_test.cpp。

Java 侧 EncryptUtils.createSignature 里是 `publicStr.append(publicStr).append("&"+str)`
—— 每轮把累加量翻倍再追加。这是 bug，但服务端认的就是它，所以移植必须逐字复刻；
参照值由本脚本按同样的规则算出，避免"C++ 和自己的单测互相印证"。

用法：python scripts/henda_sig_ref.py [nonce] [timestamp]
"""
import hashlib
import sys

APPID = "YHZS"
SECRET = "b48381c4b98311ea90b100155d14fa3b"


def source(appid, timestamp, nonce, secret, json_str):
    strip = lambda s: s.replace("[", "").replace("]", "")
    parts = sorted([strip(appid), strip(timestamp), strip(nonce), secret])
    pub = ""
    for s in parts:
        pub = s if pub == "" else pub + pub + "&" + s
    body = json_str.replace("\n", "").replace(" ", "")
    return pub + "&" + body


if __name__ == "__main__":
    nonce = sys.argv[1] if len(sys.argv) > 1 else "1369353600000"
    ts = sys.argv[2] if len(sys.argv) > 2 else "20130524080000"
    src = source(APPID, ts, nonce, SECRET, nonce)
    print("SORTED   =", sorted([APPID, ts, nonce, SECRET]))
    print("SOURCE   =", src)
    print("LEN      =", len(src))
    print("MD5      =", hashlib.md5(src.encode("utf-8")).hexdigest())
