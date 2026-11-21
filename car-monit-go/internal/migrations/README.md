# 数据库版本化迁移

- 命名：`NNNN_描述.sql`，按数字升序执行；已执行的版本记录在 `schema_migrations` 表。
- 每个文件在**单独事务**中执行（MySQL DDL 隐式提交，DDL 失败无法自动回滚，需人工修复后再重跑）。
- `0001_baseline_check.sql` 只校验基线库存在（`sys_user`），不建表：
  全量 DDL 仍由现有 `carmonitdb.sql` 提供，先用 mysql 客户端导入，再执行本迁移。
- 新增结构变更务必追加新文件，不要修改已发布的文件（版本号已落库）。

执行：

```bash
# 本地
go run ./cmd/migrate -c configs/config.yaml

# 只看将执行哪些文件
go run ./cmd/migrate -c configs/config.yaml -dry-run

# 容器内（镜像已内置 carmonit-migrate）
/app/carmonit-migrate -c /app/configs/config.yaml
```
