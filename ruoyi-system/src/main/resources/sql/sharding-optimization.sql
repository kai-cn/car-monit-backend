-- 跨月份查询优化 - 数据库视图方案
-- 适用于非分布式场景，无需 Kafka/Debezium/ES

-- ============================================
-- 方案1: 创建联合视图（适用于跨月份查询）
-- ============================================

-- 创建一个包含所有月份数据的视图
-- 注意：此视图会随分表自动扩展（需要定期更新）
-- 更实用的方式是使用动态 SQL 或存储过程

DROP VIEW IF EXISTS ods_rt_szdn_snapshot_flow_view;

CREATE VIEW ods_rt_szdn_snapshot_flow_view AS
SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202401
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202402
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202403
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202404
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202405
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202406
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202407
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202408
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202409
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202410
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202411
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202412
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202501
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202502
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202503
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202504
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202505
UNION ALL
SELECT * FROM ods_rt_szdn_snapshot_flow_202506;

-- ============================================
-- 方案2: 创建物化视图（预计算，适合读多写少场景）
-- ============================================

-- 创建物化视图（需要定期刷新）
DROP MATERIALIZED VIEW IF EXISTS ods_rt_szdn_snapshot_flow_mv;

CREATE MATERIALIZED VIEW ods_rt_szdn_snapshot_flow_mv AS
SELECT 
    big_id,
    datasource,
    cameratype,
    deviceid,
    gantrycode,
    gantryname,
    roadcode,
    roadname,
    sectioncode,
    sectionname,
    tollcode,
    tollname,
    orgcode,
    orgname,
    direction,
    hexcode,
    pileno,
    lon,
    lat,
    deviceip,
    siteid,
    laneid,
    snapshottimeunix,
    snapshottime,
    receivedtimeunix,
    receivedtime,
    platenumber,
    platecolor,
    platecolorcode,
    platetype,
    platetypecode,
    plateconfidence,
    carbrand,
    carcolor,
    carcolorcode,
    cartype,
    cartypecode,
    cardirection,
    snappicturepath,
    loadtime,
    gradelevel,
    datauuid,
    reserve3,
    DATE_TRUNC('month', snapshottime) as month_start
FROM ods_rt_szdn_snapshot_flow_view
WITH DATA;

-- 创建物化视图索引
CREATE INDEX idx_mv_platenumber ON ods_rt_szdn_snapshot_flow_mv(platenumber);
CREATE INDEX idx_mv_snapshottime ON ods_rt_szdn_snapshot_flow_mv(snapshottime);
CREATE INDEX idx_mv_sectioncode ON ods_rt_szdn_snapshot_flow_mv(sectioncode);
CREATE INDEX idx_mv_month_start ON ods_rt_szdn_snapshot_flow_mv(month_start);

-- 刷新物化视图（需要定期执行）
-- REFRESH MATERIALIZED VIEW ods_rt_szdn_snapshot_flow_mv;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY ods_rt_szdn_snapshot_flow_mv;

-- ============================================
-- 方案3: 创建按月分区的主表（PostgreSQL 原生分区表）
-- ============================================

-- 创建分区父表
DROP TABLE IF EXISTS ods_rt_szdn_snapshot_flow_partitioned;

CREATE TABLE ods_rt_szdn_snapshot_flow_partitioned (
    big_id VARCHAR(64) PRIMARY KEY,
    datasource VARCHAR(64),
    cameratype VARCHAR(64),
    deviceid VARCHAR(64),
    gantrycode VARCHAR(64),
    gantryname VARCHAR(255),
    roadcode VARCHAR(64),
    roadname VARCHAR(255),
    sectioncode VARCHAR(64),
    sectionname VARCHAR(255),
    tollcode VARCHAR(64),
    tollname VARCHAR(255),
    orgcode VARCHAR(64),
    orgname VARCHAR(255),
    direction INTEGER,
    hexcode VARCHAR(64),
    pileno VARCHAR(64),
    lon DECIMAL(18,10),
    lat DECIMAL(18,10),
    deviceip VARCHAR(32),
    siteid BIGINT,
    laneid INTEGER,
    snapshottimeunix BIGINT,
    snapshottime TIMESTAMP,
    receivedtimeunix BIGINT,
    receivedtime TIMESTAMP,
    platenumber VARCHAR(32),
    platecolor VARCHAR(32),
    platecolorcode INTEGER,
    platetype VARCHAR(32),
    platetypecode INTEGER,
    plateconfidence INTEGER,
    carbrand VARCHAR(64),
    carcolor VARCHAR(32),
    carcolorcode INTEGER,
    cartype VARCHAR(64),
    cartypecode INTEGER,
    cardirection VARCHAR(32),
    snappicturepath VARCHAR(512),
    loadtime TIMESTAMP,
    gradelevel INTEGER,
    datauuid VARCHAR(64),
    reserve3 VARCHAR(255)
) PARTITION BY RANGE (snapshottime);

-- 创建月份分区（示例）
-- 可以使用脚本自动创建
CREATE TABLE IF NOT EXISTS ods_rt_szdn_snapshot_flow_p202401
PARTITION OF ods_rt_szdn_snapshot_flow_partitioned
FOR VALUES FROM ('2024-01-01 00:00:00') TO ('2024-02-01 00:00:00');

CREATE TABLE IF NOT EXISTS ods_rt_szdn_snapshot_flow_p202402
PARTITION OF ods_rt_szdn_snapshot_flow_partitioned
FOR VALUES FROM ('2024-02-01 00:00:00') TO ('2024-03-01 00:00:00');

-- ============================================
-- 索引优化（针对跨月份查询）
-- ============================================

-- 为每个分表创建必要的索引
-- 在应用层会自动路由到对应的分表查询

-- 车牌号索引（最常用的查询条件）
CREATE INDEX IF NOT EXISTS idx_snapshot_flow_platenumber 
    ON ods_rt_szdn_snapshot_flow_addcode(platenumber);

-- 抓拍时间索引（跨月份查询必备）
CREATE INDEX IF NOT EXISTS idx_snapshot_flow_snapshottime 
    ON ods_rt_szdn_snapshot_flow_addcode(snapshottime);

-- 复合索引（车牌号 + 时间范围）
CREATE INDEX IF NOT EXISTS idx_snapshot_flow_plate_time 
    ON ods_rt_szdn_snapshot_flow_addcode(platenumber, snapshottime);

-- 路段编码索引
CREATE INDEX IF NOT EXISTS idx_snapshot_flow_sectioncode 
    ON ods_rt_szdn_snapshot_flow_addcode(sectioncode);

-- 门架编码索引
CREATE INDEX IF NOT EXISTS idx_snapshot_flow_gantrycode 
    ON ods_rt_szdn_snapshot_flow_addcode(gantrycode);

-- ============================================
-- 常用查询示例（针对视图）
-- ============================================

-- 跨月份查询示例
SELECT * 
FROM ods_rt_szdn_snapshot_flow_view
WHERE platenumber = '京A12345'
    AND snapshottime >= '2024-01-01' 
    AND snapshottime < '2024-06-01'
ORDER BY snapshottime DESC;

-- 统计查询示例
SELECT 
    sectioncode,
    COUNT(*) as total_count,
    MIN(snapshottime) as first_time,
    MAX(snapshottime) as last_time
FROM ods_rt_szdn_snapshot_flow_view
WHERE snapshottime >= '2024-01-01' 
    AND snapshottime < '2024-02-01'
GROUP BY sectioncode
ORDER BY total_count DESC;

-- ============================================
-- 存储过程：动态查询多个分表
-- ============================================

-- 创建存储过程用于跨月份查询
CREATE OR REPLACE FUNCTION query_snapshot_flow_by_month_range(
    p_platenumber VARCHAR DEFAULT NULL,
    p_start_date DATE,
    p_end_date DATE
) RETURNS SETOF ods_rt_szdn_snapshot_flow_addcode AS $$
DECLARE
    current_month DATE;
    table_name TEXT;
    query_sql TEXT;
BEGIN
    current_month := DATE_TRUNC('month', p_start_date);
    
    WHILE current_month < p_end_date LOOP
        table_name := 'ods_rt_szdn_snapshot_flow_' || TO_CHAR(current_month, 'YYYYMM');
        
        -- 检查表是否存在
        IF EXISTS (
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_name = table_name
        ) THEN
            query_sql := 'SELECT * FROM ' || quote_ident(table_name) || ' WHERE 1=1';
            
            IF p_platenumber IS NOT NULL THEN
                query_sql := query_sql || ' AND platenumber = ' || quote_literal(p_platenumber);
            END IF;
            
            query_sql := query_sql || ' AND snapshottime >= ' || quote_literal(p_start_date) || 
                        ' AND snapshottime < ' || quote_literal(p_end_date);
            
            RETURN QUERY EXECUTE query_sql;
        END IF;
        
        current_month := current_month + INTERVAL '1 month';
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql STABLE;

-- 使用存储过程
-- SELECT * FROM query_snapshot_flow_by_month_range('京A12345', '2024-01-01', '2024-06-01');
