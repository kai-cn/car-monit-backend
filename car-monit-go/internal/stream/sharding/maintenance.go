// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/task/ShardingTableTask.java:23-103
// JAVA 对照: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml:236-245
// 类/职责: 提前创建未来月份的分表（每月 1 日 01:00 由 Quartz/Go 调度触发）
// 对应 Go 文件: internal/stream/sharding/maintenance.go
//
// DIFF: Java 用 Spring @Scheduled；Go 由 internal/modules/quartz 或 main 中的 cron 调用
//
//	CreateFutureTables，调度表达式保持一致（0 0 1 1 * ?）。
//
// DIFF: CREATE TABLE 的表名来自服务端生成（非请求参数），仍做标识符白名单校验后再拼接。
package sharding

import (
	"context"
	"fmt"
	"log/slog"
	"regexp"
	"time"

	"gorm.io/gorm"
)

// TemplateTable 对应 mapper 中 CREATE TABLE ... LIKE 的基准表。
const TemplateTable = "ods_rt_szdn_snapshot_flow_addcode"

var identPattern = regexp.MustCompile(`^[A-Za-z0-9_]+$`)

type Maintenance struct {
	db       *gorm.DB
	prefix   string
	strategy Strategy
	log      *slog.Logger
}

func NewMaintenance(db *gorm.DB, prefix string, strategy Strategy, log *slog.Logger) *Maintenance {
	if prefix == "" {
		prefix = DefaultTablePrefix
	}
	if strategy == "" {
		strategy = DefaultStrategy
	}
	return &Maintenance{db: db, prefix: prefix, strategy: strategy, log: log}
}

// CreateFutureTables 对应 ShardingTableTask.createShardingTables:35-68。
func (m *Maintenance) CreateFutureTables(ctx context.Context, months int) (created, existed int, err error) {
	names := FutureTableNames(m.prefix, months, m.strategy)
	for _, name := range names {
		ok, e := m.tableExists(ctx, name)
		if e != nil {
			return created, existed, e
		}
		if ok {
			m.log.Info("分表已存在，跳过创建", "table", name)
			existed++
			continue
		}
		if e := m.createTable(ctx, name); e != nil {
			return created, existed, fmt.Errorf("创建分表 %s 失败: %w", name, e)
		}
		m.log.Info("成功创建分表", "table", name)
		created++
	}
	m.log.Info("分表任务执行完成", "existed", existed, "created", created)
	return created, existed, nil
}

// ManualCreateTables 对应 ShardingTableTask.manualCreateTables:76-102。
func (m *Maintenance) ManualCreateTables(ctx context.Context, months int) string {
	created, existed, err := m.CreateFutureTables(ctx, months)
	if err != nil {
		m.log.Error("手动创建分表失败", "err", err)
		return "创建失败: " + err.Error()
	}
	return fmt.Sprintf("创建完成，已存在表: %d, 新创建表: %d", existed, created)
}

func (m *Maintenance) tableExists(ctx context.Context, table string) (bool, error) {
	var count int64
	err := m.db.WithContext(ctx).Raw(`
		SELECT COUNT(*)
		FROM INFORMATION_SCHEMA.TABLES
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?`, table).Scan(&count).Error
	return count > 0, err
}

func (m *Maintenance) createTable(ctx context.Context, table string) error {
	if !identPattern.MatchString(table) || !identPattern.MatchString(TemplateTable) {
		return fmt.Errorf("非法表名: %s", table)
	}
	// 表名已通过白名单校验，且不来自请求参数。
	return m.db.WithContext(ctx).Exec(fmt.Sprintf("CREATE TABLE IF NOT EXISTS `%s` LIKE `%s`", table, TemplateTable)).Error
}

// CurrentMonthName 便于日志与验证。
func (m *Maintenance) CurrentMonthName() string {
	return TableNameByDate(m.prefix, time.Now(), m.strategy)
}
