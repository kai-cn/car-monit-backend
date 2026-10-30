# 非分布式跨月份查询优化方案

## 目录

1. [问题分析](#1-问题分析)
2. [方案对比](#2-方案对比)
3. [推荐方案实现](#3-推荐方案实现)
4. [代码示例](#4-代码示例)
5. [性能测试](#5-性能测试)

---

## 1. 问题分析

### 1.1 当前架构问题

| 问题 | 描述 | 影响 |
|------|------|------|
| **跨月份查询慢** | 查询跨多个月份的数据需要遍历多个分表 | 查询时间随月份数量线性增长 |
| **分布式组件复杂** | Kafka + Debezium + Elasticsearch 增加运维复杂度 | 学习成本高，运维难度大 |
| **资源占用高** | 多个服务需要独立资源 | 服务器成本增加 |
| **单点故障风险** | 分布式系统任一组件故障影响整体 | 系统可靠性下降 |

### 1.2 数据规模

- 总数据量：300GB+
- 日增量：50万条
- 分表策略：按月分表（约30+个表）

---

## 2. 方案对比

### 2.1 方案矩阵

| 方案 | 复杂度 | 性能 | 侵入性 | 推荐度 |
|------|--------|------|--------|--------|
| **数据库视图** | 低 | 中 | 低 | ⭐⭐⭐⭐⭐ |
| **物化视图** | 低 | 高 | 低 | ⭐⭐⭐⭐ |
| **原生分区表** | 中 | 高 | 中 | ⭐⭐⭐ |
| **Kafka + Debezium + ES** | 高 | 高 | 高 | ⭐⭐ |

### 2.2 方案详解

#### 方案一：数据库联合视图（推荐）

```sql
-- 创建联合视图
CREATE VIEW ods_rt_szdn_snapshot_flow_view AS
SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202401
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202402
-- ... 其他月份
```

**优点**：
- 实现简单，只需创建一次
- 查询透明，应用层无需修改
- 零侵入，不影响写入性能

**缺点**：
- 视图需要定期更新（新增月份）
- 查询性能略低于物化视图

#### 方案二：物化视图（适合读多写少）

```sql
-- 创建物化视图
CREATE MATERIALIZED VIEW ods_rt_szdn_snapshot_flow_mv AS
SELECT * FROM ods_rt_szdn_snapshot_flow_view WITH DATA;

-- 创建索引
CREATE INDEX idx_mv_platenumber ON ods_rt_szdn_snapshot_flow_mv(platenumber);
CREATE INDEX idx_mv_snapshottime ON ods_rt_szdn_snapshot_flow_mv(snapshottime);

-- 刷新数据
REFRESH MATERIALIZED VIEW ods_rt_szdn_snapshot_flow_mv;
```

**优点**：
- 查询性能极高（预计算）
- 支持复杂聚合查询

**缺点**：
- 需要定期刷新（数据有延迟）
- 占用额外存储空间

#### 方案三：动态分表查询（应用层优化）

```java
// 根据时间范围动态构建查询
List<String> tableNames = getTableNamesByDateRange(startDate, endDate);

if (tableNames.size() == 1) {
    // 单表查询
    return mapper.selectFromTable(tableNames.get(0), query);
} else {
    // UNION ALL 联合查询
    return unionQuery(tableNames, query);
}
```

**优点**：
- 灵活控制查询策略
- 可根据月份数量选择最优路径
- 无需修改数据库结构

**缺点**：
- 需要修改应用代码
- 跨表查询需要合并结果

---

## 3. 推荐方案实现

### 3.1 架构设计

```
┌────────────────────────────────────────────────────────────────────┐
│                      应用层 (car-monit-backend-new)               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              CrossMonthQueryService                        │  │
│  │  - 根据时间范围计算涉及的分表                            │  │
│  │  - 选择最优查询策略（单表/UNION ALL/视图）               │  │
│  │  - 合并结果并分页                                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                         MySQL 数据库                             │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  分表:                                                      │  │
│  │    - ods_rt_szdn_snapshot_flow_addcode (当前月)             │  │
│  │    - ods_rt_szdn_snapshot_flow_202401                     │  │
│  │    - ods_rt_szdn_snapshot_flow_202402                     │  │
│  │    - ...                                                  │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  视图:                                                      │  │
│  │    - ods_rt_szdn_snapshot_flow_view (UNION ALL)            │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 查询策略

| 条件 | 策略 | 说明 |
|------|------|------|
| 单月份 | 直接查询对应分表 | 最优性能 |
| 2-3个月份 | UNION ALL 查询 | 避免视图开销 |
| 4+个月份 | 使用联合视图 | 简化SQL复杂度 |

---

## 4. 代码示例

### 4.1 Service 层

```java
// 文件: CrossMonthQueryService.java

/**
 * 跨月份分页查询（优化版）
 */
public TableDataInfo queryCrossMonthPage(OdsRtSzdnSnapshotFlowAddcode queryParam) {
    // 1. 获取时间范围涉及的分表
    List<String> tableNames = getTableNamesByDateRange(startTime, endTime);
    
    // 2. 根据分表数量选择查询策略
    List<OdsRtSzdnSnapshotFlowAddcode> dataList;
    if (tableNames.size() == 1) {
        // 单表查询
        dataList = snapshotFlowMapper.selectFromTable(tableNames.get(0), queryParam);
    } else if (tableNames.size() <= 3) {
        // 少量表：UNION ALL
        dataList = unionQuery(tableNames, queryParam);
    } else {
        // 大量表：使用视图
        try {
            dataList = snapshotFlowMapper.selectFromView(queryParam);
        } catch (Exception e) {
            // 视图不存在，回退到 UNION ALL
            dataList = unionQuery(tableNames, queryParam);
        }
    }
    
    // 3. 排序和分页
    dataList.sort((a, b) -> b.getSnapshottime().compareTo(a.getSnapshottime()));
    
    // 4. 返回结果
    return buildPageResult(dataList, pageNum, pageSize);
}
```

### 4.2 Mapper 层

```java
// 文件: OdsRtSzdnSnapshotFlowAddcodeMapper.java

/**
 * 从指定表查询数据
 */
List<OdsRtSzdnSnapshotFlowAddcode> selectFromTable(
    @Param("tableName") String tableName,
    @Param("query") OdsRtSzdnSnapshotFlowAddcode query);

/**
 * 从联合视图查询数据
 */
List<OdsRtSzdnSnapshotFlowAddcode> selectFromView(OdsRtSzdnSnapshotFlowAddcode query);

/**
 * 统计指定表的数据
 */
Map<String, Object> statisticsTable(
    @Param("tableName") String tableName,
    @Param("query") OdsRtSzdnSnapshotFlowAddcode query);
```

### 4.3 XML 映射

```xml
<!-- 文件: OdsRtSzdnSnapshotFlowAddcodeMapper.xml -->

<select id="selectFromTable" resultMap="OdsRtSzdnSnapshotFlowAddcodeResult">
    SELECT <include refid="selectOdsRtSzdnSnapshotFlowAddcodeVo"/>
    FROM ${tableName} t
    WHERE 1=1
    <if test="query.platenumber != null"> and t.platenumber = #{query.platenumber}</if>
    <if test="query.snapshottime != null"> and t.snapshottime >= #{query.snapshottime}</if>
    <if test="query.applyTime2 != null"> and t.snapshottime < #{query.applyTime2}</if>
    ORDER BY t.snapshottime DESC
</select>

<select id="selectFromView" resultMap="OdsRtSzdnSnapshotFlowAddcodeResult">
    SELECT <include refid="selectOdsRtSzdnSnapshotFlowAddcodeVo"/>
    FROM ods_rt_szdn_snapshot_flow_view t
    WHERE 1=1
    <if test="platenumber != null"> and t.platenumber = #{platenumber}</if>
    <if test="snapshottime != null"> and t.snapshottime >= #{snapshottime}</if>
    <if test="applyTime2 != null"> and t.snapshottime < #{applyTime2}</if>
    ORDER BY t.snapshottime DESC
</select>
```

### 4.4 数据库脚本

```sql
-- 创建联合视图（需要定期维护）
DROP VIEW IF EXISTS ods_rt_szdn_snapshot_flow_view;

CREATE VIEW ods_rt_szdn_snapshot_flow_view AS
SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202401
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202402
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202403
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202404
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202405
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202406
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202407
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202408
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202409
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202410
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202411
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202412
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202501
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202502
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202503
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202504
UNION ALL SELECT * FROM ods_rt_szdn_snapshot_flow_202505;

-- 创建索引（视图本身不需要索引，确保基础表有索引）
CREATE INDEX idx_platenumber ON ods_rt_szdn_snapshot_flow_addcode(platenumber);
CREATE INDEX idx_snapshottime ON ods_rt_szdn_snapshot_flow_addcode(snapshottime);
CREATE INDEX idx_plate_time ON ods_rt_szdn_snapshot_flow_addcode(platenumber, snapshottime);
```

---

## 5. 性能测试

### 5.1 测试场景

| 场景 | 时间范围 | 涉及表数 | 预期结果 |
|------|---------|---------|---------|
| 单月查询 | 2024-01 | 1 | < 50ms |
| 季度查询 | 2024-Q1 | 3 | < 200ms |
| 半年查询 | 2024-H1 | 6 | < 500ms |
| 全年查询 | 2024年 | 12 | < 1000ms |

### 5.2 优化建议

| 优化项 | 说明 | 收益 |
|--------|------|------|
| 索引优化 | 确保 `platenumber`、`snapshottime` 有索引 | 查询加速 5-10x |
| 分区裁剪 | 根据 `snapshottime` 范围自动选择分表 | 避免全表扫描 |
| 查询缓存 | Redis 缓存常用查询结果 | 热点数据加速 |
| 异步统计 | 复杂统计任务异步执行 | 不阻塞主流程 |

### 5.3 监控指标

```java
// 监控指标示例
Map<String, Object> monitorMetrics = new HashMap<>();
monitorMetrics.put("queryDurationMs", duration);
monitorMetrics.put("tableCount", tableNames.size());
monitorMetrics.put("recordCount", resultCount);
monitorMetrics.put("queryType", queryType); // SINGLE_TABLE / UNION_ALL / VIEW
```

---

## 6. 总结

### 6.1 方案选择建议

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| 开发简单 | 数据库视图 | 零代码修改 |
| 读多写少 | 物化视图 | 最高查询性能 |
| 需要灵活控制 | 动态分表查询 | 最优策略选择 |
| 大数据量 + 实时性 | Kafka + Debezium + ES | 分布式处理 |

### 6.2 实施步骤

1. ✅ 创建联合视图
2. ✅ 优化索引
3. ✅ 实现 CrossMonthQueryService
4. ✅ 更新 Controller 使用新服务
5. ✅ 性能测试和调优

### 6.3 与分布式方案对比

| 维度 | 非分布式方案 | 分布式方案 |
|------|------------|-----------|
| 复杂度 | 低 | 高 |
| 性能 | 中高 | 高 |
| 运维 | 简单 | 复杂 |
| 成本 | 低 | 高 |
| 适用场景 | 中小规模 | 大规模实时 |

---

## 附录：已创建的文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 跨月份查询服务 | `ruoyi-system/.../CrossMonthQueryService.java` | 核心查询逻辑 |
| 数据库脚本 | `ruoyi-system/.../sharding-optimization.sql` | 视图和索引创建 |
| Mapper 接口 | `OdsRtSzdnSnapshotFlowAddcodeMapper.java` | 新增方法 |
| Mapper XML | `OdsRtSzdnSnapshotFlowAddcodeMapper.xml` | 新增 SQL |
