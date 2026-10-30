"""启动自检脚本 / startup smoke test.

# Migrated from: (no Java equivalent -- 手工 curl 检查)

用法 / Usage
-----------
先启动服务（另开一个终端）::

    python run.py

再执行::

    python scripts/smoke_test.py
    python scripts/smoke_test.py --base-url http://127.0.0.1:9989

退出码 / Exit code
------------------
``0`` = 全部通过；``1`` = 有失败项。可直接用于 CI / 部署后验证。

为什么不复用 pytest？
---------------------
pytest 走的是进程内 ``TestClient``，不经过真实的 socket、真实的 uvicorn 与真实的
中间件顺序。本脚本用 httpx 打真实端口，验证「部署后这套东西真的活着」。
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Tuple

import httpx

#: Java: 首页欢迎语（SysIndexController#index），name 取自 ruoyi.name
EXPECTED_INDEX_TEXT = "欢迎使用系统后台管理框架，请通过前端地址访问。"

#: 探测 404 用的未映射路径。**必须在安全过滤器白名单内**，否则鉴权会先于路由否决请求，
#: 回 HTTP 200 + ``code 401``（Java 的 ``FilterSecurityInterceptor`` 也排在
#: ``DispatcherServlet`` 之前，行为一致，不是缺陷）。``/profile/**`` 对 GET 是 ``permitAll``。
UNMAPPED_PERMIT_ALL_PATH = "/profile/definitely-not-a-route"


class CheckResult:
    """One assertion result, printed as OK / FAIL."""

    def __init__(self, name: str, ok: bool, detail: str = "") -> None:
        self.name = name
        self.ok = ok
        self.detail = detail

    def __str__(self) -> str:
        mark = "[ OK ]" if self.ok else "[FAIL]"
        return f"{mark} {self.name}" + (f" -> {self.detail}" if self.detail else "")


def _check_index(client: httpx.Client) -> CheckResult:
    """Java: GET / -> text/plain 欢迎语，HTTP 200。"""
    response = client.get("/")
    if response.status_code != 200:
        return CheckResult("GET / 状态码", False, f"期望 200, 实际 {response.status_code}")
    if response.text != EXPECTED_INDEX_TEXT:
        return CheckResult("GET / 响应正文", False, f"期望 {EXPECTED_INDEX_TEXT!r}, 实际 {response.text!r}")
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("text/plain"):
        return CheckResult("GET / Content-Type", False, f"期望 text/plain, 实际 {content_type}")
    return CheckResult("GET / 首页欢迎语", True, content_type)


def _check_trace_header(client: httpx.Client) -> CheckResult:
    """Java: TraceIdFilter 总是回写 X-Trace-Id 响应头。"""
    response = client.get("/", headers={"X-Trace-Id": "smoke-test-trace-id"})
    echoed = response.headers.get("X-Trace-Id")
    if echoed != "smoke-test-trace-id":
        return CheckResult("X-Trace-Id 透传", False, f"期望 smoke-test-trace-id, 实际 {echoed!r}")
    return CheckResult("X-Trace-Id 透传", True)


def _check_health(client: httpx.Client) -> Tuple[CheckResult, dict]:
    """健康检查：HTTP 永远 200，真实状态在 data.status。"""
    response = client.get("/health")
    if response.status_code != 200:
        return CheckResult("GET /health 状态码", False, f"期望 200, 实际 {response.status_code}"), {}
    try:
        body = response.json()
    except ValueError:
        return CheckResult("GET /health 响应体", False, "不是合法 JSON"), {}

    if body.get("code") != 200:
        return CheckResult("GET /health 业务码", False, f"期望 200, 实际 {body.get('code')!r}"), body

    data = body.get("data") or {}
    components = data.get("components") or {}
    missing = {"db", "redis"} - set(components)
    if missing:
        return CheckResult("GET /health 组件清单", False, f"缺少 {sorted(missing)}"), body

    status = data.get("status")
    detail = ", ".join(f"{name}={state}" for name, state in components.items())
    return CheckResult("GET /health 依赖状态", status == "UP", f"status={status} ({detail})"), body


def _check_404(client: httpx.Client) -> CheckResult:
    """未匹配路由：真实 404 + Spring BasicErrorController 的 JSON 体。

    为什么不用 ``/__smoke_test_not_a_route__``：那个路径不在白名单里，会被
    ``anyRequest().authenticated()`` 先判 401（HTTP 仍是 200），根本走不到 404 分支。
    """
    response = client.get(UNMAPPED_PERMIT_ALL_PATH)
    if response.status_code != 404:
        return CheckResult("未匹配路由 404", False, f"期望 404, 实际 {response.status_code}")
    body = response.json()
    expected_keys = {"timestamp", "status", "error", "path"}
    if set(body.keys()) != expected_keys:
        return CheckResult("未匹配路由响应体", False, f"期望字段 {sorted(expected_keys)}, 实际 {sorted(body.keys())}")
    if body.get("path") != UNMAPPED_PERMIT_ALL_PATH:
        return CheckResult("未匹配路由 path 字段", False, f"实际 {body.get('path')!r}")
    return CheckResult("未匹配路由 404 结构", True)


def _check_405(client: httpx.Client) -> CheckResult:
    """方法不支持：HTTP 200 + AjaxResult(500)，RuoYi 统一约定。"""
    response = client.post("/health")
    if response.status_code != 200:
        return CheckResult("405 降级为 HTTP 200", False, f"期望 200, 实际 {response.status_code}")
    body = response.json()
    expected_msg = "Request method 'POST' not supported"
    if body.get("code") != 500 or body.get("msg") != expected_msg:
        return CheckResult("405 响应体", False, f"code={body.get('code')!r}, msg={body.get('msg')!r}")
    return CheckResult("405 降级为 HTTP 200", True)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Python port startup smoke test")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_BASE_URL", "http://127.0.0.1:9989"),
        help="服务地址，默认 http://127.0.0.1:9989（对应 server.port）",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="单个请求超时（秒）")
    args = parser.parse_args(argv)

    print(f"[smoke] 目标服务: {args.base_url}")

    results: List[CheckResult] = []
    try:
        with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
            results.append(_check_index(client))
            results.append(_check_trace_header(client))
            health_result, health_body = _check_health(client)
            results.append(health_result)
            results.append(_check_404(client))
            results.append(_check_405(client))
    except httpx.ConnectError:
        print(f"[FAIL] 无法连接 {args.base_url}")
        print("       请先启动服务: python run.py")
        return 1
    except httpx.HTTPError as exc:
        print(f"[FAIL] 请求异常: {exc!r}")
        return 1

    for result in results:
        print(result)

    failed = [result for result in results if not result.ok]
    print()
    print(f"[smoke] {len(results) - len(failed)}/{len(results)} 项通过")
    if health_body:
        data = health_body.get("data") or {}
        print(f"[smoke] 健康状态: {data.get('status')}  {data.get('components')}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
