// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumerV2.java:44-200
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/base/mapper/ShardingSnapshotFlowMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml:236-245
// 类/职责: 门架抓拍流水的数据接入 —— Kafka 批次消费 → Redis 幂等 → MySQL 月度分表 → ES 索引
// 对应 Go 文件: internal/modules/base/datasync.go
//
// DIFF: Java 由 ShardingSphere 依据 snapshottime 自动路由逻辑表；Go 直接按月份计算物理表名，
// 每张分表单独批量 INSERT（见 insertShardRows）。
// DIFF: Java 的 batchInsert 使用 ShardingSnapshotFlowMapper.baseColumns（含 smallpicturepath 等
// 领域对象并不存在的列，MyBatis 无法绑定）；这里只写 OdsRtSzdnSnapshotFlowAddcode 真实存在的 43 列。
// DIFF: Java 批量 INSERT 失败时先降级 saveBatch，再失败只记日志并照常 ack（会丢数据）；
// Go 失败行回滚幂等标记后返回给消费者，由 retryFailed 重试 3 次再进死信队列。
// DIFF: Java 依赖预先建好的分表；Go 在写入前按需 CREATE TABLE ... LIKE（与 ShardingTableTask 同语义）。
// DIFF: 分表 INSERT 追加 ON DUPLICATE KEY UPDATE big_id=big_id，使重试/重叠同步幂等（Java 为裸 INSERT）。
package base

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"regexp"
	"strings"
	"sync"
	"time"

	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/platform/sqlx"
	"car-monit-go/internal/stream/es"
	"car-monit-go/internal/stream/idempotent"
	"car-monit-go/internal/stream/kafka"
	"car-monit-go/internal/stream/sharding"
)

// DataSync 汇总数据接入所需的依赖（对应 KafkaConsumerV2 + SnapshotFlowSyncTask + VehicleMonitoringTask）。
type DataSync struct {
	app      *app.App
	log      *slog.Logger
	db       *gorm.DB
	es       *es.Client
	idem     *idempotent.Util
	source   SnapshotFlowSource
	prefix   string
	strategy sharding.Strategy

	ensureMu sync.Mutex
	ensured  map[string]struct{}

	// retryDelay 对应 Java retryProcess 的 Thread.sleep(1000)；测试可置 0。
	retryDelay time.Duration
}

// NewDataSync 按配置构造数据接入服务。main 与 quartz 共用同一个实例。
func NewDataSync(a *app.App) *DataSync {
	cfg := a.Cfg
	prefix := cfg.Snapshot.Flow.Sharding.TablePrefix
	if prefix == "" {
		prefix = sharding.DefaultTablePrefix
	}
	s := &DataSync{
		app:        a,
		log:        a.Log,
		db:         a.DB,
		es:         es.New(cfg),
		prefix:     prefix,
		strategy:   parseShardingStrategy(cfg.Snapshot.Flow.Sharding.ShardingType),
		ensured:    map[string]struct{}{},
		retryDelay: time.Second,
	}
	if a.Redis != nil {
		s.idem = idempotent.New(a.Redis, cfg.Idempotent.Redis.Prefix, cfg.Idempotent.Redis.ExpireTime)
	} else {
		a.Log.Warn("Redis 未初始化，Kafka 消费将失去幂等保护")
	}
	s.source = newSnapshotFlowSource(cfg)
	return s
}

// parseShardingStrategy 把 Java 配置里的 month/day/quarter/year 转成 ShardingTableUtil 的枚举。
func parseShardingStrategy(value string) sharding.Strategy {
	switch strings.ToLower(strings.TrimSpace(value)) {
	case "day", "daily":
		return sharding.Daily
	case "quarter", "quarterly":
		return sharding.Quarterly
	case "year", "yearly":
		return sharding.Yearly
	default:
		return sharding.Monthly
	}
}

// SnapshotFlowSource 是 GaussDB 读取的可配置适配层。
//
// 未验证点：本地没有 GaussDB/vehicleMonitor 实例，HTTP 适配层只按 Java Forest 声明
// （/base/snapshotflow/list 与 /earliest-time）实现，联调前需在真实环境核对返回结构。
type SnapshotFlowSource interface {
	Name() string
	Earliest(ctx context.Context) (time.Time, bool, error)
	Page(ctx context.Context, start, end string, pageNum, pageSize int) ([]*odsRtSzdnSnapshotFlowAddcode, error)
}

// ---------------------------------------------------------------------------
// Kafka 消费（SnapshotFlowKafkaConsumerV2）
// ---------------------------------------------------------------------------

// snapshotFlowMessage 对应消息体 {"operationType":"INSERT|UPDATE|DELETE","data":{...}}。
type snapshotFlowMessage struct {
	OperationType string                        `json:"operationType"`
	Data          *odsRtSzdnSnapshotFlowAddcode `json:"data"`
}

type snapshotRowMessage struct {
	msg kafka.Message
	row *odsRtSzdnSnapshotFlowAddcode
	key string
}

// HandleSnapshotFlowBatch 对应 @KafkaListener consumeBatch。
func (s *DataSync) HandleSnapshotFlowBatch(ctx context.Context, msgs []kafka.Message) ([]kafka.Message, error) {
	if len(msgs) == 0 {
		return nil, nil
	}
	started := time.Now()

	var (
		rows   []snapshotRowMessage
		failed []kafka.Message
	)
	esDocs := make(map[string]any)
	inserted, skipped := 0, 0

	for _, msg := range msgs {
		var payload snapshotFlowMessage
		if err := json.Unmarshal([]byte(msg.Value), &payload); err != nil {
			failed = append(failed, withReason(msg, "JSON 解析失败: "+err.Error()))
			continue
		}
		data := payload.Data
		if data == nil || isBlank(data.BigID) {
			failed = append(failed, withReason(msg, "数据为空或缺少bigId"))
			continue
		}
		key := strOf(data.BigID)

		// JAVA 对照: checkAndSet —— SETNX 失败表示消息已处理，直接跳过且不算失败。
		if s.idem != nil && !s.idem.CheckAndSet(ctx, key) {
			skipped++
			continue
		}

		switch payload.OperationType {
		case "INSERT", "UPDATE":
			if data.Snapshottime == nil || data.Snapshottime.IsZero() {
				s.removeIdempotent(ctx, key)
				failed = append(failed, withReason(msg, "缺少 snapshottime，无法路由分表"))
				continue
			}
			rows = append(rows, snapshotRowMessage{msg: msg, row: data, key: key})
			esDocs[key] = snapshotFlowESDoc(data)
		case "DELETE":
			if err := s.deleteSnapshotFlow(ctx, key); err != nil {
				s.removeIdempotent(ctx, key)
				failed = append(failed, withReason(msg, "删除失败: "+err.Error()))
				continue
			}
			inserted++
		default:
			// JAVA 对照: 未知 operationType 不做任何处理，视为成功。
			inserted++
		}
	}

	// MySQL 分表写入：按 snapshottime 的月份分组，单表失败只影响该表的消息。
	if len(rows) > 0 {
		grouped := make(map[string][]snapshotRowMessage)
		order := make([]string, 0)
		for _, item := range rows {
			table := sharding.TableNameByDate(s.prefix, item.row.Snapshottime.Time, s.strategy)
			if _, ok := grouped[table]; !ok {
				order = append(order, table)
			}
			grouped[table] = append(grouped[table], item)
		}
		for _, table := range order {
			group := grouped[table]
			batch := make([]*odsRtSzdnSnapshotFlowAddcode, 0, len(group))
			for _, item := range group {
				batch = append(batch, item.row)
			}
			if err := s.ensureShardTable(ctx, table); err != nil {
				s.failGroup(ctx, group, &failed, "分表不可用: "+err.Error())
				continue
			}
			if err := s.insertShardRows(ctx, table, batch); err != nil {
				s.failGroup(ctx, group, &failed, "分表写入失败: "+err.Error())
				continue
			}
			inserted += len(group)
		}
	}

	// ES 索引：JAVA 对照 batchSave —— 失败只告警，不回滚 MySQL，也不阻塞提交。
	if s.es != nil && s.es.Enabled() && len(esDocs) > 0 {
		if err := s.es.BulkIndex(ctx, esDocs); err != nil {
			s.log.Warn("ES 批量索引失败（MySQL 已写入，不影响提交）", "count", len(esDocs), "err", err)
		}
	}

	failed = s.retryFailed(ctx, failed)

	s.log.Info("Kafka 批次处理完成",
		"batch", len(msgs), "inserted", inserted, "skipped", skipped,
		"failed", len(failed), "costMs", time.Since(started).Milliseconds())
	return failed, nil
}

// failGroup 把一组写失败的消息标记进 failed，并回滚幂等标记以便重试。
func (s *DataSync) failGroup(ctx context.Context, group []snapshotRowMessage, failed *[]kafka.Message, reason string) {
	for _, item := range group {
		s.removeIdempotent(ctx, item.key)
		*failed = append(*failed, withReason(item.msg, reason))
	}
}

// retryFailed 对应 handleFailedRecords + retryProcess：最多 3 次、间隔 1 秒，仍失败则进死信队列。
func (s *DataSync) retryFailed(ctx context.Context, failed []kafka.Message) []kafka.Message {
	if len(failed) == 0 {
		return nil
	}
	out := make([]kafka.Message, 0, len(failed))
	for _, msg := range failed {
		ok := false
		reason := msg.Reason
		for attempt := 1; attempt <= 3; attempt++ {
			if err := sleepCtx(ctx, s.retryDelay); err != nil {
				out = append(out, withReason(msg, "重试被中断: "+err.Error()))
				ok = true // 已转交死信，避免外层再次重试
				break
			}
			var retryErr error
			ok, retryErr = s.processSingleMessage(ctx, msg)
			if ok {
				break
			}
			if retryErr != nil {
				reason = msg.Reason + "；重试: " + retryErr.Error()
			}
		}
		if !ok {
			out = append(out, withReason(msg, "重试失败: "+reason))
		}
	}
	return out
}

// processSingleMessage 对应 retryProcess 中的 processSingleRecord + batchSaveData。
func (s *DataSync) processSingleMessage(ctx context.Context, msg kafka.Message) (bool, error) {
	var payload snapshotFlowMessage
	if err := json.Unmarshal([]byte(msg.Value), &payload); err != nil {
		return false, fmt.Errorf("JSON 解析失败: %w", err)
	}
	data := payload.Data
	if data == nil || isBlank(data.BigID) {
		return false, fmt.Errorf("数据为空或缺少bigId")
	}
	key := strOf(data.BigID)
	if s.idem != nil && !s.idem.CheckAndSet(ctx, key) {
		// 幂等标记已存在（首轮可能已写入成功），按已处理返回。
		return true, nil
	}
	switch payload.OperationType {
	case "INSERT", "UPDATE":
		if data.Snapshottime == nil || data.Snapshottime.IsZero() {
			s.removeIdempotent(ctx, key)
			return false, fmt.Errorf("缺少 snapshottime")
		}
		table := sharding.TableNameByDate(s.prefix, data.Snapshottime.Time, s.strategy)
		if err := s.ensureShardTable(ctx, table); err != nil {
			s.removeIdempotent(ctx, key)
			return false, err
		}
		if err := s.insertShardRows(ctx, table, []*odsRtSzdnSnapshotFlowAddcode{data}); err != nil {
			s.removeIdempotent(ctx, key)
			return false, err
		}
		if s.es != nil && s.es.Enabled() {
			if err := s.es.Index(ctx, key, snapshotFlowESDoc(data)); err != nil {
				s.log.Warn("ES 单条索引失败（MySQL 已写入）", "bigId", key, "err", err)
			}
		}
		return true, nil
	case "DELETE":
		if err := s.deleteSnapshotFlow(ctx, key); err != nil {
			s.removeIdempotent(ctx, key)
			return false, err
		}
		return true, nil
	default:
		return true, nil
	}
}

func (s *DataSync) removeIdempotent(ctx context.Context, key string) {
	if s.idem != nil {
		s.idem.Remove(ctx, key)
	}
}

// ---------------------------------------------------------------------------
// MySQL 月度分表
// ---------------------------------------------------------------------------

// snapshotFlowColumns 是 ods_rt_szdn_snapshot_flow_addcode 的 43 个真实列。
var snapshotFlowColumns = []string{
	"big_id", "datasource", "cameratype", "deviceid", "gantrycode", "gantryname",
	"roadcode", "roadname", "sectioncode", "sectionname", "tollcode", "tollname",
	"orgcode", "orgname", "direction", "hexcode", "pileno", "lon", "lat",
	"deviceip", "siteid", "laneid", "snapshottimeunix", "snapshottime",
	"receivedtimeunix", "receivedtime", "platenumber", "platecolor", "platecolorcode",
	"platetype", "platetypecode", "plateconfidence", "carbrand", "carcolor",
	"carcolorcode", "cartype", "cartypecode", "cardirection", "snappicturepath",
	"loadtime", "gradelevel", "datauuid", "reserve3",
}

const snapshotFlowInsertChunk = 200

var shardIdentPattern = regexp.MustCompile(`^[A-Za-z0-9_]+$`)

// insertShardRows 把同一月份的行批量写入物理分表。
func (s *DataSync) insertShardRows(ctx context.Context, table string, rows []*odsRtSzdnSnapshotFlowAddcode) error {
	if len(rows) == 0 {
		return nil
	}
	if !shardIdentPattern.MatchString(table) {
		return fmt.Errorf("非法分表名: %s", table)
	}
	cols := strings.Join(snapshotFlowColumns, ",")
	for start := 0; start < len(rows); start += snapshotFlowInsertChunk {
		end := start + snapshotFlowInsertChunk
		if end > len(rows) {
			end = len(rows)
		}
		part := rows[start:end]
		var b strings.Builder
		b.WriteString("INSERT INTO `")
		b.WriteString(table)
		b.WriteString("` (")
		b.WriteString(cols)
		b.WriteString(") VALUES ")
		args := make([]any, 0, len(part)*len(snapshotFlowColumns))
		for i, row := range part {
			if i > 0 {
				b.WriteByte(',')
			}
			b.WriteByte('(')
			b.WriteString(sqlx.Placeholders(len(snapshotFlowColumns)))
			b.WriteByte(')')
			args = append(args, snapshotFlowValues(row)...)
		}
		// 重试/重叠同步幂等：主键已存在时保持原值。
		b.WriteString(" ON DUPLICATE KEY UPDATE big_id=big_id")
		if err := s.db.WithContext(ctx).Exec(b.String(), args...).Error; err != nil {
			return err
		}
	}
	return nil
}

func snapshotFlowValues(r *odsRtSzdnSnapshotFlowAddcode) []any {
	return []any{
		anyStr(r.BigID), anyStr(r.Datasource), anyStr(r.Cameratype), anyStr(r.Deviceid),
		anyStr(r.Gantrycode), anyStr(r.Gantryname), anyStr(r.Roadcode), anyStr(r.Roadname),
		anyStr(r.Sectioncode), anyStr(r.Sectionname), anyStr(r.Tollcode), anyStr(r.Tollname),
		anyStr(r.Orgcode), anyStr(r.Orgname), anyInt(r.Direction), anyStr(r.Hexcode),
		anyStr(r.Pileno), anyFloat(r.Lon), anyFloat(r.Lat), anyStr(r.Deviceip),
		anyInt64(r.Siteid), anyInt(r.Laneid), anyInt64(r.Snapshottimeunix),
		anyISO(r.Snapshottime), anyInt64(r.Receivedtimeunix), anyDate(r.Receivedtime),
		anyStr(r.Platenumber), anyStr(r.Platecolor), anyInt(r.Platecolorcode),
		anyStr(r.Platetype), anyInt(r.Platetypecode), anyInt(r.Plateconfidence),
		anyStr(r.Carbrand), anyStr(r.Carcolor), anyInt(r.Carcolorcode),
		anyStr(r.Cartype), anyInt(r.Cartypecode), anyStr(r.Cardirection),
		anyStr(r.Snappicturepath), anyDate(r.Loadtime), anyInt(r.Gradelevel),
		anyStr(r.Datauuid), anyStr(r.Reserve3),
	}
}

func anyStr(p *string) any {
	if p == nil {
		return nil
	}
	return *p
}

func anyInt(p *int) any {
	if p == nil {
		return nil
	}
	return *p
}

func anyInt64(p *int64) any {
	if p == nil {
		return nil
	}
	return *p
}

func anyFloat(p *float64) any {
	if p == nil {
		return nil
	}
	return *p
}

func anyISO(p *isoDateTime) any {
	if p == nil || p.IsZero() {
		return nil
	}
	return p.Time
}

func anyDate(p *dateOnly) any {
	if p == nil || p.IsZero() {
		return nil
	}
	return p.Time
}

// ensureShardTable 对应 ShardingTableTask 的单表创建：存在则跳过，否则 LIKE 模板表。
func (s *DataSync) ensureShardTable(ctx context.Context, table string) error {
	s.ensureMu.Lock()
	_, ok := s.ensured[table]
	s.ensureMu.Unlock()
	if ok {
		return nil
	}
	var count int64
	if err := s.db.WithContext(ctx).Raw(`
		SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?`, table).Scan(&count).Error; err != nil {
		return err
	}
	if count == 0 {
		if !shardIdentPattern.MatchString(table) || !shardIdentPattern.MatchString(sharding.TemplateTable) {
			return fmt.Errorf("非法分表名: %s", table)
		}
		// 表名来自服务端按日期生成，且已通过标识符白名单校验。
		if err := s.db.WithContext(ctx).Exec(
			fmt.Sprintf("CREATE TABLE IF NOT EXISTS `%s` LIKE `%s`", table, sharding.TemplateTable)).Error; err != nil {
			return err
		}
		s.log.Info("已创建门架抓拍流水分表", "table", table)
	}
	s.ensureMu.Lock()
	s.ensured[table] = struct{}{}
	s.ensureMu.Unlock()
	return nil
}

// snapshotShardTables 列出已存在的月度分表（排除 _addcode 模板表）。
func (s *DataSync) snapshotShardTables(ctx context.Context) ([]string, error) {
	var names []string
	if err := s.db.WithContext(ctx).Raw(`
		SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES
		WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME LIKE ?`,
		s.prefix+"%").Scan(&names).Error; err != nil {
		return nil, err
	}
	out := make([]string, 0, len(names))
	for _, name := range names {
		if s.isShardTable(name) {
			out = append(out, name)
		}
	}
	return out, nil
}

// isShardTable 只接受「前缀 + 周期后缀」的表名，避免误删 _addcode 模板表/view。
func (s *DataSync) isShardTable(name string) bool {
	if !strings.HasPrefix(name, s.prefix) {
		return false
	}
	suffix := strings.TrimPrefix(name, s.prefix)
	switch s.strategy {
	case sharding.Daily:
		return regexp.MustCompile(`^\d{8}$`).MatchString(suffix)
	case sharding.Quarterly:
		return regexp.MustCompile(`^\d{4}Q[1-4]$`).MatchString(suffix)
	case sharding.Yearly:
		return regexp.MustCompile(`^\d{4}$`).MatchString(suffix)
	default:
		return regexp.MustCompile(`^\d{6}$`).MatchString(suffix)
	}
}

// deleteSnapshotFlow 对应 removeById(bigId)：无分片键时广播到所有月度分表。
func (s *DataSync) deleteSnapshotFlow(ctx context.Context, bigID string) error {
	tables, err := s.snapshotShardTables(ctx)
	if err != nil {
		return err
	}
	for _, table := range tables {
		if err := s.db.WithContext(ctx).Exec(
			fmt.Sprintf("DELETE FROM `%s` WHERE big_id = ?", table), bigID).Error; err != nil {
			return err
		}
	}
	return nil
}

// maxSnapshottime 对应 getMaxSnapshottime。
func (s *DataSync) maxSnapshottime(ctx context.Context, table string) (time.Time, bool, error) {
	var row struct {
		Max *time.Time `gorm:"column:max_time"`
	}
	err := s.db.WithContext(ctx).Raw(
		fmt.Sprintf("SELECT MAX(snapshottime) AS max_time FROM `%s`", table)).Scan(&row).Error
	if err != nil {
		return time.Time{}, false, err
	}
	if row.Max == nil {
		return time.Time{}, false, nil
	}
	return *row.Max, true, nil
}

// snapshotFlowESDoc 对应 SnapshotFlowDocument + JSON.toJSONString(doc)。
//
// DIFF: fastjson2 默认把 java.util.Date 写成毫秒时间戳、忽略 null 字段；
// 这里同样按毫秒输出时间并丢弃 null，保证 ES 文档形态与 Java 一致。
func snapshotFlowESDoc(r *odsRtSzdnSnapshotFlowAddcode) map[string]any {
	raw, err := json.Marshal(r)
	if err != nil {
		return map[string]any{"bigId": strOf(r.BigID)}
	}
	var all map[string]any
	if err := json.Unmarshal(raw, &all); err != nil {
		return map[string]any{"bigId": strOf(r.BigID)}
	}
	out := make(map[string]any, len(snapshotFlowDocKeys))
	for key := range snapshotFlowDocKeys {
		if v, ok := all[key]; ok && v != nil {
			out[key] = v
		}
	}
	if r.Snapshottime != nil && !r.Snapshottime.IsZero() {
		out["snapshottime"] = r.Snapshottime.UnixMilli()
	}
	if r.Receivedtime != nil && !r.Receivedtime.IsZero() {
		out["receivedtime"] = r.Receivedtime.UnixMilli()
	}
	if r.Loadtime != nil && !r.Loadtime.IsZero() {
		out["loadtime"] = r.Loadtime.UnixMilli()
	}
	return out
}

// snapshotFlowDocKeys 对应 SnapshotFlowDocument 的字段集合（不含 transient 查询字段）。
var snapshotFlowDocKeys = map[string]struct{}{
	"bigId": {}, "datasource": {}, "cameratype": {}, "deviceid": {}, "gantrycode": {},
	"gantryname": {}, "roadcode": {}, "roadname": {}, "sectioncode": {}, "sectionname": {},
	"tollcode": {}, "tollname": {}, "orgcode": {}, "orgname": {}, "direction": {},
	"hexcode": {}, "pileno": {}, "lon": {}, "lat": {}, "deviceip": {}, "siteid": {},
	"laneid": {}, "snapshottimeunix": {}, "snapshottime": {}, "receivedtimeunix": {},
	"receivedtime": {}, "platenumber": {}, "platecolor": {}, "platecolorcode": {},
	"platetype": {}, "platetypecode": {}, "plateconfidence": {}, "carbrand": {},
	"carcolor": {}, "carcolorcode": {}, "cartype": {}, "cartypecode": {},
	"cardirection": {}, "snappicturepath": {}, "loadtime": {}, "gradelevel": {},
	"datauuid": {}, "reserve3": {},
}

func withReason(msg kafka.Message, reason string) kafka.Message {
	msg.Reason = reason
	return msg
}

func sleepCtx(ctx context.Context, d time.Duration) error {
	timer := time.NewTimer(d)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}
