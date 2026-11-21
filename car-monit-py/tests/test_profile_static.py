"""`/profile/**` 静态资源映射回归用例.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ResourcesConfig.java

Java 的 ``ResourcesConfig#addResourceHandlers`` 把 ``Constants.RESOURCE_PREFIX``（``/profile``）
映射到 ``file:${ruoyi.profile}/``。上传接口与头像接口返回的都是相对 url
（``/profile/upload/...`` / ``/profile/avatar/...``），前端 ``<img :src>`` 直接使用它，
所以后端必须提供这条静态映射；缺失时这些 url 全部 404（本次评审的 P0-3）。

用例只覆盖两件事：
1. 存在的文件能按 url 原样读出；
2. 目录不存在的路径仍然返回 Spring ``BasicErrorController`` 的 404 信封，
   而不是 StaticFiles 自己的纯文本 "Not Found"。
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.settings import reset_settings_cache


def test_profile_static_serves_uploaded_file(tmp_path: Path, monkeypatch) -> None:
    """``GET /profile/upload/...`` 读到的就是 ``{ruoyi.profile}/upload/...``。"""
    profile = tmp_path / "uploadPath"
    target = profile / "upload" / "2026" / "11" / "07" / "a.txt"
    target.parent.mkdir(parents=True)
    target.write_text("hello", encoding="utf-8")

    monkeypatch.setenv("RUOYI__PROFILE", str(profile))
    reset_settings_cache()
    try:
        from app.main import create_app

        # 不进入 ``with``：不需要触发 lifespan（避免连 MySQL / 启动 Quartz）。
        client = TestClient(create_app())

        response = client.get("/profile/upload/2026/11/07/a.txt")
        assert response.status_code == 200
        assert response.text == "hello"
    finally:
        reset_settings_cache()


def test_profile_static_missing_file_keeps_spring_404_body(
    tmp_path: Path, monkeypatch
) -> None:
    """缺文件时仍是 ``{"timestamp","status","error","path"}`` 的 Spring 404 信封。"""
    profile = tmp_path / "uploadPath"
    profile.mkdir(parents=True)
    monkeypatch.setenv("RUOYI__PROFILE", str(profile))
    reset_settings_cache()
    try:
        from app.main import create_app

        client = TestClient(create_app())
        response = client.get("/profile/upload/missing.txt")
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == 404
        assert body["error"] == "Not Found"
        assert body["path"] == "/profile/upload/missing.txt"
    finally:
        reset_settings_cache()


def test_profile_static_adds_download_and_nosniff_headers(
    tmp_path: Path, monkeypatch
) -> None:
    """上传目录里的 html 被直接导航时必须下载，不能在同源执行脚本."""
    profile = tmp_path / "uploadPath"
    target = profile / "upload" / "2026" / "11" / "07" / "x.html"
    target.parent.mkdir(parents=True)
    target.write_text("<script>alert(1)</script>", encoding="utf-8")

    monkeypatch.setenv("RUOYI__PROFILE", str(profile))
    reset_settings_cache()
    try:
        from app.main import create_app

        client = TestClient(create_app())
        response = client.get("/profile/upload/2026/11/07/x.html")
        assert response.status_code == 200
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["content-disposition"] == "attachment"
    finally:
        reset_settings_cache()


def test_profile_static_cross_drive_path_is_not_found(
    tmp_path: Path, monkeypatch
) -> None:
    """Windows 上 ``commonpath`` 跨盘会抛 ValueError；必须按"越界"转成 404."""

    def _cross_drive(_paths) -> str:
        raise ValueError("path is on mount 'C:', start on mount 'D:'")

    monkeypatch.setattr(os.path, "commonpath", _cross_drive)

    from app.middleware.profile_static import ProfileStaticFiles

    files = ProfileStaticFiles(directory=str(tmp_path), check_dir=False)
    assert files.lookup_path("../../../C:/Windows/win.ini") == ("", None)
