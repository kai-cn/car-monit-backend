# 生成阶段的“真实列校验”。
#
# 为什么需要：Mapper XML 的 selectVo 里可能混着 join 出来的列（例如
# sys_index_menu 的 menu_name 来自 sys_menu），单表 spec 拼出的 SQL 要到运行期才炸。
# 这里在生成前用 information_schema 核对一次，列对不上的实体直接不生成，
# 并在 stderr 里说明原因 —— 宁可少生成，也不产出会 500 的接口。
import os
import subprocess


def real_columns(table, db=None):
    if os.environ.get("CM_SKIP_DB_CHECK") or not table:
        return None
    cmd = ["mysql",
           "-h", os.environ.get("CM_DB_HOST", "127.0.0.1"),
           "-P", os.environ.get("CM_DB_PORT", "3307"),
           "-u", os.environ.get("CM_DB_USER", "root"),
           "-p" + os.environ.get("CM_DB_PASSWORD", "root"),
           "-N", "-B", "-e",
           "select column_name from information_schema.columns where table_schema = "
           "database() and table_name = '" + table + "'",
           db or os.environ.get("CM_DB_NAME", "carmonitdb")]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=20)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return {c.strip().lower() for c in r.stdout.splitlines() if c.strip()}
