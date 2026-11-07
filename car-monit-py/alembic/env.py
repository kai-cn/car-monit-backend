"""Alembic environment.

# Migrated from: (no Java equivalent -- RuoYi manages schema by hand-written SQL)

Java 原语义
-----------
本项目**没有** Flyway / Liquibase。表结构由 ``ruoyi-system/src/main/resources/sql/*.sql``
人工执行，schema 就是「库里的现状」。

Python 等价实现
---------------
Alembic 只作为「结构对照工具」，不接管 schema：

* 连接串从 :mod:`app.settings` 读取，不重复配置（alembic.ini 里留空）。
* ``target_metadata`` 为空，因为没有 SQLAlchemy 声明式模型 —— MyBatis 的
  97 个 XML mapper 才是 SQL 的唯一权威，映射成 ORM 元数据会导致漂移。
* 因此 ``--autogenerate`` 只会输出「删除全部表」的差异；请只用
  ``alembic current`` / 手工 SQL 检查库结构。

基线（P2-13）
-------------
``versions/0001_baseline_existing_schema.py`` 是空迁移，只用于记录"当前结构已被
登记"。已有库执行一次 ``alembic stamp 0001_baseline`` 即可；后续增量变更才写
真正的 ``op.*``，并同步修改对应的 MyBatis XML。
"""

from __future__ import annotations

import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

logger = logging.getLogger("alembic.env")

#: 故意为空 —— 见模块 docstring。Empty on purpose: no declarative models exist.
target_metadata = None


def _database_url() -> str:
    """Resolve the SQLAlchemy URL from ``application.yml`` (single source of truth)."""
    return get_settings().database_url


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of executing it."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and run migrations (inspection only)."""
    settings = get_settings()
    connectable = create_engine(
        _database_url(),
        connect_args=settings.database_connect_args,
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
