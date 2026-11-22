#!/usr/bin/env python3

"""
@description 历史脚本 download-mandrel-linux.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python download-mandrel-linux.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Download a build artifact or log through the GitHub API.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Download a pinned Mandrel Linux amd64 tarball + verify its sha256.



Usage:

  python download-mandrel-linux.py [output-dir] [jdk]

    output-dir : default D:\\jdk  (also reachable from WSL as /mnt/d/jdk)

    jdk        : 25 (default) | 21 | 17



Pinned, reproducible releases (GraalVM/mandrel official GitHub releases):

  25 -> mandrel-25.0.4.1-Final  (the exact build verified on this host)

  21 -> mandrel-23.1.13.0-Final

  17 -> mandrel-23.0.6.0-Final



Reproducibility notes (verified on this host 2026-11-15):

  * curl.exe fails with "CONNECT tunnel failed, response 502" through the

    WorkBuddy https_proxy; urllib (same proxy) works for api.github.com.

  * github.com/.../releases/download/... direct asset links get

    RemoteDisconnected. The GitHub API asset endpoint with

    "Accept: application/octet-stream" works (redirects to

    release-assets.githubusercontent.com).

  * Large transfers may drop; Range-based resume + retries are implemented.

"""

import hashlib

import json

import os

import sys

import time

import urllib.error

import urllib.request



PINS = {

    "25": "mandrel-25.0.4.1-Final",

    "21": "mandrel-23.1.13.0-Final",

    "17": "mandrel-23.0.6.0-Final",

}

UA = {"User-Agent": "WorkBuddy-ops/1.0"}

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else r"D:\jdk"

JDK = sys.argv[2] if len(sys.argv) > 2 else "25"

if JDK not in PINS:

    print("UNSUPPORTED_JDK %s (choose 25/21/17)" % JDK, flush=True)

    sys.exit(2)

TAG = PINS[JDK]

RELEASE_API = "https://api.github.com/repos/graalvm/mandrel/releases/tags/" + TAG

MAX_RETRY = 8





def api_json(url):

    req = urllib.request.Request(url, headers=UA)

    with urllib.request.urlopen(req, timeout=30) as r:

        return json.load(r)





def api_text(url):

    req = urllib.request.Request(url, headers={**UA, "Accept": "application/octet-stream"})

    with urllib.request.urlopen(req, timeout=60) as r:

        return r.read().decode("utf-8").strip()





def sha256(path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):

            h.update(b)

    return h.hexdigest()





def resume_download(asset_url, expected_size, part):

    """Append to `part` using Range, retry on disconnect."""

    for attempt in range(1, MAX_RETRY + 1):

        have = os.path.getsize(part) if os.path.isfile(part) else 0

        if have >= expected_size:

            return have

        headers = {**UA, "Accept": "application/octet-stream", "Range": "bytes=%d-" % have}

        try:

            with urllib.request.urlopen(urllib.request.Request(asset_url, headers=headers),

                                        timeout=180) as r:

                if have and r.status != 206:

                    print("  server ignored Range (status %d), restarting" % r.status, flush=True)

                    have, mode = 0, "wb"

                else:

                    mode = "ab" if have else "wb"

                t0, got = time.time(), 0

                with open(part, mode) as f:

                    while True:

                        chunk = r.read(1024 * 1024)

                        if not chunk:

                            break

                        f.write(chunk)

                        got += len(chunk)

                        if got // (25 * 1024 * 1024) != (got - len(chunk)) // (25 * 1024 * 1024):

                            print("  +%.1f MB (total %.1f/%.1f MB)" % (

                                got / 1e6, (have + got) / 1e6, expected_size / 1e6), flush=True)

            print("  attempt %d: received %.1f MB in %.1fs" % (

                attempt, got / 1e6, time.time() - t0), flush=True)

        except Exception as e:

            print("  attempt %d: %s: %s" % (attempt, type(e).__name__, e), flush=True)

        have = os.path.getsize(part) if os.path.isfile(part) else 0

        if have >= expected_size:

            return have

        time.sleep(2)

    return os.path.getsize(part) if os.path.isfile(part) else 0





def main():

    os.makedirs(OUT_DIR, exist_ok=True)

    rel = api_json(RELEASE_API)

    assets = {a["name"]: a for a in rel["assets"]}

    prefix = "mandrel-java%s-linux-amd64-" % JDK

    matches = [n for n in assets if n.startswith(prefix) and n.endswith(".tar.gz")]

    if not matches:

        print("ASSET_NOT_FOUND for %s in %s" % (prefix, TAG), flush=True)

        return 3

    asset = sorted(matches)[0]

    expected_size = assets[asset]["size"]

    expected_hash = None

    checksum_name = asset + ".sha256"

    if checksum_name in assets:

        expected_hash = api_text(assets[checksum_name]["url"]).split()[0]

    dest = os.path.join(OUT_DIR, asset)

    part = dest + ".part"

    print("release     =", rel["tag_name"], flush=True)

    print("asset       =", asset, flush=True)

    print("asset_url   =", assets[asset]["url"], flush=True)

    print("size        =", expected_size, flush=True)

    print("sha256      =", expected_hash or "<no checksum asset; size check only>", flush=True)



    if os.path.isfile(dest) and os.path.getsize(dest) == expected_size:

        if expected_hash is None or sha256(dest) == expected_hash:

            print("ALREADY_OK size=%d bytes -> %s" % (os.path.getsize(dest), dest), flush=True)

            return 0



    size = resume_download(assets[asset]["url"], expected_size, part)

    if size != expected_size:

        print("INCOMPLETE got=%d expected=%d" % (size, expected_size), flush=True)

        return 4

    actual = sha256(part)

    print("local sha256 =", actual, flush=True)

    if expected_hash and actual != expected_hash:

        print("SHA256_MISMATCH", flush=True)

        return 2

    os.replace(part, dest)

    print("SHA256_OK ->", dest, os.path.getsize(dest), "bytes", flush=True)

    return 0





if __name__ == "__main__":

    sys.exit(main())

