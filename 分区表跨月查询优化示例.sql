-- ============================================================
-- 脚本：openGauss 3.0 分区表查询优化与分页完整示例
-- 适用表：ods_rt_szdn_snapshot_flow_addcode（按月 RANGE 分区）
--         ods_lwzxsfsj_fee_records_01（按 transtime RANGE 分区）
--         zdata_trail_fitting（按 extime RANGE 分区）
-- 执行方式：gsql -d 数据库名 -f 分区表跨月查询优化示例.sql
--
-- 核心优化手段：
--   1. 分区剪枝（Partition Pruning）：只扫描涉及的分区
--   2. Keyset / 游标分页：避免 OFFSET 深分页性能衰减
--   3. 半开区间写法：>= 开始时间 AND < 结束时间
--   4. 覆盖索引（Covering Index）：避免回表
-- ============================================================

SET client_encoding = 'UTF8';


-- ============================================================
-- 场景1：跨月份范围查询 + Keyset 游标分页（推荐方案）
-- 查询：某车牌在 2025-03 至 2025-06 的抓拍记录，按时间倒序分页
--
-- 关键点：
--   a. snapshottime 上不包函数（否则无法走分区剪枝）
--   b. 用 (snapshottime DESC, big_id DESC) 作为排序键（必须唯一）
--   c. 用 (snapshottime, big_id) < (上次最后一条的时间, 上次最后一条的ID) 做游标
-- ============================================================

-- 第1页（首次查询，不需要游标条件）
SELECT big_id, gantrycode, gantryname, platenumber, snapshottime, lon, lat
FROM ods_rt_szdn_snapshot_flow_addcode
WHERE platenumber = '赣A12345'
  AND snapshottime >= '2025-03-01 00:00:00'
  AND snapshottime <  '2025-07-01 00:00:00'   -- 半开区间：包含 3-6 月
ORDER BY snapshottime DESC, big_id DESC
LIMIT 20;


-- 第2页（用上一页最后一条记录的 snapshottime + big_id 作为游标）
-- 假设第1页最后一条是：snapshottime='2025-05-20 14:30:00', big_id=98765
SELECT big_id, gantrycode, gantryname, platenumber, snapshottime, lon, lat
FROM ods_rt_szdn_snapshot_flow_addcode
WHERE platenumber = '赣A12345'
  AND snapshottime >= '2025-03-01 00:00:00'
  AND snapshottime <  '2025-07-01 00:00:00'
  -- 游标条件：比上一页最后一条更"早"的记录
  AND (snapshottime, big_id) < ('2025-05-20 14:30:00', 98765)
ORDER BY snapshottime DESC, big_id DESC
LIMIT 20;


-- ============================================================
-- 场景2：如果 UI 要求必须支持跳页（OFFSET 无法避免）
-- 用"内层 ID 查询 + 外层回表"的双层查询
-- 性能比直接 SELECT * ... OFFSET 好很多（内层只扫索引）
-- ============================================================

SELECT t.big_id, t.gantrycode, t.gantryname, t.platenumber, t.snapshottime, t.lon, t.lat
FROM (
    -- 内层：只查主键列（可被 (platenumber, snapshottime DESC, big_id DESC) 索引覆盖）
    SELECT big_id
    FROM ods_rt_szdn_snapshot_flow_addcode
    WHERE platenumber = '赣A12345'
      AND snapshottime >= '2025-03-01 00:00:00'
      AND snapshottime <  '2025-07-01 00:00:00'
    ORDER BY snapshottime DESC, big_id DESC
    LIMIT 20 OFFSET 10000   -- 跳第 501 页
) p
JOIN ods_rt_szdn_snapshot_flow_addcode t ON p.big_id = t.big_id
ORDER BY t.snapshottime DESC, t.big_id DESC;


-- ============================================================
-- 场景3：按门架 + 时间范围跨月查询（常见稽查场景）
-- ============================================================

-- Keyset 分页版本
SELECT big_id, gantrycode, gantryname, platenumber, snapshottime
FROM ods_rt_szdn_snapshot_flow_addcode
WHERE gantrycode = 'G0001'
  AND snapshottime >= '2025-04-01 00:00:00'
  AND snapshottime <  '2025-08-01 00:00:00'
  AND (snapshottime, big_id) < ('2025-06-15 10:20:00', 556677)
ORDER BY snapshottime DESC, big_id DESC
LIMIT 20;


-- ============================================================
-- 场景4：收费流水表（ods_lwzxsfsj_fee_records_01）按交易时间跨月查询
-- ============================================================

SELECT big_id, gantrycode, platenumber, transtime, fee
FROM ods_lwzxsfsj_fee_records_01
WHERE platenumber = '赣A12345'
  AND transtime >= '2025-01-01 00:00:00'
  AND transtime <  '2025-07-01 00:00:00'
  AND (transtime, big_id) < ('2025-05-01 08:00:00', 334455)
ORDER BY transtime DESC, big_id DESC
LIMIT 20;


-- ============================================================
-- 场景5：轨迹拟合表（zdata_trail_fitting）按出站时间跨月查询
-- ============================================================

SELECT uuid, plate_key, enter_time, exit_time, extime, mileage, fee_amount
FROM zdata_trail_fitting
WHERE plate_key = '赣A12345_BLUE'
  AND extime >= '2025-03-01 00:00:00'
  AND extime <  '2025-07-01 00:00:00'
  AND (extime, uuid) < ('2025-06-01 12:00:00', 'uuid-last-page')
ORDER BY extime DESC, uuid DESC
LIMIT 20;


-- ============================================================
-- 验证：用 EXPLAIN 确认分区剪枝生效
-- 在 gsql 里执行 EXPLAIN 会输出执行计划
-- 如果只看到 p_202503, p_202504, p_202505, p_202506 这4个分区
-- 说明分区剪枝成功
-- ============================================================

EXPLAIN
SELECT big_id, gantrycode, platenumber, snapshottime
FROM ods_rt_szdn_snapshot_flow_addcode
WHERE platenumber = '赣A12345'
  AND snapshottime >= '2025-03-01 00:00:00'
  AND snapshottime <  '2025-07-01 00:00:00'
ORDER BY snapshottime DESC, big_id DESC
LIMIT 20;


-- ============================================================
-- 需要提前建好的索引（分区表索引会自动应用到所有分区）
-- openGauss 3.0 分区表支持分区级别的本地索引
-- ============================================================

-- 抓拍流水表：按车牌+时间查询
CREATE INDEX IF NOT EXISTS idx_snapflow_plate_time_desc
    ON ods_rt_szdn_snapshot_flow_addcode (platenumber, snapshottime DESC, big_id DESC);

-- 抓拍流水表：按门架+时间查询
CREATE INDEX IF NOT EXISTS idx_snapflow_gantry_time_desc
    ON ods_rt_szdn_snapshot_flow_addcode (gantrycode, snapshottime DESC, big_id DESC);

-- 收费流水表：按车牌+交易时间
CREATE INDEX IF NOT EXISTS idx_fee_plate_transtime_desc
    ON ods_lwzxsfsj_fee_records_01 (platenumber, transtime DESC, big_id DESC);

-- 收费流水表：按门架+交易时间
CREATE INDEX IF NOT EXISTS idx_fee_gantry_transtime_desc
    ON ods_lwzxsfsj_fee_records_01 (gantrycode, transtime DESC, big_id DESC);

-- 轨迹拟合表：按车牌key+出站时间
CREATE INDEX IF NOT EXISTS idx_trail_platekey_extime_desc
    ON zdata_trail_fitting (plate_key, extime DESC, uuid DESC);


-- 收集统计信息（分区表必须定期做，优化器才能正确判断分区剪枝）
ANALYZE ods_rt_szdn_snapshot_flow_addcode;
ANALYZE ods_lwzxsfsj_fee_records_01;
ANALYZE zdata_trail_fitting;


-- ============================================================
-- 分页查询的总条数（用于 UI 显示总页数）
-- 注意：COUNT(*) 在分区表上也要走分区剪枝，WHERE 条件写法必须和列表查询一致
-- ============================================================

SELECT COUNT(*)
FROM ods_rt_szdn_snapshot_flow_addcode
WHERE platenumber = '赣A12345'
  AND snapshottime >= '2025-03-01 00:00:00'
  AND snapshottime <  '2025-07-01 00:00:00';


-- ============================================================
-- 常见错误写法（会导致无法走分区剪枝，禁止使用）
-- ============================================================

-- ❌ 错误1：分区键上包函数
-- SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
-- WHERE EXTRACT(YEAR FROM snapshottime) = 2025
--   AND EXTRACT(MONTH FROM snapshottime) BETWEEN 3 AND 6;

-- ❌ 错误2：用 BETWEEN 代替半开区间（TIMESTAMP 精度问题可能漏数据）
-- SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
-- WHERE snapshottime BETWEEN '2025-03-01' AND '2025-06-30 23:59:59';

-- ❌ 错误3：深分页用 OFFSET（翻到第 1000 页后性能极差）
-- SELECT * FROM ods_rt_szdn_snapshot_flow_addcode
-- WHERE platenumber = '赣A12345'
--   AND snapshottime >= '2025-03-01'
-- ORDER BY snapshottime DESC
-- LIMIT 20 OFFSET 20000;
