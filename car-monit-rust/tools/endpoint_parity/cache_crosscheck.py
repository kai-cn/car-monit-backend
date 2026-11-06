"""跨端缓存共存检查：`car_lxgh:*`（轨迹路径规划结果）由一端写成 FastJson2 的形状后，
另一端必须能按 String 读出来。

背景：双端各连自己的 Redis db（Java=db0 / Rust=db15），平时互不读对方的键；
但 Rust 写的是 serde_json 的 `"..."`（带引号的 JSON 字符串），Java 写的是 FastJson2 的
同一形状。这个脚本把 **一端的值按字节抄到另一端的 db**，再让「读的那端」命中缓存路径，
证明两种写法在对方读取方眼里等价。

    python -m tools.endpoint_parity.cache_crosscheck            # 双向各测一次

脚本先把两端的原值都抓在手里，抄完再还原，所以跑完缓存内容与跑前一致。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import (JAVA_BASE, RUST_BASE, http, login, redis_cmd)  # noqa: E402,F401

KEY_PREFIX = 'car_lxgh:'
SUSPICIOUS_ID = os.environ.get('CROSSCHECK_ID', '2019309574142369799')


def raw_get(key, db):
    """读原始字节串（不剥引号），用于逐字节搬运。"""
    return redis_cmd('GET', key, db=db)


def raw_set(key, value, db):
    return redis_cmd('SET', key, value, db=db)


def paths_of(payload):
    """从 /manager/suspicious/{id} 的响应里取出 raodTrailList 的 paths 与 lxbh。"""
    out = []
    data = payload.get('data') or {}
    for info in data.get('trailList') or []:
        for geo in info.get('raodTrailList') or []:
            out.append((geo.get('lxbh'), str(geo.get('paths') or '')))
    return out


def call(base, token):
    status, _, body = http('GET', base + '/manager/suspicious/%s' % SUSPICIOUS_ID,
                           token=token, timeout=300)
    return status, json.loads(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    java_keys = [k for k in (redis_cmd('KEYS', KEY_PREFIX + '*', db=0) or [])]
    rust_keys = [k for k in (redis_cmd('KEYS', KEY_PREFIX + '*', db=15) or [])]
    print('db0 keys=%d db15 keys=%d' % (len(java_keys), len(rust_keys)))
    if not java_keys or not rust_keys:
        print('两端都得先有至少一个 car_lxgh 缓存（各跑一次 /manager/suspicious 即可）')
        return 2

    tj = login(JAVA_BASE)[0]
    tr = login(RUST_BASE)[0]
    # 基准：两端各自命中自己缓存时的输出
    _, pj = call(JAVA_BASE, tj)
    _, pr = call(RUST_BASE, tr)
    base_j, base_r = paths_of(pj), paths_of(pr)
    print('命中各自缓存：java=%s rust=%s' % ([(l, len(p)) for l, p in base_j],
                                             [(l, len(p)) for l, p in base_r]))

    # 先把两端的原值都抓在手里：两轮抄写之间不还原，否则第二轮拿到的就是第一轮抄过去的值，
    # 变成「Java 的值给 Java 读」这种自证的空测试。
    key = (redis_cmd('KEYS', KEY_PREFIX + '*', db=0) or [''])[0]
    original = {0: raw_get(key, 0), 15: raw_get(key, 15)}
    if not original[0] or not original[15]:
        print('两端都必有 %s%s（分别命中一次缓存即可）' % (KEY_PREFIX, key[len(KEY_PREFIX):]))
        return 2
    print('源值长度 db0=%s db15=%s' % (len(original[0]), len(original[15])))

    failures = 0
    for src_db, dst_db, label, base, token in (
        (15, 0, 'Rust 写的值 -> Java 读', JAVA_BASE, tj),
        (0, 15, 'Java 写的值 -> Rust 读', RUST_BASE, tr),
    ):
        value = original[src_db]
        raw_set(key, value, db=dst_db)
        status, payload = call(base, token)
        got = paths_of(payload)
        # 缓存值是 FastJson2/serde_json 写的 JSON 字符串（外层带引号），
        # 出参应当与去掉引号的原文逐字符相同。
        inner = value[1:-1] if value.startswith('"') and value.endswith('"') else value
        read = got[0][1] if got else None
        match = read == inner
        print('%s: 源值=%d 出参=%s %s' % (
            label, len(inner), len(read or ''), 'OK（逐字节一致）' if match else 'FAIL'))
        if not match:
            failures += 1
            print('     status=%s code=%s msg=%s' % (status, payload.get('code'),
                                                     str(payload.get('msg'))[:80]))

    for db, value in original.items():
        if value is None:
            redis_cmd('DEL', key, db=db)
        else:
            raw_set(key, value, db=db)
    print('已还原两端的原缓存值')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
