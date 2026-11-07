// JAVA 对照: 无（Java 仓库没有版本化迁移，表结构由外部 carmonitdb.sql 提供）
// 类/职责: 内嵌数据库迁移脚本，供 cmd/migrate 顺序执行
// 对应 Go 文件: internal/migrations/embed.go
package migrations

import "embed"

// FS 内嵌全部迁移脚本；命名规范 NNNN_描述.sql，按文件名升序执行。
//
//go:embed sql/*.sql
var FS embed.FS

// Dir 是脚本在 FS 中的目录。
const Dir = "sql"
