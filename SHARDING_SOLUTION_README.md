# ShardingSphere分表解决方案

## 问题分析

### 问题1：只对特定表进行分表

**问题描述**：
项目中只有以下两张表需要分表：
- `ods_rt_szdn_snapshot_flow`（卡口流水表）- 按月分表
- `ods_lwzxsfsj_fee_records`（费用记录表）- 按日分表

其他业务表不需要分表。

### 问题2：根据ID查询时的性能问题

**问题描述**：
根据ID查询时，由于ID中不包含分片信息，ShardingSphere会遍历所有分表进行查询，导致性能下降。

## 解决方案

### 1. 配置默认数据源路由

**核心配置**：
在`ShardingSphereConfig.java`中添加：
```java
shardingRuleConfig.setDefaultDataSourceName("ds");
```

**效果**：
- 未配置分表规则的表，直接路由到默认数据源ds
- 不经过ShardingSphere的分表逻辑，性能不受影响
- 完全兼容原有的业务逻辑

### 2. 优化根据ID查询的性能

**方案A：从雪花算法ID中解析时间戳（推荐）**

利用雪花算法ID包含时间戳的特性，从ID中解析出时间信息，直接确定需要查询的分表：

```
雪花算法ID结构：
[1bit][41bits时间戳][10bits工作机器id][12bits序列号]
```

**实现**：
`ShardingIdCacheService.java` - ID-分表映射缓存服务
- `extractTimestampFromId()` - 从ID中解析时间戳
- `getSnapshotFlowTableName()` - 根据ID获取分表名
- `getFeeRecordsTableName()` - 根据ID获取分表名

**方案B：时间范围查询**

从ID解析出时间范围，使用时间范围+ID查询，ShardingSphere会根据时间范围自动路由到对应分表。

**方案C：Redis缓存**

缓存ID与分表的映射关系，首次查询后缓存，后续直接从缓存获取。

### 3. 双数据源配置

- 主数据源：用于所有业务表
- ShardingSphere数据源：仅用于分表查询，配置为Primary

## 文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/SnapshotFlowMonthShardingAlgorithm.java` | 卡口流水表按月分表算法 |
| `ruoyi-system/src/main/java/com/ruoyi/base/sharding/FeeRecordsDayShardingAlgorithm.java` | 费用记录表按日分表算法 |
| `ruoyi-admin/src/main/java/com/ruoyi/admin/config/ShardingSphereConfig.java` | ShardingSphere分表配置类 |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/ShardingSnapshotFlowMapper.java` | ShardingSphere专用Mapper |
| `ruoyi-system/src/main/resources/mapper/base/ShardingSnapshotFlowMapper.xml` | ShardingSphere专用Mapper XML |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/ShardingIdCacheService.java` | ID-分表映射缓存服务 |
| `ruoyi-system/src/main/java/com/ruoyi/base/service/sharding/ShardingQueryService.java` | 分表查询优化服务 |

### 修改文件

| 文件路径 | 说明 |
|---------|------|
| `pom.xml` | 添加ShardingSphere依赖 |
| `ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapper.java` | 添加selectFromTableById方法 |
| `ruoyi-system/src/main/resources/mapper/base/OdsRtSzdnSnapshotFlowAddcodeMapper.xml` | 添加对应SQL |

## 配置说明

### application.yml配置

```yaml
# ShardingSphere开关（默认关闭，需要时开启）
sharding:
  enabled: true
```

### 分表规则配置

**卡口流水表**：
- 逻辑表名：`ods_rt_szdn_snapshot_flow`
- 分表字段：`snapshottime`
- 分表策略：按月分表
- 分表格式：`ods_rt_szdn_snapshot_flow_yyyyMM`
- 数据范围：2025年-2099年

**费用记录表**：
- 逻辑表名：`ods_lwzxsfsj_fee_records`
- 分表字段：`record_time`
- 分表策略：按日分表
- 分表格式：`ods_lwzxsfsj_fee_records_yyyyMMdd`

## 使用示例

### 示例1：普通业务表查询（不经过分表）

```java
// 完全不需要修改，直接使用原有的Mapper
SysUser user = sysUserMapper.selectById(1L);
```

### 示例2：根据ID查询分表（优化版）

```java
@Autowired
private ShardingQueryService shardingQueryService;

// 优化查询，避免遍历所有分表
OdsRtSzdnSnapshotFlowAddcode result = 
    shardingQueryService.selectByIdOptimized(bigId);
```

### 示例3：时间范围查询分表

```java
@Autowired
private ShardingSnapshotFlowMapper shardingSnapshotFlowMapper;

// ShardingSphere自动路由到对应的分表
List<OdsRtSzdnSnapshotFlowAddcode> list = 
    shardingSnapshotFlowMapper.selectByTimeRange(startTime, endTime);
```

### 示例4：插入数据

```java
@Autowired
private ShardingQueryService shardingQueryService;

// 插入数据并缓存ID映射关系
shardingQueryService.insertWithCache(record);
```

## 性能对比

### 根据ID查询

| 方案 | 性能 | 说明 |
|-----|------|------|
| ShardingSphere标准查询 | ⚠️ 慢 | 遍历所有分表 |
| 从ID解析时间戳直接查询 | ✅ 快 | 仅查询一个分表 |
| 时间范围查询 | ✅ 较快 | 查询1-2个分表 |

### 普通业务表查询

| 方案 | 性能 |
|-----|------|
| 直接查询 | ✅ 不受影响 |
| 经过ShardingSphere | ✅ 相同（路由到默认数据源） |

## 分表建表SQL示例

```sql
-- 创建2025年8月的卡口流水表
CREATE TABLE IF NOT EXISTS ods_rt_szdn_snapshot_flow_202508 
LIKE ods_rt_szdn_snapshot_flow;

-- 创建索引
CREATE INDEX idx_snapshottime_202508 
ON ods_rt_szdn_snapshot_flow_202508(snapshottime);

-- 创建2025年8月1日的费用记录表
CREATE TABLE IF NOT EXISTS ods_lwzxsfsj_fee_records_20250801 
LIKE ods_lwzxsfsj_fee_records;

CREATE INDEX idx_record_time_20250801 
ON ods_lwzxsfsj_fee_records_20250801(record_time);
```

## 注意事项

1. **雪花算法时间戳**：确保雪花算法的起始时间与配置一致（当前为2023-01-01）
2. **分表创建**：需要提前创建好分表，或者配置自动创建策略
3. **索引优化**：每个分表都需要在分片字段上建立索引
4. **事务支持**：跨分表事务需要使用分布式事务
5. **配置开关**：通过`sharding.enabled`可以灵活开启/关闭分表功能

## 扩展说明

### 如何添加新的分表

1. 创建分表算法（类似`SnapshotFlowMonthShardingAlgorithm`）
2. 在`ShardingSphereConfig`中配置分表规则
3. 创建对应的Mapper（如需要）
4. 提前创建好分表

### 如何调整雪花算法参数

修改`ShardingIdCacheService.java`中的常量：
```java
private static final long SNOWFLAKE_EPOCH = 1672531200000L; // 起始时间
private static final long TIME_SHIFT = 22; // 时间戳位移
```
