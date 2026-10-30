-- ============================================================
-- 脚本：openGauss 3.0 3张核心表分区改造完整SQL
-- 适用版本：openGauss 3.0.x（兼容华为云 GaussDB 主备版）
-- 目标表：ods_rt_szdn_snapshot_flow_addcode（抓拍流水）
--         ods_lwzxsfsj_fee_records_01（收费流水）
--         zdata_trail_fitting（轨迹拟合）
-- 执行方式：gsql -d 数据库名 -U 用户名 -f 分区.sql
--
-- 核心思路：
--   1. 先安全重命名原表（加 _old 后缀）作为备份
--   2. 按时间字段创建 RANGE 分区表，按月划分分区
--   3. 从备份表 INSERT 迁移数据到新分区表
--   4. 创建分区索引（openGauss 分区索引自动应用到所有分区）
--   5. 收集统计信息，确保查询优化器能正确分区剪枝
--   6. DO 块中输出执行日志，便于验证和排查问题
--
-- 注意事项：
--   - openGauss 3.0 支持声明式分区（PARTITION BY RANGE）
--   - ALTER TABLE ... ADD PARTITION ... VALUES LESS THAN (...) 添加分区
--   - 所有 RAISE NOTICE 必须放在 DO ... $$ ... $$ 块内
--   - 数据量较大时，建议分批迁移（例如按月份分多个 INSERT）
-- ============================================================

-- 设置客户端编码，避免中文乱码
SET client_encoding = 'UTF8';


-- ============================================================
-- 第一部分：抓拍流水表分区改造
-- 分区键：snapshottime（抓拍时间）
-- 策略：按月 RANGE 分区
-- ============================================================

DO $$
BEGIN
    -- 只有在原表存在、且 _old 备份表不存在时，才执行重命名
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_rt_szdn_snapshot_flow_addcode'
          AND schemaname = current_schema()
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_rt_szdn_snapshot_flow_addcode_old'
          AND schemaname = current_schema()
    ) THEN
        RAISE NOTICE '[1/5] 正在备份抓拍流水表：ods_rt_szdn_snapshot_flow_addcode -> ods_rt_szdn_snapshot_flow_addcode_old';
        ALTER TABLE ods_rt_szdn_snapshot_flow_addcode
            RENAME TO ods_rt_szdn_snapshot_flow_addcode_old;
    ELSE
        RAISE NOTICE '[1/5] 跳过备份步骤：原表已不存在或已存在 _old 备份表';
    END IF;
END $$;

-- 1.2 创建分区表（空表，后续添加分区）
--   openGauss 3.0 标准语法：PARTITION BY RANGE (column_name)
CREATE TABLE IF NOT EXISTS ods_rt_szdn_snapshot_flow_addcode (
    big_id BIGINT,
    datasource VARCHAR(128),
    deviceid VARCHAR(128),
    gantrycode VARCHAR(128),
    gantryname VARCHAR(128),
    roadcode VARCHAR(128),
    sectioncode VARCHAR(128),
    sectionname VARCHAR(128),
    tollcode VARCHAR(128),
    tollname VARCHAR(128),
    orgcode VARCHAR(128),
    hexcode VARCHAR(128),
    direction SMALLINT,
    pileno VARCHAR(128),
    lon NUMERIC(9,6),
    lat NUMERIC(9,6),
    deviceip VARCHAR(128),
    siteid INTEGER,
    laneid SMALLINT,
    snapshottimeunix BIGINT,
    snapshottime TIMESTAMP,
    receivedtimeunix BIGINT,
    receivedtime TIMESTAMP,
    platenumber VARCHAR(128),
    platecolor VARCHAR(128),
    platecolorcode SMALLINT,
    platetype VARCHAR(128),
    platetypecode SMALLINT,
    plateconfidence SMALLINT,
    carbrand VARCHAR(128),
    carcolor VARCHAR(128),
    carcolorcode SMALLINT,
    cartype VARCHAR(128),
    cartypecode SMALLINT,
    cardirection VARCHAR(128),
    snappicturepath VARCHAR(512),
    loadtime TIMESTAMP,
    gradelevel SMALLINT,
    datauuid VARCHAR(50),
    reserve3 VARCHAR(50)
) PARTITION BY RANGE (snapshottime);


-- 1.3 添加分区的辅助函数（避免分区已存在时报错）
--   openGauss 3.0 的 ADD PARTITION 不支持 IF NOT EXISTS，通过函数实现
CREATE OR REPLACE FUNCTION add_partition_if_not_exists(
    p_table_name    TEXT,
    p_partition_name TEXT,
    p_boundary      TEXT
) RETURNS VOID AS $$
BEGIN
    -- 通过 pg_inherits 判断该分区是否已经存在
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = p_table_name
          AND child.relname = p_partition_name
    ) THEN
        -- 分区不存在：动态执行 ALTER TABLE ADD PARTITION
        --   注意：openGauss 的 RANGE 分区使用 VALUES LESS THAN 语法
        EXECUTE format(
            'ALTER TABLE %I ADD PARTITION %I VALUES LESS THAN (''%s'')',
            p_table_name, p_partition_name, p_boundary
        );
        RAISE NOTICE '  + 添加分区：%.%  (边界: %)', p_table_name, p_partition_name, p_boundary;
    ELSE
        RAISE NOTICE '  - 分区已存在，跳过：%.%', p_table_name, p_partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- 1.4 批量添加月度分区（抓拍流水表）
--   分区 p_YYYYMM 的含义：snapshottime < 下个月 1 号
DO $$
BEGIN
    RAISE NOTICE '[2/5] 正在为抓拍流水表添加分区 ...';
END $$;

SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202501', '2025-02-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202502', '2025-03-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202503', '2025-04-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202504', '2025-05-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202505', '2025-06-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202506', '2025-07-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202507', '2025-08-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202508', '2025-09-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202509', '2025-10-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202510', '2025-11-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202511', '2025-12-01 00:00:00');
SELECT add_partition_if_not_exists('ods_rt_szdn_snapshot_flow_addcode', 'p_202512', '2026-01-01 00:00:00');

-- 添加一个兜底默认分区（MAXVALUE），防止超范围数据插入失败
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'ods_rt_szdn_snapshot_flow_addcode'
          AND child.relname = 'p_default'
    ) THEN
        ALTER TABLE ods_rt_szdn_snapshot_flow_addcode
            ADD PARTITION p_default VALUES LESS THAN (MAXVALUE);
        RAISE NOTICE '  + 添加兜底默认分区：ods_rt_szdn_snapshot_flow_addcode.p_default';
    END IF;
END $$;


-- 1.5 迁移数据：从 _old 备份表 INSERT 到新分区表
DO $$
DECLARE
    v_old_count BIGINT;
    v_new_count BIGINT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_rt_szdn_snapshot_flow_addcode_old'
          AND schemaname = current_schema()
    ) THEN
        EXECUTE 'SELECT COUNT(*) FROM ods_rt_szdn_snapshot_flow_addcode_old' INTO v_old_count;
        RAISE NOTICE '[3/5] 正在迁移抓拍流水表数据，备份表共 % 条记录 ...', v_old_count;

        IF v_old_count > 0 THEN
            INSERT INTO ods_rt_szdn_snapshot_flow_addcode
                SELECT * FROM ods_rt_szdn_snapshot_flow_addcode_old;
            GET DIAGNOSTICS v_new_count = ROW_COUNT;
            RAISE NOTICE '      迁移完成，成功写入 % 条记录到新分区表', v_new_count;
        ELSE
            RAISE NOTICE '      备份表无数据，跳过迁移';
        END IF;
    ELSE
        RAISE NOTICE '      备份表不存在，跳过数据迁移（首次执行脚本属于正常情况）';
    END IF;
END $$;


-- 1.6 创建索引（分区表索引自动应用到所有分区）
CREATE INDEX IF NOT EXISTS idx_snapflow_gantrycode
    ON ods_rt_szdn_snapshot_flow_addcode (gantrycode);

CREATE INDEX IF NOT EXISTS idx_snapflow_platenumber
    ON ods_rt_szdn_snapshot_flow_addcode (platenumber);

CREATE INDEX IF NOT EXISTS idx_snapflow_snapshottime
    ON ods_rt_szdn_snapshot_flow_addcode (snapshottime DESC);

CREATE INDEX IF NOT EXISTS idx_snapflow_platecolorcode
    ON ods_rt_szdn_snapshot_flow_addcode (platecolorcode);

CREATE INDEX IF NOT EXISTS idx_snapflow_combo1
    ON ods_rt_szdn_snapshot_flow_addcode (gantrycode, snapshottime DESC);

CREATE INDEX IF NOT EXISTS idx_snapflow_combo2
    ON ods_rt_szdn_snapshot_flow_addcode (platenumber, snapshottime DESC);

-- 1.7 收集统计信息（对分区表非常重要，影响查询优化器分区剪枝）
ANALYZE ods_rt_szdn_snapshot_flow_addcode;


-- ============================================================
-- 第二部分：收费流水表分区改造
-- 分区键：transtime（交易时间）
-- 策略：按月 RANGE 分区
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_lwzxsfsj_fee_records_01'
          AND schemaname = current_schema()
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_lwzxsfsj_fee_records_01_old'
          AND schemaname = current_schema()
    ) THEN
        RAISE NOTICE '[1/5] 正在备份收费流水表：ods_lwzxsfsj_fee_records_01 -> ods_lwzxsfsj_fee_records_01_old';
        ALTER TABLE ods_lwzxsfsj_fee_records_01
            RENAME TO ods_lwzxsfsj_fee_records_01_old;
    ELSE
        RAISE NOTICE '[1/5] 跳过备份步骤：原表已不存在或已存在 _old 备份表';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS ods_lwzxsfsj_fee_records_01 (
    big_id BIGINT,
    algorithmidentifier VARCHAR(100),
    antennaid VARCHAR(100),
    axlecount INTEGER,
    balanceafter NUMERIC(18,2),
    balancebefore NUMERIC(18,2),
    cardfeesumafter NUMERIC(18,2),
    cardfeesumbefore NUMERIC(18,2),
    computerorder VARCHAR(100),
    consumetime INTEGER,
    cpucardid VARCHAR(100),
    cpucardtype VARCHAR(100),
    cpuenddate VARCHAR(20),
    cpuissueid VARCHAR(100),
    cpunetid VARCHAR(100),
    cpustartdate VARCHAR(20),
    cpuvehicleplate VARCHAR(100),
    cpuvehicletype VARCHAR(100),
    cpurevision VARCHAR(100),
    dealstatus VARCHAR(100),
    discountfee NUMERIC(18,2),
    discountfeegroup VARCHAR(1000),
    enlanetype VARCHAR(100),
    entime TIMESTAMP,
    entolllanehex VARCHAR(100),
    entolllaneid VARCHAR(100),
    entollstationhex VARCHAR(100),
    entollstationid VARCHAR(100),
    fee NUMERIC(18,2),
    feecalresult VARCHAR(1000),
    feecalcspecial VARCHAR(100),
    feecalcspecials VARCHAR(1000),
    feegroup VARCHAR(1000),
    feeinfo1 VARCHAR(1000),
    feeinfo2 VARCHAR(1000),
    feeinfo3 VARCHAR(1000),
    feemileage NUMERIC(18,2),
    feeprovbeginhex VARCHAR(100),
    transtime TIMESTAMP,
    gantrycode VARCHAR(128),
    platenumber VARCHAR(128),
    platecolor VARCHAR(128),
    platecolorcode SMALLINT,
    loadtime TIMESTAMP,
    gradelevel SMALLINT,
    datauuid VARCHAR(50),
    reserve1 VARCHAR(50),
    reserve2 VARCHAR(50),
    reserve3 VARCHAR(50)
) PARTITION BY RANGE (transtime);

DO $$
BEGIN
    RAISE NOTICE '[2/5] 正在为收费流水表添加分区 ...';
END $$;

SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202501', '2025-02-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202502', '2025-03-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202503', '2025-04-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202504', '2025-05-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202505', '2025-06-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202506', '2025-07-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202507', '2025-08-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202508', '2025-09-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202509', '2025-10-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202510', '2025-11-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202511', '2025-12-01 00:00:00');
SELECT add_partition_if_not_exists('ods_lwzxsfsj_fee_records_01', 'p_202512', '2026-01-01 00:00:00');

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'ods_lwzxsfsj_fee_records_01'
          AND child.relname = 'p_default'
    ) THEN
        ALTER TABLE ods_lwzxsfsj_fee_records_01
            ADD PARTITION p_default VALUES LESS THAN (MAXVALUE);
    END IF;
END $$;

DO $$
DECLARE
    v_old_count BIGINT;
    v_new_count BIGINT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'ods_lwzxsfsj_fee_records_01_old'
          AND schemaname = current_schema()
    ) THEN
        EXECUTE 'SELECT COUNT(*) FROM ods_lwzxsfsj_fee_records_01_old' INTO v_old_count;
        RAISE NOTICE '[3/5] 正在迁移收费流水表数据，备份表共 % 条记录 ...', v_old_count;
        IF v_old_count > 0 THEN
            INSERT INTO ods_lwzxsfsj_fee_records_01
                SELECT * FROM ods_lwzxsfsj_fee_records_01_old;
            GET DIAGNOSTICS v_new_count = ROW_COUNT;
            RAISE NOTICE '      迁移完成，成功写入 % 条记录', v_new_count;
        END IF;
    ELSE
        RAISE NOTICE '      备份表不存在，跳过数据迁移';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_fee_transtime
    ON ods_lwzxsfsj_fee_records_01 (transtime DESC);
CREATE INDEX IF NOT EXISTS idx_fee_platenumber
    ON ods_lwzxsfsj_fee_records_01 (platenumber);
CREATE INDEX IF NOT EXISTS idx_fee_gantrycode
    ON ods_lwzxsfsj_fee_records_01 (gantrycode);
CREATE INDEX IF NOT EXISTS idx_fee_combo
    ON ods_lwzxsfsj_fee_records_01 (gantrycode, transtime DESC);

ANALYZE ods_lwzxsfsj_fee_records_01;


-- ============================================================
-- 第三部分：轨迹拟合表分区改造
-- 分区键：extime（出站时间）
-- 策略：按月 RANGE 分区
-- ============================================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'zdata_trail_fitting'
          AND schemaname = current_schema()
    ) AND NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'zdata_trail_fitting_old'
          AND schemaname = current_schema()
    ) THEN
        RAISE NOTICE '[1/5] 正在备份轨迹拟合表：zdata_trail_fitting -> zdata_trail_fitting_old';
        ALTER TABLE zdata_trail_fitting
            RENAME TO zdata_trail_fitting_old;
    ELSE
        RAISE NOTICE '[1/5] 跳过备份步骤：原表已不存在或已存在 _old 备份表';
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS zdata_trail_fitting (
    uuid VARCHAR(255),
    type SMALLINT,
    point_count INTEGER,
    plate_key VARCHAR(255),
    enter_time TIMESTAMP,
    exit_time TIMESTAMP,
    extime TIMESTAMP,
    trail_points TEXT,
    create_time TIMESTAMP,
    gantrycodes VARCHAR(2000),
    enter_gantry_code VARCHAR(128),
    exit_gantry_code VARCHAR(128),
    enter_gantry_name VARCHAR(128),
    exit_gantry_name VARCHAR(128),
    mileage NUMERIC(18,2),
    fee_amount NUMERIC(18,2),
    reserved1 VARCHAR(255),
    reserved2 VARCHAR(255),
    reserved3 VARCHAR(255)
) PARTITION BY RANGE (extime);

DO $$
BEGIN
    RAISE NOTICE '[2/5] 正在为轨迹拟合表添加分区 ...';
END $$;

SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202501', '2025-02-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202502', '2025-03-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202503', '2025-04-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202504', '2025-05-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202505', '2025-06-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202506', '2025-07-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202507', '2025-08-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202508', '2025-09-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202509', '2025-10-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202510', '2025-11-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202511', '2025-12-01 00:00:00');
SELECT add_partition_if_not_exists('zdata_trail_fitting', 'p_202512', '2026-01-01 00:00:00');

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'zdata_trail_fitting'
          AND child.relname = 'p_default'
    ) THEN
        ALTER TABLE zdata_trail_fitting
            ADD PARTITION p_default VALUES LESS THAN (MAXVALUE);
    END IF;
END $$;

DO $$
DECLARE
    v_old_count BIGINT;
    v_new_count BIGINT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_catalog.pg_tables
        WHERE tablename = 'zdata_trail_fitting_old'
          AND schemaname = current_schema()
    ) THEN
        EXECUTE 'SELECT COUNT(*) FROM zdata_trail_fitting_old' INTO v_old_count;
        RAISE NOTICE '[3/5] 正在迁移轨迹拟合表数据，备份表共 % 条记录 ...', v_old_count;
        IF v_old_count > 0 THEN
            INSERT INTO zdata_trail_fitting
                SELECT * FROM zdata_trail_fitting_old;
            GET DIAGNOSTICS v_new_count = ROW_COUNT;
            RAISE NOTICE '      迁移完成，成功写入 % 条记录', v_new_count;
        END IF;
    ELSE
        RAISE NOTICE '      备份表不存在，跳过数据迁移';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_trail_extime
    ON zdata_trail_fitting (extime DESC);
CREATE INDEX IF NOT EXISTS idx_trail_platekey
    ON zdata_trail_fitting (plate_key);
CREATE INDEX IF NOT EXISTS idx_trail_entertime
    ON zdata_trail_fitting (enter_time);
CREATE INDEX IF NOT EXISTS idx_trail_combo
    ON zdata_trail_fitting (plate_key, extime DESC);

ANALYZE zdata_trail_fitting;


-- ============================================================
-- 第四部分：清理辅助函数，输出验证结果
-- ============================================================

DROP FUNCTION IF EXISTS add_partition_if_not_exists(TEXT, TEXT, TEXT);


DO $$
DECLARE
    rec RECORD;
    v_total BIGINT;
    v_old BIGINT;
    v_new BIGINT;
BEGIN
    RAISE NOTICE '============================================================';
    RAISE NOTICE '           分区改造完成 - 分区列表验证';
    RAISE NOTICE '============================================================';

    -- -------- 1. 抓拍流水表 --------
    RAISE NOTICE ' ';
    RAISE NOTICE '[1/3] 抓拍流水表: ods_rt_szdn_snapshot_flow_addcode';
    RAISE NOTICE '       分区名称              分区边界';
    RAISE NOTICE '       ------------------------------------------';

    FOR rec IN
        SELECT child.relname AS pname,
               pg_catalog.pg_get_expr(child.relpartbound, child.oid, true) AS pbound
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'ods_rt_szdn_snapshot_flow_addcode'
        ORDER BY child.relname
    LOOP
        RAISE NOTICE '       %  %', rpad(rec.pname, 24, ' '), rec.pbound;
    END LOOP;

    -- 行数对比
    SELECT COUNT(*) INTO v_new FROM ods_rt_szdn_snapshot_flow_addcode;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables
               WHERE tablename = 'ods_rt_szdn_snapshot_flow_addcode_old'
                 AND schemaname = current_schema()) THEN
        EXECUTE 'SELECT COUNT(*) FROM ods_rt_szdn_snapshot_flow_addcode_old' INTO v_old;
    ELSE
        v_old := 0;
    END IF;
    RAISE NOTICE '       ------------------------------------------';
    RAISE NOTICE '       备份表行数: %  | 新表行数: %', v_old, v_new;
    IF v_old > 0 AND v_old = v_new THEN
        RAISE NOTICE '       ✓ 数据迁移完整（行数一致）';
    ELSIF v_old > 0 THEN
        RAISE NOTICE '       ⚠ 数据行数不一致，请人工核对！';
    ELSE
        RAISE NOTICE '       (首次执行无历史数据，正常)';
    END IF;


    -- -------- 2. 收费流水表 --------
    RAISE NOTICE ' ';
    RAISE NOTICE '[2/3] 收费流水表: ods_lwzxsfsj_fee_records_01';
    RAISE NOTICE '       分区名称              分区边界';
    RAISE NOTICE '       ------------------------------------------';

    FOR rec IN
        SELECT child.relname AS pname,
               pg_catalog.pg_get_expr(child.relpartbound, child.oid, true) AS pbound
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'ods_lwzxsfsj_fee_records_01'
        ORDER BY child.relname
    LOOP
        RAISE NOTICE '       %  %', rpad(rec.pname, 24, ' '), rec.pbound;
    END LOOP;

    SELECT COUNT(*) INTO v_new FROM ods_lwzxsfsj_fee_records_01;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables
               WHERE tablename = 'ods_lwzxsfsj_fee_records_01_old'
                 AND schemaname = current_schema()) THEN
        EXECUTE 'SELECT COUNT(*) FROM ods_lwzxsfsj_fee_records_01_old' INTO v_old;
    ELSE
        v_old := 0;
    END IF;
    RAISE NOTICE '       ------------------------------------------';
    RAISE NOTICE '       备份表行数: %  | 新表行数: %', v_old, v_new;


    -- -------- 3. 轨迹拟合表 --------
    RAISE NOTICE ' ';
    RAISE NOTICE '[3/3] 轨迹拟合表: zdata_trail_fitting';
    RAISE NOTICE '       分区名称              分区边界';
    RAISE NOTICE '       ------------------------------------------';

    FOR rec IN
        SELECT child.relname AS pname,
               pg_catalog.pg_get_expr(child.relpartbound, child.oid, true) AS pbound
        FROM pg_catalog.pg_inherits inh
        INNER JOIN pg_catalog.pg_class parent ON inh.inhparent = parent.oid
        INNER JOIN pg_catalog.pg_class child  ON inh.inhrelid = child.oid
        WHERE parent.relname = 'zdata_trail_fitting'
        ORDER BY child.relname
    LOOP
        RAISE NOTICE '       %  %', rpad(rec.pname, 24, ' '), rec.pbound;
    END LOOP;

    SELECT COUNT(*) INTO v_new FROM zdata_trail_fitting;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_tables
               WHERE tablename = 'zdata_trail_fitting_old'
                 AND schemaname = current_schema()) THEN
        EXECUTE 'SELECT COUNT(*) FROM zdata_trail_fitting_old' INTO v_old;
    ELSE
        v_old := 0;
    END IF;
    RAISE NOTICE '       ------------------------------------------';
    RAISE NOTICE '       备份表行数: %  | 新表行数: %', v_old, v_new;


    RAISE NOTICE ' ';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '  ✓ 分区改造脚本执行完毕';
    RAISE NOTICE ' ';
    RAISE NOTICE '  后续建议：';
    RAISE NOTICE '    1. 用 EXPLAIN 验证分区剪枝是否生效：';
    RAISE NOTICE '       EXPLAIN SELECT COUNT(*) FROM ods_rt_szdn_snapshot_flow_addcode';
    RAISE NOTICE '           WHERE snapshottime >= ''2025-06-01'' AND snapshottime < ''2025-07-01'';';
    RAISE NOTICE '    2. 确认数据无误后，可清理备份表（谨慎操作）：';
    RAISE NOTICE '       DROP TABLE ods_rt_szdn_snapshot_flow_addcode_old;';
    RAISE NOTICE '       DROP TABLE ods_lwzxsfsj_fee_records_01_old;';
    RAISE NOTICE '       DROP TABLE zdata_trail_fitting_old;';
    RAISE NOTICE '    3. 每月月底前添加下个月的分区（否则新数据会落到 p_default）：';
    RAISE NOTICE '       ALTER TABLE ods_rt_szdn_snapshot_flow_addcode';
    RAISE NOTICE '           ADD PARTITION p_YYYYMM VALUES LESS THAN (''YYYY-MM-01 00:00:00'');';
    RAISE NOTICE '============================================================';
END $$;
