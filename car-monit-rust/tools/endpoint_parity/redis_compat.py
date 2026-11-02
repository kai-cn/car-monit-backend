# -*- coding: utf-8 -*-
"""共存键体检：找出 Redis 里缺 FastJson2 `@type` 的共享缓存值。

背景：Java 侧用 `FastJson2JsonRedisSerializer`（WriteClassName）读写缓存，
读出来会直接强转成 `LoginUser` / `CarInfo` / `Geometry` 等类型。
如果同一个 Redis 被其它语言的端口（car-monit-py / car-monit-go 等）写入过
**不带 `@type`** 的值，Java 会抛
`com.alibaba.fastjson2.JSONObject cannot be cast to ...`，表现为接口 500
（`/monitor/online/list`、`/manager/bigScreen/carLocation` 等），
而 Rust 侧因为是按 JSON 解析的，照样返回 200 —— 两端就对不上了。

用法：

    python -m tools.endpoint_parity.redis_compat            # 只看报告
    python -m tools.endpoint_parity.redis_compat --apply     # 删掉这些键

删除是安全的：
* `login_tokens:*` 是无类型的过期/测试会话（Java 与 Rust 自己写的都带 `@type`），
  删掉等于踢掉那个会话；
* 其余都是缓存，下次读取时 Java / Rust 都会回源 DB 重建，并带上正确的 `@type`。

真正的修法是在其它端口的序列化里补 `@type`，这个工具只用于把共享环境拉回可比状态。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import redis_cmd

# 需要 @type 的共享键：模式 -> 说明
PATTERNS = {
    "login_tokens:*": "登录态（LoginUser）",
    "car_list": "车辆列表缓存",
    "car_list_jc": "车辆简称缓存",
    "white_car_list": "白名单缓存",
    "section_list": "路段缓存（OdsSzdnSection）",
    "car_warning_list": "预警缓存（CarWarningInfo）",
    "car_warning_config_list": "预警配置缓存（CarWarningConfig）",
    "lxbh_jdwd:*": "路线点位缓存（Geometry）",
    "sys_dict:*": "字典缓存（SysDictData）",
}


def typed(fragment: str) -> bool:
    """Java 的 FastJson2 会在对象头/数组首元素写 @type；空容器本来就无需 @type。"""
    text = (fragment or "").lstrip()
    if text in ("[]", "{}"):
        return True
    return text.startswith('{"@type"') or text.startswith('[{"@type"')


def scan() -> list[tuple[str, str, str]]:
    problems: list[tuple[str, str, str]] = []
    for pattern, note in PATTERNS.items():
        keys = redis_cmd("KEYS", pattern) or []
        if isinstance(keys, str):
            keys = [keys]
        for key in sorted(keys):
            if redis_cmd("TYPE", key) != "string":
                continue
            value = redis_cmd("GET", key) or ""
            if not value or value[0] not in "[{":
                continue  # 纯字符串值（如 sys_config:api_map）不需要 @type
            if not typed(value):
                problems.append((key, note, value[:60]))
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="删除缺 @type 的键（缓存会回源重建）")
    args = parser.parse_args(argv)

    problems = scan()
    if not problems:
        print("共享键都带 @type，Java 与 Rust 可比。")
        return 0
    for key, note, head in problems:
        print("%-46s %s  %s" % (key, note, head))
    print("\n缺 @type 的键：%d" % len(problems))
    if not args.apply:
        print("加 --apply 删除这些键（登录会话会被踢掉，缓存下次自动重建）")
        return 1
    deleted = 0
    for key, _, _ in problems:
        if redis_cmd("DEL", key) == 1:
            deleted += 1
    print("已删除 %d 个键；下次请求会由 Java/Rust 回源重建" % deleted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
