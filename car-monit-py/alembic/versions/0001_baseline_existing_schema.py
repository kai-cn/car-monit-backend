"""baseline: 现有库结构由 Java 侧 SQL 脚本维护，本基线只做版本记录（P2-13）.

Revision ID: 0001_baseline
Revises: (none)
Create Date: 2026-11-07

为什么是空迁移
--------------
本项目没有声明式 ORM 元数据（``target_metadata = None``），表结构由
``ruoyi-system/src/main/resources/sql/*.sql`` 人工执行，97 个 MyBatis XML mapper
才是 SQL 的唯一权威。因此 Alembic 只负责"库结构版本号"这一件事：

* 已有数据库执行一次 ``alembic stamp 0001_baseline``，把当前结构登记为基线，
  **不会**修改任何表；
* 后续增量变更（新增列/索引）才写真正的 ``op.add_column`` / ``op.create_index``，
  并且仍然要同步修改对应的 MyBatis XML。

不要运行 ``alembic upgrade head`` 去"重建"这套表 —— 那需要 97 份 XML 的完整 DDL，
本项目未提供。``upgrade()`` 在这里是空操作，正是为了让 ``stamp`` 之后的
``upgrade`` 不会误删数据。
"""

from __future__ import annotations

from alembic import op  # noqa: F401 - 增量迁移会用到；基线本身不执行 SQL

# revision identifiers, used by Alembic.
revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op：现有 schema 由人工 SQL 维护，基线只登记版本号。"""


def downgrade() -> None:
    """No-op：基线没有可回退的结构变更。"""
