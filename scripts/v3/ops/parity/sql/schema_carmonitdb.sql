
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP TABLE IF EXISTS `base_config_service_area`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `base_config_service_area` (
  `fwqbm` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '判定进入的服务区编码',
  `fwqmc` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '判定进入的服务区名称',
  `lon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `lat` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '维度',
  `road_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线编码',
  `section_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路段编码',
  `pile_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='服务区';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `buss_test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `buss_test` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `bill_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称',
  `bill_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称(字典：1业务2其他)',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '金额',
  `dept_id` bigint DEFAULT NULL COMMENT '部门id',
  `user_id` bigint DEFAULT NULL COMMENT '人员id',
  `apply_time` date DEFAULT NULL COMMENT '申请时间',
  `apply_time2` datetime DEFAULT NULL COMMENT '时间时分秒',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '附件(逗号多个分割)',
  `flow_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程key',
  `flow_ruid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程实例ID',
  `flow_apply_oid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程申请ID',
  `flow_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)',
  `sh_time` datetime DEFAULT NULL COMMENT '审核时间',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='业务测试';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_aduit_free`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_aduit_free` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `confirm_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '确认补缴id',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理单位id',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理单位',
  `user_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '录入人员ids',
  `user_names` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '处理人员',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '拆分金额',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='补缴处理';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_confim_free`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_confim_free` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `link_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '司机名称',
  `link_phone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '联系方式',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '录入单位id',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '录入单位',
  `user_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '录入人员ids',
  `user_names` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '录入人员',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '拆分金额',
  `aduit_amount` decimal(19,2) DEFAULT NULL COMMENT '处理金额',
  `except_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '异常流水ids',
  `escaped_types` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型s',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `car_confim_car_no` (`car_no`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='确认补缴';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_except_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_except_record` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行标识（1人工2ETC）',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '入口时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `total_amount` decimal(19,2) DEFAULT NULL COMMENT '应缴金额',
  `charge_amount` decimal(19,2) DEFAULT NULL COMMENT '收费金额',
  `dif_amount` decimal(19,2) DEFAULT NULL COMMENT '差额',
  `escaped_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）',
  `confirm_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '确认补缴id',
  `remark` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0未补交1.部分补缴2全部补交）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `exceptrecord_car_no` (`car_no`) USING BTREE,
  KEY `exceptrecord_status` (`status`) USING BTREE,
  KEY `exceptrecord_in_time` (`in_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='异常车辆流水';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_fee_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_fee_record` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '入口时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `charge_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易类型（字典：1出口交易2逃费补缴）',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '收费金额',
  `except_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '异常流水id',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费流水';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `escaped_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）',
  `escaped_type_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型名称',
  `escaped_amount` decimal(19,2) DEFAULT NULL COMMENT '逃费金额（元）',
  `escaped_num` int DEFAULT NULL COMMENT '逃费次数(反改)',
  `return_amount` decimal(19,2) DEFAULT NULL COMMENT '累计追缴金额（元）',
  `total_amount` decimal(19,2) DEFAULT NULL COMMENT '应缴金额',
  `charge_amount` decimal(19,2) DEFAULT NULL COMMENT '收费金额',
  `dif_amount` decimal(19,2) DEFAULT NULL COMMENT '差额',
  `auit_org_id` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理单位id',
  `auit_org_name` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理单位',
  `is_white` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否在白名单（0否1是）',
  `white_remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '白名单原因',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '图片(附件ids)',
  `brand` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `plate_color` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色（字典：1白色2黑色）',
  `plate_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `car_color` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色（字典：1白色2黑色）',
  `data_source` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)',
  `data_source_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源名称',
  `last_pass_time` datetime DEFAULT NULL COMMENT '最后通行时间',
  `last_pass_picture` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行图片',
  `last_pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行类型(1?架2收费拍)3服务区)',
  `last_pass_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行地址',
  `last_pass_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行经度',
  `last_pass_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行维度',
  `last_pass_cardirection` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '驾驶(1上行2下行3未知)',
  `road_section_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段id',
  `section_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `road_section_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段名称',
  `next_pass_time` datetime DEFAULT NULL COMMENT '预计下一个通行时间',
  `next_pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行类型',
  `next_pass_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行地址',
  `next_pass_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行经度',
  `next_pass_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行维度',
  `track_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶轨迹id',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行驶轨迹josn',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心id',
  `org_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心名称',
  `gantry_code` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架编号（分离）',
  `road_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `road_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `toll_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `toll_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `link_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '司机名称',
  `link_phone` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '联系方式',
  `fwqbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务区编码',
  `fwqmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务区名称',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `carinfo_car_no` (`car_no`) USING BTREE,
  KEY `carinfo_status` (`status`) USING BTREE,
  KEY `carinfo_escaped_type` (`escaped_type`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='车辆信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_query_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_query_log` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `user_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户ID',
  `user_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户名称',
  `user_ip` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '用户IP',
  `model_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模块菜单(1轨迹单2门架拍识3门架交易流水)',
  `menu_point` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '模块功能(1查看2导出)',
  `query_condition` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '查询条件',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='车辆查询日志';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_route_detail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_route_detail` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `route_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线d',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `data_source` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)',
  `data_source_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源名称',
  `last_pass_time` datetime DEFAULT NULL COMMENT '最后通行时间',
  `last_pass_picture` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行图片',
  `last_pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行类型(1?架2收费拍)3服务区)',
  `last_pass_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行地址',
  `last_pass_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行经度',
  `last_pass_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行维度',
  `last_pass_cardirection` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '驾驶(1上行2下行3未知)',
  `road_section_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段id',
  `road_section_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段名称',
  `next_pass_time` datetime DEFAULT NULL COMMENT '预计下一个通行时间',
  `next_pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行类型',
  `next_pass_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行地址',
  `next_pass_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行经度',
  `next_pass_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行维度',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心id',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心名称',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='常用路线明细';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_route_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_route_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `start_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '起点通行地址',
  `start_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后通行经度',
  `start_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '起点通行维度',
  `end_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终点通行地址',
  `end_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终点通行经度',
  `end_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终点通行维度',
  `route_detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路线明细JOSN',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='常用路线';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_split_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_split_record` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通信标识（1人工2ETC）',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '入口时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '拆分金额',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='拆分流水';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_suspicious`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_suspicious` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `plate_color` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色（字典：1白色2黑色）',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行标识（1人工2ETC）',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '通行时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架id',
  `gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `gantry_time` datetime DEFAULT NULL COMMENT '经过时间',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '图片(附件ids)',
  `out_gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止门架id',
  `out_gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止门架名称',
  `out_gantry_time` datetime DEFAULT NULL COMMENT '终止经过时间',
  `out_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止图片(附件ids)',
  `escaped_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）',
  `escaped_type_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型名称',
  `escaped_num` int DEFAULT NULL COMMENT '异常通行门架次数',
  `is_except` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否为可疑车辆',
  `except_remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '可疑原因',
  `except_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '可疑材料',
  `check_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '核实状态（0未核实1已核实）',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心id',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心名称',
  `is_white` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否在白名单（0否1是）',
  `white_remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '白名单原因',
  `white_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '白名单材料',
  `road_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `road_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `section_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `section_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `track_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶轨迹id',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行驶轨迹josn',
  `track_names` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '轨迹点集合',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `suspicious_car_no` (`car_no`) USING BTREE,
  KEY `suspicious_check_status` (`check_status`) USING BTREE,
  KEY `suspicious_in_time` (`in_time`) USING BTREE,
  KEY `suspicious_out_time` (`out_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='可疑车辆';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_suspicious_back`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_suspicious_back` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `plate_color` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色（字典：1白色2黑色）',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行标识（1人工2ETC）',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '通行时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口站',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架id',
  `gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `gantry_time` datetime DEFAULT NULL COMMENT '经过时间',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '图片(附件ids)',
  `out_gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止门架id',
  `out_gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止门架名称',
  `out_gantry_time` datetime DEFAULT NULL COMMENT '终止经过时间',
  `out_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终止图片(附件ids)',
  `escaped_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）',
  `escaped_type_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型名称',
  `escaped_num` int DEFAULT NULL COMMENT '异常通行门架次数',
  `is_except` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否为可疑车辆',
  `except_remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '可疑原因',
  `except_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '可疑材料',
  `check_status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '核实状态（0未核实1已核实）',
  `org_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心id',
  `org_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心名称',
  `is_white` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否在白名单（0否1是）',
  `white_remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '白名单原因',
  `white_file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '白名单材料',
  `road_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `road_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `section_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `section_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `track_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶轨迹id',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行驶轨迹josn',
  `track_names` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '轨迹点集合',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `suspicious_car_no` (`car_no`) USING BTREE,
  KEY `suspicious_check_status` (`check_status`) USING BTREE,
  KEY `suspicious_in_time` (`in_time`) USING BTREE,
  KEY `suspicious_out_time` (`out_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='可疑车辆';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_suspicious_check`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_suspicious_check` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `suspicous_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否为可疑车辆',
  `escaped_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）',
  `charge_amount` decimal(19,2) DEFAULT NULL COMMENT '收费金额',
  `total_amount` decimal(19,2) DEFAULT NULL COMMENT '应缴金额',
  `dif_amount` decimal(19,2) DEFAULT NULL COMMENT '差额',
  `attachments` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '附件',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='可疑车辆人工核实';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_track_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_track_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '维度',
  `device_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `device_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `lane_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车道编号',
  `snap_time` datetime DEFAULT NULL COMMENT '抓拍时间',
  `receive_time` datetime DEFAULT NULL COMMENT '接收时间',
  `snap_pic` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '抓拍图片',
  `road_section_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段id',
  `road_section_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管理中心路段名称',
  `track_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶轨迹id',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行驶轨迹josn',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='车辆行驶轨迹';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_warning_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_warning_config` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `gantry_code_in` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '进入门架编号（分离）',
  `gantry_name_in` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '进入门架名称',
  `gantry_code_out` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出去门架编号（分离）',
  `gantry_name_out` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出去门架名称',
  `time_span` int DEFAULT NULL COMMENT '判定时间间隔（分钟）',
  `fwqbm` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '判定进入的服务区编码',
  `fwqmc` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '判定进入的服务区名称',
  `lon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `lat` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '维度',
  `road_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线编码',
  `section_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路段编码',
  `pile_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='服务区判定规则';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_warning_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_warning_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆id',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '入口时间',
  `gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架id',
  `gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `gantry_time` datetime DEFAULT NULL COMMENT '经过时间',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '图片(附件ids)',
  `next_pass_time` datetime DEFAULT NULL COMMENT '预计下一个通行时间',
  `next_pass_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行类型',
  `next_pass_address` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行地址',
  `next_pass_longitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行经度',
  `next_pass_latitude` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '预计下一个通行维度',
  `road_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `road_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `section_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `section_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `track_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶轨迹id',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行驶轨迹josn',
  `track_names` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '轨迹点集合',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `warning_gantry_time` (`gantry_time`) USING BTREE,
  KEY `warning_car_no` (`car_no`) USING BTREE,
  KEY `warning_back_col1` (`back_col1`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='预警车辆';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_warning_rule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_warning_rule` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `rule_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则名称',
  `notice_range_id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '预警范围id(包含的路段范围)',
  `notice_range_anme` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '预警范围(包含的路段范围)',
  `notice` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通知',
  `notice_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通知方式',
  `notice_user_id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通知人员id',
  `notice_user_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通知人员',
  `org_id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '所属站/所',
  `org_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '所属站/所',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='预警规则';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `car_white_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_white_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `plate_color` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色（字典：1白色2黑色）',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '相关附件(附件ids)',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='车俩白名单';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `dwd_lczt_fwqjcxx`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dwd_lczt_fwqjcxx` (
  `agent_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '代理主键',
  `yxtzj` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '源系统主键',
  `fwqbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务区编码',
  `fwqmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务区名称',
  `fxdm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '方向代码',
  `fxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '方向名称',
  `jd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `wd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '纬度',
  `sslxbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编号',
  `sslxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `ssldbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编号',
  `ssldmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `sczhkgs` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(K格式)',
  `sczhszgs` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(数值格式)',
  `mj` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '面积(平方米)',
  `synx` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '使用年限',
  `xzqhdm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行政区划代码',
  `xzqhmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行政区划名称',
  `ssglzxbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心编码',
  `ssglzxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心名称',
  `yyrq` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '营业日期',
  `cws` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车位数',
  `sfszlkk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否设置了卡口',
  `cdzs` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '充电桩数',
  `sfcyfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否餐饮服务',
  `sftgzsfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否提供住宿服务',
  `sftgqxfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否提供汽修服务',
  `sftgcsfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否提供超市服务',
  `sftgjyfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否提供加油服务',
  `sftgcshfw` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否提供厕所服务',
  `lyxt` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源系统',
  `load_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '加载日期',
  `all_col_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '全字段MD5'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='服务区基础信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `dwd_lczt_sfsjcxx`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dwd_lczt_sfsjcxx` (
  `agent_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '代理主键',
  `yxtzj` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '源系统主键',
  `sfsbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费所编码',
  `sfsmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费所名称',
  `jd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `wd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '纬度',
  `sslxbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编号',
  `sslxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `ssldbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编号',
  `ssldmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `sczh_k` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(K格式)',
  `sczh_n` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(数值格式)',
  `ssglzxbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心编码',
  `ssglzxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心名称',
  `lyxt` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源系统',
  `load_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '加载日期',
  `all_col_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '全字段MD5'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费所基础信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `dwd_lczt_sfzjcxx`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `dwd_lczt_sfzjcxx` (
  `agent_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '代理主键',
  `yxtzj` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '源系统主键',
  `sfzdm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站代码',
  `sfzmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站名称',
  `jd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `wd` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '纬度',
  `sslxbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编号',
  `sslxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `ssldbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编号',
  `ssldmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `sczh_k` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(K格式)',
  `sczh_n` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所处桩号(数值格式)',
  `ssglzxbm` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心编码',
  `ssglzxmc` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心名称',
  `lyxt` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '来源系统',
  `load_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '加载日期',
  `all_col_pk` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '全字段MD5'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费站基础信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_apply_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_apply_info` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `BILL_OID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '单据OID',
  `BUSS_TYPE` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务类型-字典',
  `FLOW_RUID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程实例ID',
  `MSG_TITLE` varchar(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `MSG_CONTEXT` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '内容',
  `MSG_TYPE` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息类型(1:通知业务，2:办理业务)',
  `MSG_URL` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理的URL',
  `APPLY_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请人',
  `CURRENT_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '当前节点OID(流程节点OID)',
  `PC_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '批次OID',
  `BACK_COL1` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `BACK_COL2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `BACK_COL3` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段3',
  `FLOW_STATUS` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `entrust_info` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程委托数据, json数组',
  PRIMARY KEY (`ID`) USING BTREE,
  KEY `apply_info_create_by` (`create_by`) USING BTREE,
  KEY `apply_info_BILL_OID` (`BILL_OID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='我的申请';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_current_node`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_current_node` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `FLOW_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程OID',
  `CURRENT_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '当前节点OID(流程节点OID)',
  `NODE_ORDER` int DEFAULT NULL COMMENT '节点顺序',
  `NODE_KEY` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点KEY',
  `NODE_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点名称',
  `CONFIG_TYPE` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '当前流程类型(字典：1人员2角色3其他)',
  `CONFIG_ID` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点配置id',
  `CONFIG_NAME` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点配置名称',
  `BILL_OID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '单据OID',
  `AUIT_EMP_OID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理人ID',
  `AUIT_EMP_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理人名称',
  `BACK_COL1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `BACK_COL2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `BACK_COL3` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段3',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`ID`) USING BTREE,
  KEY `current_node_BILL_OID` (`BILL_OID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='流程_当前节点表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_list` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `BILL_OID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '单据OID',
  `BUSS_TYPE` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程类型',
  `TASK_ID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '任务ID',
  `flow_ruid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程实例ID',
  `CURRENT_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '当前节点OID(流程节点OID)',
  `SH_USER` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审核人',
  `SH_KEY` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审核结论KEY（T同意F拒绝R退回S提交）',
  `SH_VALUE` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审核结论（T同意F拒绝R退回S提交）',
  `SH_CONTEXT` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '内容',
  `BACK_COL1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `BACK_COL2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `BACK_COL3` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段3',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`ID`) USING BTREE,
  KEY `flow_list_BILL_OID` (`BILL_OID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='审核历史记录';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_message_dispose`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_message_dispose` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `MID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息外键',
  `BUSS_ID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理对象ID',
  `BUSS_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理对象名称, 业务流消息-处理人id',
  `MSG_STATUS` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息状态（1：已办理，2：未办理）',
  `HANG_TIME` datetime DEFAULT NULL COMMENT '处理时间',
  `DISPOSE_OTHER` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '其他',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`ID`) USING BTREE,
  KEY `msgdisd_MID` (`MID`) USING BTREE,
  KEY `msgdisd_BUSS_ID` (`BUSS_ID`) USING BTREE,
  KEY `msgdisd_MSG_STATUS` (`MSG_STATUS`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='系统消息处理人';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_message_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_message_info` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `BILL_OID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '单据OID',
  `BUSS_TYPE` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务类型-字典',
  `FLOW_RUID` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程实例ID',
  `MSG_TITLE` varchar(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `MSG_CONTEXT` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '内容',
  `MSG_TYPE` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息类型(1:通知业务，2:办理业务)',
  `MSG_URL` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理的URL',
  `PC_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '批次OID',
  `APPLY_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请人',
  `BACK_COL1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `BACK_COL2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `BACK_COL3` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段3',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `message_no` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消息编号',
  PRIMARY KEY (`ID`) USING BTREE,
  KEY `msginfo_MSG_TYPE` (`MSG_TYPE`) USING BTREE,
  KEY `msginfo_BILL_OID` (`BILL_OID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='系统内部消息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_name`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_name` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `FLOW_KEY` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程KEY',
  `FLOW_TITLE` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程名称',
  `FLOW_CONTEXT` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '内容',
  `BUSS_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位id',
  `flow_business_type` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程业务类型',
  PRIMARY KEY (`ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='流程名称';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `flow_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flow_template` (
  `ID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `FLOW_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流程OID',
  `FLOW_TYPE` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '当前流程类型(字典：1正常流程2会签流程)',
  `NODE_ORDER` int DEFAULT NULL COMMENT '节点顺序',
  `NODE_KEY` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点KEY',
  `NODE_NAME` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点名称',
  `NEXT_NODE_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '下一节点OID(-1为当前为最后一个节点)',
  `PREVIOUS_NODE_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上一节点OID(0为开始节点)',
  `RETURN_NUM` int DEFAULT NULL COMMENT '驳回到第几步 0 是发起人',
  `RETURN_NODE_OID` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '驳回节点OID',
  `CONFIG_CONDTION` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点配置条件',
  `CONFIG_TYPE` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '当前流程类型(字典：1人员2角色3其他)',
  `CONFIG_ID` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点配置id',
  `CONFIG_NAME` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节点配置名称',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`ID`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='流程节点';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `gantry_car`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gantry_car` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口站',
  `in_time` datetime DEFAULT NULL COMMENT '通行时间',
  `gantry_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架id',
  `gantryt_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `gantry_time` datetime DEFAULT NULL COMMENT '经过时间',
  `file_ids` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '图片(附件ids)',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='门架拍识查询';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `gantry_trade_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gantry_trade_info` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `car_no` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `car_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `car_vehicle` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `car_num` int DEFAULT NULL COMMENT '轴数',
  `in_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入门架id',
  `in_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入门架',
  `in_time` datetime DEFAULT NULL COMMENT '入门时间',
  `out_station_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口门架id',
  `out_station` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口门架',
  `out_time` datetime DEFAULT NULL COMMENT '出口时间',
  `charge_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易类型（字典：1出口交易2逃费补缴）',
  `amount` decimal(19,2) DEFAULT NULL COMMENT '收费金额',
  `back_col1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段1',
  `back_col2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段2',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `status` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常1停用）',
  `sort` int DEFAULT NULL COMMENT '排序',
  `eps_id` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `create_by` bigint DEFAULT NULL COMMENT '创建人',
  `create_time` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `update_by` bigint DEFAULT NULL COMMENT '更新人',
  `update_time` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='门架交易查询';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `gen_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table` (
  `table_id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `table_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '表名称',
  `table_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '表描述',
  `sub_table_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '关联子表的表名',
  `sub_table_fk_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '子表关联的外键名',
  `class_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '实体类名称',
  `tpl_category` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'crud' COMMENT '使用的模板（crud单表操作 tree树表操作）',
  `package_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '生成包路径',
  `module_name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '生成模块名',
  `business_name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '生成业务名',
  `function_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '生成功能名',
  `function_author` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '生成功能作者',
  `gen_type` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '生成代码方式（0zip压缩包 1自定义路径）',
  `gen_path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '/' COMMENT '生成路径（不填默认项目路径）',
  `options` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '其它生成选项',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`table_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=435 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='代码生成业务表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `gen_table_column`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `gen_table_column` (
  `column_id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `table_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '归属表编号',
  `column_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '列名称',
  `column_comment` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '列描述',
  `column_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '列类型',
  `java_type` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'JAVA类型',
  `java_field` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'JAVA字段名',
  `is_pk` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否主键（1是）',
  `is_increment` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否自增（1是）',
  `is_required` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否必填（1是）',
  `is_insert` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否为插入字段（1是）',
  `is_edit` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否编辑字段（1是）',
  `is_list` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否列表字段（1是）',
  `is_query` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否查询字段（1是）',
  `query_type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'EQ' COMMENT '查询方式（等于、不等于、大于、小于、范围）',
  `html_type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '显示类型（文本框、文本域、下拉框、复选框、单选框、日期控件）',
  `dict_type` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典类型',
  `sort` int DEFAULT NULL COMMENT '排序',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `link_table_id` bigint DEFAULT NULL COMMENT '关联表id',
  `single_selection` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否生成 单选 Dialog, 0 => 不生成, 1 => 生成',
  `multiple_selections` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否生成 多选 Dialog, 0 => 不生成, 1 => 生成',
  `dialog_search_column_ids` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'dialog 搜索字段ids, 多个使用逗号拼接',
  `dialog_list_column_ids` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'dialog 列表字段ids, 多个使用逗号拼接',
  `field_map_string` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '字段映射 规则 : 当前表字段id:关联表映射id, 当前表字段id:关联表映射id .......',
  PRIMARY KEY (`column_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1000000882 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='代码生成业务表字段';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `geometry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `geometry` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `lxbh` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '路线编号',
  `lxfx` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT '路线方向',
  `qdzh` float DEFAULT NULL COMMENT '起点桩号',
  `zdzh` float DEFAULT NULL COMMENT '终点桩号',
  `paths` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT '经纬度',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1377198145 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='路线经纬度';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_cxzt_fwqclls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_cxzt_fwqclls` (
  `big_id` bigint NOT NULL,
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `targetpicurl` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '抓拍照片url',
  `vehiclebrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `platepicurl` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车牌照片',
  `rollvehiclestype` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车类型',
  `plateno` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌',
  `directionname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '方向名称',
  `platetype` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `dangmark` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否危化品车',
  `crosstime` datetime DEFAULT NULL COMMENT '通过时间（分区字段）',
  `axles` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '坐标',
  `devicename` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备名称',
  `ipaddress` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'IP地址',
  `servicename` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '服务区名称',
  `vehicletype` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `load_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '加载时间',
  `grade_level` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '分类分级'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='服务区车辆流水';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_lwzxsfsj_fee_gantry_fusion_01`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_lwzxsfsj_fee_gantry_fusion_01` (
  `big_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `actualfeeclass` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '实际计费方式',
  `axlecount` int DEFAULT NULL COMMENT '车轴数',
  `createtime` datetime DEFAULT NULL COMMENT '创建时间',
  `discountfee` int DEFAULT NULL COMMENT '优惠金额',
  `electricalpercentage` int DEFAULT NULL COMMENT '单片式OBU/CPC卡电量百分比',
  `enaxlecount` int DEFAULT NULL COMMENT '入口车轴数',
  `entime` datetime DEFAULT NULL COMMENT '入站时间',
  `entolllanehex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道hex',
  `entolllaneid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道ID',
  `entollstationid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口收费站编码',
  `entollstationname` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口收费站名称',
  `envehicleclass` int DEFAULT NULL COMMENT '入口车种',
  `envehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车牌号+车牌类型',
  `envehicleidcolor` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车牌号+颜色',
  `envehicletype` int DEFAULT NULL COMMENT '入口车型',
  `enweight` int DEFAULT NULL COMMENT '入口称重',
  `entryoperatorid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口操作人员id',
  `extime` datetime DEFAULT NULL COMMENT '出站时间',
  `extolllaneid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车道号编码',
  `extollstationid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口收费站编码',
  `extollstationname` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口收费站名称',
  `exvehicleclass` int DEFAULT NULL COMMENT '出口车种',
  `exvehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车牌号+车牌类型',
  `exvehicletype` int DEFAULT NULL COMMENT '出口车型',
  `exweight` int DEFAULT NULL COMMENT '出口称重',
  `exitid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口id',
  `fee` int DEFAULT NULL COMMENT '费用',
  `feeboardplay` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '费显显示信息',
  `feemileage` int DEFAULT NULL COMMENT '收费里程',
  `feerate` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易金额占比',
  `fusiondesc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '融合描述',
  `fusionflag` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '融合标识,',
  `id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'ID',
  `identification` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '开票标识',
  `identifyvehicleid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口识别车牌号+车牌类型',
  `identifyvehicleidcolor` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口识别车牌号+颜色',
  `lanetype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口车道类型',
  `mediano` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '介质编码',
  `mediatype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通行介质',
  `nocardcount` int DEFAULT NULL COMMENT '标签无卡累计次数',
  `obuid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'OBU序号编码',
  `obusign` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'OBU 单/双片标识',
  `obutotalamount` int DEFAULT NULL COMMENT '0BU 总累计交易金额',
  `obutotaldiscountamount` int DEFAULT NULL COMMENT 'OBU累计优惠后通行费金额',
  `operid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '操作id',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '参数',
  `passid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通行id',
  `paycardid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '支付id',
  `payfee` int DEFAULT NULL COMMENT '应收总额',
  `paytype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '支付类型',
  `provfee` int DEFAULT NULL,
  `provtranscount` int DEFAULT NULL COMMENT '本省交易成功次数',
  `provincecount` int DEFAULT NULL COMMENT '通行省份个数',
  `receivetime` datetime DEFAULT NULL COMMENT '接收时间',
  `shift` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '工班号',
  `shortfee` int DEFAULT NULL COMMENT '最短收费金额',
  `shortfeemileage` int DEFAULT NULL COMMENT '最短路径里程数',
  `signstatus` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '标记状态',
  `spcrateversion` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '全网最小费额费率版本号',
  `specialtype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '特殊类型',
  `splitprovince` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '多条省内交易信息',
  `tac` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'TAC码',
  `terminalno` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '终端机编号',
  `terminaltransno` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'PSAM卡脱机交易序列号',
  `transfee` int DEFAULT NULL COMMENT '卡面扣费金额',
  `transpaytype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '交易支付类型',
  `transtype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '交易类型',
  `vehiclesign` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车辆识别标识',
  `vehiclesignid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车牌识别流水号',
  `vid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车牌号ID',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` int DEFAULT NULL COMMENT '分类分级',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='交易流水';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_lwzxsfsj_fee_records_01`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_lwzxsfsj_fee_records_01` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `algorithmidentifier` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '算法标识',
  `antennaid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '天线ID编号(天线头编号)',
  `axlecount` int DEFAULT NULL COMMENT '车轴数',
  `balanceafter` decimal(18,2) DEFAULT NULL COMMENT '交易后余额',
  `balancebefore` decimal(18,2) DEFAULT NULL COMMENT '交易前余额',
  `cardfeesumafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后卡片累计金额',
  `cardfeesumbefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前卡片累计金额',
  `computerorder` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '控制器序号',
  `consumetime` int DEFAULT NULL COMMENT '交易耗时（单位：ms）',
  `cpucardid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU卡编号',
  `cpucardtype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU卡类型',
  `cpuenddate` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU截止日期',
  `cpuissueid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU卡片发行方标识',
  `cpunetid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU卡片网络编号',
  `cpustartdate` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU起始日期',
  `cpuvehicleplate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU 内车牌号码',
  `cpuvehicletype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU内车型',
  `cpuversion` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPU用户卡版本号',
  `dealstatus` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '处理状态',
  `discountfee` decimal(18,2) DEFAULT NULL COMMENT '优惠金额',
  `discountfeegroup` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '优惠金额组合',
  `enlanetype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道类型',
  `entime` datetime DEFAULT NULL COMMENT '进站时间',
  `entolllaneid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '进站收费站车道号',
  `entollstationhex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '进站收费站hex编码',
  `fee` decimal(18,2) DEFAULT NULL COMMENT '费用',
  `feecalcresult` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '计费模块响应计费结果',
  `feecalcspecial` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费接口特情值',
  `feecalcspecials` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '计费特情值组合',
  `feegroup` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '交易金额组合',
  `feeinfo1` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '计费信息1',
  `feeinfo2` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '计费信息2',
  `feeinfo3` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '计费信息3',
  `feemileage` decimal(18,2) DEFAULT NULL COMMENT '收费里程',
  `feeprovbeginhex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '本省计费起点',
  `feespare1` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费协议保留字段1',
  `feespare2` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费协议保留字段2',
  `feevehicletype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费车型',
  `gantryhex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架Hex值',
  `gantryhexopposite` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '对向门架Hex值',
  `gantryid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编码',
  `gantryordernum` int DEFAULT NULL COMMENT '门架顺序号',
  `gantrytype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架类型',
  `holidaystate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '节假日状态',
  `hourbatchno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '小时批次号',
  `keyversion` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '消费密钥版本号',
  `lastgantryhex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上一个门架的hex编号',
  `lastgantrytime` datetime DEFAULT NULL COMMENT '通过上一个门架的时间',
  `matchstatus` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '匹配状态',
  `mediatype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行介质类型',
  `nocardtimesafter` int DEFAULT NULL COMMENT '本次交易后累计无卡次数',
  `nocardtimesbefore` int DEFAULT NULL COMMENT '本次交易前累计无卡次数',
  `obuelectrical` int DEFAULT NULL COMMENT 'OBU/CPC卡电量百分比',
  `obuenddate` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC截止日期',
  `obufeesumafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后标签累计实收金额',
  `obufeesumbefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前标签累计实收金额',
  `obuinfotyperead` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '读取标签入口信息类型',
  `obuinfotypewrite` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '本次写入标签入口信息类型',
  `obuissueid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC发行方标识',
  `obulastgantryhex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU中上一个门架HEX',
  `obulastgantrytime` datetime DEFAULT NULL COMMENT 'OBU中通过上一个门架时间',
  `obumac` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU /CPC物理地址',
  `obumileageafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后标签累计里程',
  `obumileagebefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前标签累计里程',
  `obupassstate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标签入口状态',
  `obupayfeesumafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后标签累计应收金额',
  `obupayfeesumbefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前标签累计应收金额',
  `obuprovfeesumafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后标签累计金额（省内）',
  `obuprovfeesumbefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前标签累计金额 （省内）',
  `obuprovpayfeesumafter` decimal(18,2) DEFAULT NULL COMMENT '本次交易后标签累计应收金额（省内）',
  `obuprovpayfeesumbefore` decimal(18,2) DEFAULT NULL COMMENT '本次交易前标签累计应收金额（省内）',
  `obuprovtradesuccnumafter` int DEFAULT NULL COMMENT '省内本次交易后标签累计写入成功数量',
  `obuprovtradesuccnumbefore` int DEFAULT NULL COMMENT '省内本次交易前标签累计写入成功数量',
  `obusign` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU 单/双片标识',
  `obusn` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC序号编码',
  `obustartdate` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC起始日期',
  `obustate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC状态',
  `obutotaltradesuccnumafter` int DEFAULT NULL COMMENT '本次交易后标签累计写入成功总量',
  `obutotaltradesuccnumbefore` int DEFAULT NULL COMMENT '本次交易前标签累计写入成功总量',
  `obutraderesult` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标签写入结果',
  `obuvehicleplate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'obu车牌',
  `obuvehicletype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'obu车牌类型',
  `obuversion` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'OBU/CPC版本号',
  `params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `passid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行id',
  `passstate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行状态',
  `pathfitflag` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '本次计费拟合结果标识',
  `payfee` decimal(18,2) DEFAULT NULL COMMENT '应收金额',
  `payfeegroup` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '应收金额组合',
  `pcrsuversion` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'PC-RSU接口协议版本号',
  `provminfee` decimal(18,2) DEFAULT NULL COMMENT '本省累计通行金额参考',
  `provincenumafter` int DEFAULT NULL COMMENT '本次交易后累计省份数量',
  `provincenumbefore` int DEFAULT NULL COMMENT '本次交易前累计省份数量',
  `ratecompute` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费模块计费模式',
  `ratefitcount` int DEFAULT NULL COMMENT '计费模块拟合点总数',
  `rateversion` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费模块和计费参数版本号',
  `readciphertextverify` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '本次交易读取的EF04加密摘要验证结果',
  `receivetime` datetime DEFAULT NULL COMMENT '接收时间',
  `servicetype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易的服务类型',
  `stationdbtime` datetime DEFAULT NULL COMMENT '门架后台入库时间',
  `stationdealtime` datetime DEFAULT NULL COMMENT '门架后台处理时间',
  `stationmatchtime` datetime DEFAULT NULL COMMENT '门架后台匹配时间',
  `stationvalidtime` datetime DEFAULT NULL COMMENT '门架后台去重时间',
  `tac` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'TAC码',
  `terminalno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终端机编号',
  `terminaltransno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'PSAM卡脱机交易序列号',
  `tollintervalid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '收费单元编号组合',
  `tollintervalsign` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费单元处理标识',
  `totalweight` decimal(18,2) DEFAULT NULL COMMENT '车货总重',
  `tradeid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '计费交易编号',
  `tradereadciphertext` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '本次交易读取的EF04加密摘要',
  `traderesult` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '卡片复合交易结果',
  `tradetype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易类型',
  `tradewriteciphertext` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '本次交易生成的EF04加密摘要',
  `transfee` decimal(18,2) DEFAULT NULL COMMENT '卡面扣费金额',
  `transno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'IC卡交易序号',
  `transtime` datetime DEFAULT NULL COMMENT '计费交易时间',
  `transtype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易类型标识',
  `validstatus` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '去重状态',
  `vehicleclass` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `vehiclehight` decimal(18,2) DEFAULT NULL COMMENT '车高',
  `vehiclelength` decimal(18,2) DEFAULT NULL COMMENT '车长',
  `vehicleplate` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号+类型',
  `vehicleseat` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆座位数/载重',
  `vehiclesign` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆状态标识',
  `vehicletype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `vehicleusertype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆用户类型',
  `vehiclewidth` decimal(18,2) DEFAULT NULL COMMENT '车宽',
  `verifycode` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '校验码',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` int DEFAULT NULL COMMENT '分类分级',
  `readcipherverify` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '本次交易读取的EF04加密摘要验证结果',
  `tradewritecipher` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '本次交易生成的EF04加密摘要',
  `tradereadcipher` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '本次交易读取的EF04加密摘要',
  `cid` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'cid',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费记录表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_lwzxsfsj_fee_station_enter_01`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_lwzxsfsj_fee_station_enter_01` (
  `big_id` bigint NOT NULL,
  `cardid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'CPC卡或ETC卡的编号',
  `electricalpercentage` int DEFAULT NULL COMMENT '单片式OBU/CPC卡电量百分比',
  `enaxlecount` int DEFAULT NULL COMMENT '入站车轴数',
  `entime` datetime DEFAULT NULL COMMENT '入站时间',
  `entolllanehex` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道hex',
  `entolllaneid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道id',
  `entollstationid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口收费站编码',
  `enweight` decimal(18,2) DEFAULT NULL COMMENT '入口称重',
  `id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'ID',
  `identifyvehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号+车牌类型',
  `lanetype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车道类型',
  `mediatype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '介质类型',
  `operid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '操作id',
  `operationmedia` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '作业媒介',
  `params` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '参数',
  `passid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通行id',
  `receivetime` datetime DEFAULT NULL COMMENT '接收时间',
  `shift` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '工班号',
  `signstatus` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '标记状态',
  `specialtype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '特殊类型',
  `tac` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'TAC码',
  `terminalno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终端机编号',
  `terminaltransno` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'PSAM卡脱机交易序列号',
  `transfee` decimal(18,2) DEFAULT NULL COMMENT '交易金额',
  `transtype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '交易类型',
  `vcount` int DEFAULT NULL COMMENT '总数',
  `vehicleclass` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车种',
  `vehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号+车牌类型',
  `vehiclesign` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆识别标识',
  `vehiclesignid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌识别流水号',
  `vehicletype` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '分类分级',
  `cid` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'cid'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费站入口数据表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_lwzxsfsj_fee_station_exit_01`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_lwzxsfsj_fee_station_exit_01` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `actualfeeclass` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '实际计费方式',
  `axlecount` smallint DEFAULT NULL COMMENT '车轴数',
  `discountfee` int DEFAULT NULL COMMENT '优惠金额',
  `electricalpercentage` smallint DEFAULT NULL COMMENT '单片式OBU/CPC卡电量百分比',
  `enaxlecount` smallint DEFAULT NULL COMMENT '入站车轴数',
  `entime` datetime DEFAULT NULL COMMENT '进站时间',
  `entolllanehex` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口车道hex',
  `entolllaneid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '进站收费站车道号',
  `entollstationid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口收费站编码',
  `entollstationname` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口收费站名称',
  `envehicleclass` smallint DEFAULT NULL COMMENT '入口车种',
  `envehicleid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口车牌号+车牌类型',
  `envehicletype` smallint DEFAULT NULL COMMENT '入口车型',
  `enweight` int DEFAULT NULL COMMENT '入口称重',
  `entryoperatorid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口操作人员id',
  `extime` datetime DEFAULT NULL COMMENT '出站时间',
  `extolllaneid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口车道号编码',
  `extollstationid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口收费站编码',
  `extollstationname` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口收费站名称',
  `exvehicleclass` smallint DEFAULT NULL COMMENT '出口车种',
  `exvehicleid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口车牌号+车牌类型',
  `exvehicletype` smallint DEFAULT NULL COMMENT '出口车型',
  `exweight` int DEFAULT NULL COMMENT '出口称重',
  `fee` int DEFAULT NULL COMMENT '费用',
  `feeboardplay` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '费显显示信息',
  `feemileage` int DEFAULT NULL COMMENT '收费里程',
  `feerate` decimal(10,4) DEFAULT NULL COMMENT '交易金额占比',
  `id` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'ID',
  `identification` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '开票标识',
  `identifyvehicleid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车牌号+车牌类型',
  `lanetype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车道类型',
  `mediano` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '介质编码',
  `mediatype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通行介质类型',
  `nocardcount` smallint DEFAULT NULL COMMENT '标签无卡累计次数',
  `obuid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'OBU序号编码',
  `obusign` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'OBU 单/双片标识',
  `obutotalamount` int DEFAULT NULL COMMENT '0BU 总累计交易金额',
  `obutotaldiscountamount` int DEFAULT NULL COMMENT 'OBU累计优惠后通行费金额',
  `operid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '操作id',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '参数',
  `passid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '通行id',
  `paycardid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '支付id',
  `payfee` int DEFAULT NULL COMMENT '应收金额',
  `paytype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '支付类型',
  `provfee` int DEFAULT NULL,
  `provtranscount` smallint DEFAULT NULL COMMENT '本省交易成功次数',
  `provincecount` smallint DEFAULT NULL COMMENT '通行省份个数',
  `receivetime` datetime DEFAULT NULL COMMENT '接收时间',
  `shift` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '工班号',
  `shortfee` int DEFAULT NULL COMMENT '最短收费金额',
  `shortfeemileage` int DEFAULT NULL COMMENT '最短路径里程数',
  `signstatus` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '标记状态',
  `spcrateversion` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '全网最小费额费率版本号',
  `specialtype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '特殊类型',
  `splitprovince` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '多条省内交易信息',
  `tac` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'TAC码',
  `terminalno` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '终端机编号',
  `terminaltransno` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT 'PSAM卡脱机交易序列号',
  `transfee` int DEFAULT NULL COMMENT '卡面扣费金额',
  `transpaytype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '交易支付类型',
  `transtype` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '交易类型标识',
  `vehiclesign` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车辆状态标识',
  `vehiclesignid` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车牌识别流水号',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '分类分级',
  `cid` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'cid',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_202508`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_202508` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_202611`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_202611` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_202612`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_202612` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_202701`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_202701` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_202702`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_202702` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_addcode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_addcode` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `gantrycode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号（分离）',
  `gantryname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架名称',
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线名称',
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段名称',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站名称',
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构编码',
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属管理中心机构名称',
  `hexcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架二进制编号',
  `direction` smallint DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pileno` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` decimal(9,6) DEFAULT NULL COMMENT '经度',
  `lat` decimal(9,6) DEFAULT NULL COMMENT '纬度',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL,
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'uuid',
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备用字段',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_provcapture_addcode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_provcapture_addcode` (
  `big_id` bigint NOT NULL,
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tailcapturetimeunix` bigint DEFAULT NULL,
  `tailcapturetime` datetime DEFAULT NULL,
  `extendattribute` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci,
  `smallsideimagewidth` smallint DEFAULT NULL,
  `axletype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `smallsideimageheight` smallint DEFAULT NULL COMMENT '小侧图高度',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `cover` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '遮挡信息',
  `averageauthoritative` smallint DEFAULT NULL COMMENT '平均可信度',
  `headlanecode` smallint DEFAULT NULL COMMENT '车头车道号',
  `specialvehicle` smallint DEFAULT NULL COMMENT '特殊车辆标识',
  `carlength` smallint DEFAULT NULL COMMENT '车长',
  `resulttype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '结果类型',
  `carhight` smallint DEFAULT NULL COMMENT '车高',
  `carmodelscode` smallint DEFAULT NULL COMMENT '车型编码',
  `carmodels` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车型',
  `laneposition` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车道位置',
  `firstauthoritative` smallint DEFAULT NULL COMMENT '首字可信度',
  `tailplateimageheight` smallint DEFAULT NULL COMMENT '车尾车牌图高度',
  `axlecount` smallint DEFAULT NULL COMMENT '车轴数',
  `plateimagewidth` smallint DEFAULT NULL COMMENT '车牌图宽度',
  `specialclass` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '特殊类别',
  `tailplatenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车尾车牌号',
  `tailimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车尾图路径',
  `sidecapturetimeunix` bigint DEFAULT NULL COMMENT '车身图采集时间(Unix时间戳)',
  `sidecapturetime` datetime DEFAULT NULL COMMENT '车身图采集时间(可读格式)',
  `sidelanecode` smallint DEFAULT NULL COMMENT '车身车道号',
  `wheelbase` smallint DEFAULT NULL COMMENT '轴距',
  `attached` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '附加信息',
  `wheelcount` smallint DEFAULT NULL COMMENT '车轮数量',
  `guid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '全局唯一标识符',
  `sideimagewidth` smallint DEFAULT NULL COMMENT '车身图宽度',
  `plateimageheight` smallint DEFAULT NULL COMMENT '车牌图高度',
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据来源',
  `carclass` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆分类',
  `gantryid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架编号',
  `smallsideimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '小侧图路径',
  `headimageheight` smallint DEFAULT NULL COMMENT '车头图高度',
  `sidescenetypecode` smallint DEFAULT NULL COMMENT '车侧拍摄场景编码',
  `sidescenetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车侧拍摄场景',
  `tailimagewidth` smallint DEFAULT NULL COMMENT '车尾图宽度',
  `envstate` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '环境状态',
  `headscenetypecode` smallint DEFAULT NULL COMMENT '车头拍摄场景编码',
  `headscenetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车头拍摄场景',
  `sidedrivingdirectioncode` smallint DEFAULT NULL COMMENT '车侧行驶方向编码',
  `sidedrivingdirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车侧行驶方向',
  `sideimageheight` smallint DEFAULT NULL COMMENT '车身图高度',
  `speed` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车速',
  `tailplateimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车尾车牌图路径',
  `headdrivingdirectioncode` smallint DEFAULT NULL COMMENT '车头行驶方向编码',
  `headdrivingdirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车头行驶方向',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `plateimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌图路径',
  `changelane` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '变道信息',
  `sideimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车身图路径',
  `tailplateposition` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车尾车牌位置',
  `headimagewidth` smallint DEFAULT NULL COMMENT '车头图宽度',
  `headimage` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车头图路径',
  `carweight` smallint DEFAULT NULL COMMENT '车重',
  `tailimageheight` smallint DEFAULT NULL COMMENT '车尾图高度',
  `devicecode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号码',
  `tailplatecolorcode` smallint DEFAULT NULL COMMENT '车尾车牌颜色编码',
  `tailplatecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车尾车牌颜色',
  `uploadtimeunix` bigint DEFAULT NULL COMMENT '上传时间(Unix时间戳)',
  `uploadtime` datetime DEFAULT NULL COMMENT '上传时间(可读格式)',
  `impostoraxlecount` smallint DEFAULT NULL COMMENT '假轴数',
  `taillanecode` smallint DEFAULT NULL COMMENT '车尾车道号',
  `siteid` smallint DEFAULT NULL COMMENT '站点ID',
  `headcapturetimeunix` bigint DEFAULT NULL COMMENT '车头图采集时间(Unix时间戳)',
  `headcapturetime` datetime DEFAULT NULL COMMENT '车头图采集时间(可读格式)',
  `plateposition` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌位置',
  `tailplateimagewidth` smallint DEFAULT NULL COMMENT '车尾车牌图宽度',
  `loadtime` datetime DEFAULT NULL,
  `gradelevel` smallint DEFAULT NULL,
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve1` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve2` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='省界抓拍';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_stationcapture_addcode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_rt_szdn_snapshot_flow_stationcapture_addcode` (
  `big_id` bigint NOT NULL,
  `datasource` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `cameratype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备类型',
  `deviceid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备编号',
  `deviceip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备IP',
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站编码',
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站名称',
  `orgcode` bigint DEFAULT NULL COMMENT '组织机构编码',
  `siteid` int DEFAULT NULL COMMENT '站点ID',
  `laneid` smallint DEFAULT NULL COMMENT '车道编号',
  `snapshottimeunix` bigint DEFAULT NULL COMMENT '抓拍时间Unix格式',
  `snapshottime` datetime DEFAULT NULL COMMENT '抓拍时间',
  `receivedtimeunix` bigint DEFAULT NULL COMMENT '接收时间Unix格式',
  `receivedtime` datetime DEFAULT NULL COMMENT '接收时间',
  `platenumber` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `platecolorcode` smallint DEFAULT NULL COMMENT '车牌颜色编码',
  `platecolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色',
  `platetypecode` smallint DEFAULT NULL COMMENT '车牌类型编码',
  `platetype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型',
  `plateconfidence` smallint DEFAULT NULL COMMENT '车牌置信度',
  `carbrand` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆品牌',
  `carcolorcode` smallint DEFAULT NULL COMMENT '车辆颜色编码',
  `carcolor` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色',
  `cartypecode` smallint DEFAULT NULL COMMENT '车辆类型编码',
  `cartype` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型',
  `cardirectioncode` smallint DEFAULT NULL COMMENT '行驶方向编码',
  `cardirection` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '行驶方向',
  `snappicturepath` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片路径',
  `loadtime` datetime DEFAULT NULL COMMENT '加载时间',
  `gradelevel` smallint DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `maindirection` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `maindirectionname` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费站抓拍';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_rt_szdn_snapshot_flow_view`;
/*!50001 DROP VIEW IF EXISTS `ods_rt_szdn_snapshot_flow_view`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `ods_rt_szdn_snapshot_flow_view` AS SELECT 
 1 AS `big_id`,
 1 AS `datasource`,
 1 AS `cameratype`,
 1 AS `deviceid`,
 1 AS `gantrycode`,
 1 AS `gantryname`,
 1 AS `roadcode`,
 1 AS `roadname`,
 1 AS `sectioncode`,
 1 AS `sectionname`,
 1 AS `tollcode`,
 1 AS `tollname`,
 1 AS `orgcode`,
 1 AS `orgname`,
 1 AS `hexcode`,
 1 AS `direction`,
 1 AS `pileno`,
 1 AS `lon`,
 1 AS `lat`,
 1 AS `deviceip`,
 1 AS `siteid`,
 1 AS `laneid`,
 1 AS `snapshottimeunix`,
 1 AS `snapshottime`,
 1 AS `receivedtimeunix`,
 1 AS `receivedtime`,
 1 AS `platenumber`,
 1 AS `platecolor`,
 1 AS `platecolorcode`,
 1 AS `platetype`,
 1 AS `platetypecode`,
 1 AS `plateconfidence`,
 1 AS `carbrand`,
 1 AS `carcolor`,
 1 AS `carcolorcode`,
 1 AS `cartype`,
 1 AS `cartypecode`,
 1 AS `cardirection`,
 1 AS `snappicturepath`,
 1 AS `loadtime`,
 1 AS `gradelevel`,
 1 AS `datauuid`,
 1 AS `reserve3`*/;
SET character_set_client = @saved_cs_client;
DROP TABLE IF EXISTS `ods_szdn_gantry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_gantry` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `gantry_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架编号（分离）',
  `gantry_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架名称',
  `road_code` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路线编码',
  `section_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属路段编码',
  `toll_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属收费站编码',
  `org_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '所属管理中心机构编码',
  `hex_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架二进制编号',
  `direction` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '方向（0: 上行，1: 下行）',
  `pile_no` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `lon` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '经度',
  `lat` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '纬度',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '备注',
  `is_virtual` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否虚门架（0：否，1：是）',
  `mileage` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '里程',
  `boundary_gantry_type` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '边界门架类型（0：边界入口门架，1：边界出口门架）',
  `gantry_type` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '门架类型（0：收费门架，1：交调门架）',
  `city_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '城市编码',
  `district_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '行政区名称',
  `belong_group` varchar(4) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否属于集团，0：否；1：是',
  `gantry_code_merge` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架编号',
  `gantry_name_alias` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '门架别名',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='门架信息表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_szdn_gantry_ip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_gantry_ip` (
  `id` bigint NOT NULL COMMENT '主键',
  `gantry_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '门架编号',
  `gantry_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '门架名称',
  `org_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '机构编码',
  `ip` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设备ip',
  `brand` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '类型1是省界门架',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='省界设备ip表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_szdn_province_border_vehicle_weight_newstructure`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_province_border_vehicle_weight_newstructure` (
  `dataSource` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据来源',
  `dataType` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '数据类型',
  `plateNo` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌号',
  `siteId` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '站点ID',
  `location` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '设备地点',
  `driveNo` int DEFAULT NULL COMMENT '车道号',
  `plateColor` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色索引',
  `plateColorCode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌颜色代码',
  `plateType` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型索引',
  `plateTypeCode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌类型代码',
  `vehicleColor` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色代号',
  `vehicleColorCode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆颜色代码',
  `vehicleType` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型代号',
  `vehicleTypeCode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车辆类型代码',
  `vehicleSpeed` int DEFAULT NULL COMMENT '车辆速度（km/h）',
  `isOverweight` int DEFAULT NULL COMMENT '是否超载',
  `axleNum` int DEFAULT NULL COMMENT '轴数',
  `overWeight` int DEFAULT NULL COMMENT '超重量（KG）',
  `vehicleWeight` int DEFAULT NULL COMMENT '重量（KG）',
  `limitWeight` int DEFAULT NULL COMMENT '车辆限重（KG）',
  `checkTimeUnix` bigint DEFAULT NULL COMMENT '检测时间Unix格式',
  `checkTime` datetime DEFAULT NULL COMMENT '检测时间',
  `axleModel` int DEFAULT NULL COMMENT '轴型',
  `loadRate` double DEFAULT NULL COMMENT '超载率',
  `axleArray` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '轴型详细数据',
  `weighingImagesArry` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '图片数组',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` int DEFAULT NULL COMMENT '分类分级',
  `datauuid` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT 'datauuid',
  `reserve1` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve2` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `reserve3` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='省界称重';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_szdn_section`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_section` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `road_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路线编码',
  `road_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路线名称',
  `section_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路段编码',
  `section_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路段名称',
  `start_pile_no` double DEFAULT NULL COMMENT '起点桩号',
  `end_pile_no` double DEFAULT NULL COMMENT '终点桩号',
  `org_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '机构代码',
  `org_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '机构名称',
  `org_level_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '层级代码',
  `org_category` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '机构分类',
  `mileage` double DEFAULT NULL COMMENT '里程',
  `open_date` datetime DEFAULT NULL COMMENT '通车日期',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='路段信息表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_szdn_toll`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_toll` (
  `id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `road_code` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线编号',
  `id_card` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '收费站业务唯一编码',
  `toll_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站编号（内部）',
  `toll_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '收费站名称（内部）',
  `pile_no` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '桩号',
  `org_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '所属机构名称',
  `hex_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站HEX编码',
  `state_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '国网编号（内部）',
  `org_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '机构编码',
  `longitude` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '经度',
  `latitude` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '纬度',
  `open_date` datetime DEFAULT NULL COMMENT '开通日期',
  `toll_alias_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '收费站别名',
  `in_monitor_resource` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口治超监控资源，多个以英文逗号分割',
  `lane_monitor_resource` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '车道抓拍监控资源，多个以英文逗号分割',
  `square_monitor_resource` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '广场监控资源，多个以英文逗号分割',
  `dynamic_monitor_resource` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '动环监控资源，多个以英文逗号分割',
  `toll_code_merge` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站编号',
  `state_code_merge` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '国网编号',
  `toll_name_merge` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '收费站名称',
  `section_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '所属路段编码',
  `toll_org_code` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '收费站对应机构编码',
  `is_access` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '流水是否接入',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费站基础信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_szdn_toll_station_ip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_szdn_toll_station_ip` (
  `id` bigint NOT NULL,
  `toll_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `toll_name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `org_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `ip` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `brand` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='收费站ip表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `ods_yhgl_v_base_org`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ods_yhgl_v_base_org` (
  `big_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `org_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '机构代码',
  `org_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '机构名称',
  `org_short_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '机构简称',
  `org_parent_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上级机构ID',
  `org_level_code` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '层级代码',
  `org_is_virtual` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否虚机构1：虚机构，0：非需机构',
  `org_maintenance` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否是养护类（1：是，0否）',
  `org_sequence` int DEFAULT NULL COMMENT '机构顺序',
  `org_is_manager` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否管理单位，主要指是否是路段管理单位(1：是,0：否)',
  `org_is_deleted` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否删除1：是0：否',
  `org_category` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '机构分类01	集团02公司03管理中心10部门11所12服务区13养护区14站15项目办16信息中心17项目部99其它',
  `org_is_authorized` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否授权机构1：是0：否',
  `org_address` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '机构地址',
  `org_is_yh_autarky` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是自营养护单位',
  `load_time` datetime DEFAULT NULL COMMENT '加载时间',
  `grade_level` smallint DEFAULT NULL COMMENT '分类分级',
  PRIMARY KEY (`big_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='机构信息';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_blob_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_blob_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `blob_data` blob,
  PRIMARY KEY (`sched_name`,`trigger_name`,`trigger_group`) USING BTREE,
  CONSTRAINT `qrtz_blob_triggers_ibfk_1` FOREIGN KEY (`sched_name`, `trigger_name`, `trigger_group`) REFERENCES `qrtz_triggers` (`sched_name`, `trigger_name`, `trigger_group`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_calendars`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_calendars` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `calendar_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `calendar` blob NOT NULL,
  PRIMARY KEY (`sched_name`,`calendar_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_cron_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_cron_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `cron_expression` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `time_zone_id` varchar(80) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`sched_name`,`trigger_name`,`trigger_group`) USING BTREE,
  CONSTRAINT `qrtz_cron_triggers_ibfk_1` FOREIGN KEY (`sched_name`, `trigger_name`, `trigger_group`) REFERENCES `qrtz_triggers` (`sched_name`, `trigger_name`, `trigger_group`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_fired_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_fired_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `entry_id` varchar(95) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `instance_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `fired_time` bigint NOT NULL,
  `sched_time` bigint NOT NULL,
  `priority` int NOT NULL,
  `state` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `job_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `is_nonconcurrent` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `requests_recovery` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`sched_name`,`entry_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_job_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_job_details` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `description` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `job_class_name` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `is_durable` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `is_nonconcurrent` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `is_update_data` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `requests_recovery` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_data` blob,
  PRIMARY KEY (`sched_name`,`job_name`,`job_group`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_locks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_locks` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `lock_name` varchar(40) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`sched_name`,`lock_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_paused_trigger_grps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_paused_trigger_grps` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`sched_name`,`trigger_group`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_scheduler_state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_scheduler_state` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `instance_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `last_checkin_time` bigint NOT NULL,
  `checkin_interval` bigint NOT NULL,
  PRIMARY KEY (`sched_name`,`instance_name`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_simple_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_simple_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `repeat_count` bigint NOT NULL,
  `repeat_interval` bigint NOT NULL,
  `times_triggered` bigint NOT NULL,
  PRIMARY KEY (`sched_name`,`trigger_name`,`trigger_group`) USING BTREE,
  CONSTRAINT `qrtz_simple_triggers_ibfk_1` FOREIGN KEY (`sched_name`, `trigger_name`, `trigger_group`) REFERENCES `qrtz_triggers` (`sched_name`, `trigger_name`, `trigger_group`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_simprop_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_simprop_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `str_prop_1` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `str_prop_2` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `str_prop_3` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `int_prop_1` int DEFAULT NULL,
  `int_prop_2` int DEFAULT NULL,
  `long_prop_1` bigint DEFAULT NULL,
  `long_prop_2` bigint DEFAULT NULL,
  `dec_prop_1` decimal(13,4) DEFAULT NULL,
  `dec_prop_2` decimal(13,4) DEFAULT NULL,
  `bool_prop_1` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `bool_prop_2` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`sched_name`,`trigger_name`,`trigger_group`) USING BTREE,
  CONSTRAINT `qrtz_simprop_triggers_ibfk_1` FOREIGN KEY (`sched_name`, `trigger_name`, `trigger_group`) REFERENCES `qrtz_triggers` (`sched_name`, `trigger_name`, `trigger_group`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `qrtz_triggers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `qrtz_triggers` (
  `sched_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `job_group` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `description` varchar(250) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `next_fire_time` bigint DEFAULT NULL,
  `prev_fire_time` bigint DEFAULT NULL,
  `priority` int DEFAULT NULL,
  `trigger_state` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `trigger_type` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `start_time` bigint NOT NULL,
  `end_time` bigint DEFAULT NULL,
  `calendar_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `misfire_instr` smallint DEFAULT NULL,
  `job_data` blob,
  PRIMARY KEY (`sched_name`,`trigger_name`,`trigger_group`) USING BTREE,
  KEY `sched_name` (`sched_name`,`job_name`,`job_group`) USING BTREE,
  CONSTRAINT `qrtz_triggers_ibfk_1` FOREIGN KEY (`sched_name`, `job_name`, `job_group`) REFERENCES `qrtz_job_details` (`sched_name`, `job_name`, `job_group`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_config` (
  `config_id` int NOT NULL AUTO_INCREMENT COMMENT '参数主键',
  `config_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '参数名称',
  `config_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '参数键名',
  `config_value` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '参数键值',
  `config_type` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'N' COMMENT '系统内置（Y是 N否）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`config_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=220 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='参数配置表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dept` (
  `dept_id` bigint NOT NULL AUTO_INCREMENT COMMENT '部门id',
  `parent_id` bigint DEFAULT '0' COMMENT '父部门id',
  `ancestors` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '祖级列表',
  `dept_name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '部门名称',
  `order_num` int DEFAULT '0' COMMENT '显示顺序',
  `leader_id` bigint DEFAULT NULL COMMENT '负责人id',
  `leader` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '负责人',
  `fgld_id` bigint DEFAULT NULL COMMENT '分管领导id',
  `fgld_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '分管领导名称',
  `bank_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '开户行',
  `account` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '账号',
  `social_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '部门编码',
  `postal_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '父编码',
  `address` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '通讯地址',
  `phone` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '联系电话',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '邮箱',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '部门状态（0正常 1停用）',
  `is_zbzg` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否有招标资格(0否1是)',
  `is_uint` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '是否是单位(0否1是)',
  `tree_leavel` int DEFAULT NULL COMMENT '树级别',
  `sub_code` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '树编号',
  `dept_jc` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '简称',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位id',
  PRIMARY KEY (`dept_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=25519 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='部门表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_data` (
  `dict_code` bigint NOT NULL AUTO_INCREMENT COMMENT '字典编码',
  `dict_sort` int DEFAULT '0' COMMENT '字典排序',
  `dict_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典标签',
  `dict_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典键值',
  `dict_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典类型',
  `css_class` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '样式属性（其他样式扩展）',
  `list_class` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '表格回显样式',
  `is_default` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT 'N' COMMENT '是否默认（Y是 N否）',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常 1停用）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`dict_code`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=731 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='字典数据表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_type` (
  `dict_id` bigint NOT NULL AUTO_INCREMENT COMMENT '字典主键',
  `dict_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典名称',
  `dict_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '字典类型',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常 1停用）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`dict_id`) USING BTREE,
  UNIQUE KEY `dict_type` (`dict_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=345 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_file`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_file` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '编号',
  `file_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '文件名称',
  `bucket_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上传包名',
  `original` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '上传文件名称',
  `type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '文件类型',
  `file_size` bigint DEFAULT NULL COMMENT '文件大小',
  `buss_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务类型',
  `buss_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称',
  `create_user` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `create_time` datetime DEFAULT NULL COMMENT '上传时间',
  `update_user` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0',
  `tenant_id` bigint DEFAULT NULL COMMENT '所属租户',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `index_buss_type` (`buss_type`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=2118580249607274497 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='文件管理表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_index_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_index_menu` (
  `ID` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `USER_ID` bigint DEFAULT NULL COMMENT '用户ID',
  `MENU_ID` bigint DEFAULT NULL COMMENT '菜单ID',
  `SORT` int DEFAULT NULL COMMENT '排序',
  `EPS_ID` bigint DEFAULT NULL COMMENT '创建人所在单位或科室',
  `DEL_FLAG` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0存在 1删除）',
  `CREATE_BY` bigint DEFAULT NULL COMMENT '创建人',
  `CREATE_TIME` timestamp(3) NULL DEFAULT NULL COMMENT '创建时间',
  `UPDATE_BY` bigint DEFAULT NULL COMMENT '更新人',
  `UPDATE_TIME` timestamp(3) NULL DEFAULT NULL COMMENT '更新时间',
  `TENANT_ID` bigint DEFAULT NULL COMMENT '租户单位ID',
  PRIMARY KEY (`ID`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=91 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='用户常用菜单';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_job` (
  `job_id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `job_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '任务名称',
  `job_group` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'DEFAULT' COMMENT '任务组名',
  `invoke_target` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '调用目标字符串',
  `cron_expression` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT 'cron执行表达式',
  `misfire_policy` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '3' COMMENT '计划执行错误策略（1立即执行 2执行一次 3放弃执行）',
  `concurrent` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '是否并发执行（0允许 1禁止）',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '状态（0正常 1暂停）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '备注信息',
  PRIMARY KEY (`job_id`,`job_name`,`job_group`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=913 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='定时任务调度表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_job_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_job_log` (
  `job_log_id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务日志ID',
  `job_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称',
  `job_group` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务组名',
  `invoke_target` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '调用目标字符串',
  `job_message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '日志信息',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '执行状态（0正常 1失败）',
  `exception_info` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '异常信息',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`job_log_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1749 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='定时任务调度日志表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_logininfor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_logininfor` (
  `info_id` bigint NOT NULL AUTO_INCREMENT COMMENT '访问ID',
  `user_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '用户账号',
  `ipaddr` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '登录IP地址',
  `login_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '登录地点',
  `browser` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '浏览器类型',
  `os` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '操作系统',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '登录状态（0成功 1失败）',
  `msg` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '提示消息',
  `login_time` datetime DEFAULT NULL COMMENT '访问时间',
  PRIMARY KEY (`info_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=53303 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='系统访问记录';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_menu` (
  `menu_id` bigint NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
  `menu_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '菜单名称',
  `parent_id` bigint DEFAULT '0' COMMENT '父菜单ID',
  `order_num` int DEFAULT '0' COMMENT '显示顺序',
  `path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '路由地址',
  `component` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '组件路径',
  `is_frame` int DEFAULT '1' COMMENT '是否为外链（0是 1否）',
  `is_cache` int DEFAULT '0' COMMENT '是否缓存（0缓存 1不缓存）',
  `menu_type` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '菜单类型（M目录 C菜单 F按钮）',
  `visible` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '菜单状态（0显示 1隐藏）',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '菜单状态（0正常 1停用）',
  `perms` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限标识',
  `icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '#' COMMENT '菜单图标',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '备注',
  PRIMARY KEY (`menu_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=3155 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='菜单权限表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_notice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_notice` (
  `notice_id` int NOT NULL AUTO_INCREMENT COMMENT '公告ID',
  `notice_title` varchar(400) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `notice_type` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '公告类型（1通知 2公告）',
  `notice_content` longblob COMMENT '公告内容',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '公告状态（0正常 1关闭）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `buss_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务id',
  `buss_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称',
  `tenant_id` bigint DEFAULT NULL COMMENT '业务id',
  PRIMARY KEY (`notice_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=713 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='通知公告表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_oper_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_oper_log` (
  `oper_id` bigint NOT NULL AUTO_INCREMENT COMMENT '日志主键',
  `title` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '模块标题',
  `business_type` int DEFAULT '0' COMMENT '业务类型（0其它 1新增 2修改 3删除）',
  `method` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '方法名称',
  `request_method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '请求方式',
  `operator_type` int DEFAULT '0' COMMENT '操作类别（0其它 1后台用户 2手机端用户）',
  `oper_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '操作人员',
  `dept_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '部门名称',
  `oper_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '请求URL',
  `oper_ip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '主机地址',
  `oper_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '操作地点',
  `oper_param` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '请求参数',
  `json_result` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '返回参数',
  `status` int DEFAULT '0' COMMENT '操作状态（0正常 1异常）',
  `error_msg` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '错误消息',
  `oper_time` datetime DEFAULT NULL COMMENT '操作时间',
  PRIMARY KEY (`oper_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=90847 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='操作日志记录';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_post` (
  `post_id` bigint NOT NULL AUTO_INCREMENT COMMENT '岗位ID',
  `post_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '岗位编码',
  `post_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '岗位名称',
  `post_sort` int NOT NULL COMMENT '显示顺序',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '状态（0正常 1停用）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`post_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=158 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='岗位信息表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role` (
  `role_id` bigint NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `role_name` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名称',
  `role_key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色权限字符串',
  `role_sort` int NOT NULL COMMENT '显示顺序',
  `data_scope` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）',
  `menu_check_strictly` tinyint(1) DEFAULT '1' COMMENT '菜单树选择项是否关联显示',
  `dept_check_strictly` tinyint(1) DEFAULT '1' COMMENT '部门树选择项是否关联显示',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色状态（0正常 1停用）',
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`role_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=990145 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='角色信息表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_role_dept`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role_dept` (
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `dept_id` bigint NOT NULL COMMENT '部门ID',
  PRIMARY KEY (`role_id`,`dept_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='角色和部门关联表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_role_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_role_menu` (
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_id`,`menu_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='角色和菜单关联表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `user_id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `user_no` bigint DEFAULT NULL COMMENT '用户编码',
  `dept_id` bigint DEFAULT NULL COMMENT '部门ID',
  `user_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户账号',
  `nick_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户昵称',
  `user_type` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '1' COMMENT '用户类型（1机构用户2专家3供应商）',
  `email` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '用户邮箱',
  `phonenumber` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '手机号码',
  `sex` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '用户性别（0男 1女 2未知）',
  `avatar` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '头像地址',
  `password` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '密码',
  `status` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '帐号状态（0正常 1停用）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '备注',
  `cert_entity_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '实体id',
  `cert_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '证书id(密码卡_USB)',
  `buss_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务id',
  `buss_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '业务名称',
  `eps_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '单位名称',
  `login_ip` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '最后登录IP',
  `login_date` datetime DEFAULT NULL COMMENT '最后登录时间',
  `image_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `del_flag` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  `create_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `tenant_id` bigint DEFAULT NULL COMMENT '租户单位id',
  PRIMARY KEY (`user_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=990200 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='用户信息表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_user_post`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_post` (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `post_id` bigint NOT NULL COMMENT '岗位ID',
  PRIMARY KEY (`user_id`,`post_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='用户与岗位关联表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `sys_user_role`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_role` (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_id`,`role_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='用户和角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `t_disaster_threshold`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `t_disaster_threshold` (
  `id` int NOT NULL AUTO_INCREMENT,
  `province` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '省份',
  `city` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '地市',
  `county` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '区县',
  `road_code` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线编号',
  `road_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路线名称',
  `org_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路段管理单位编号',
  `org_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路段管理单位名称',
  `impact_level` char(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '影响等级(0: 有影响, 1: 影响较大, 2: 影响严重)',
  `section_num` int DEFAULT NULL COMMENT '路段序号',
  `start_pile_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '起点桩号',
  `end_pile_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终点桩号',
  `section_state` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '路段情况',
  `f_twenty_four` decimal(10,2) DEFAULT NULL COMMENT 'F24',
  `f_three` decimal(10,2) DEFAULT NULL COMMENT 'F3',
  `g_twenty_four` decimal(10,2) DEFAULT NULL COMMENT 'G24',
  `g_three` decimal(10,2) DEFAULT NULL COMMENT 'G3',
  `t_twenty_four` decimal(10,2) DEFAULT NULL COMMENT 'T24',
  `t_three` decimal(10,2) DEFAULT NULL COMMENT 'T3',
  `linestring` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '路径',
  `creator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建人',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `updator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '更新人',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `maintain_station` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管养站及站长联系方式',
  `maintain_director` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '管养所及所长联系方式',
  `engineer_manager` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '工程部经理联系方式',
  `vice_president` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '分管副总及联系方式',
  `general_manager` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '总经理及联系方式',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1209 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='高速公路灾害天气（汛期）路段分级分类管控阈值表';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `zdata_location_dict`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zdata_location_dict` (
  `id` int NOT NULL,
  `type` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `raw_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `standard_code` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `roadcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `roadname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sectioncode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `sectionname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tollcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tollname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `orgcode` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `orgname` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `latitude` decimal(20,17) DEFAULT NULL,
  `longitude` decimal(20,17) DEFAULT NULL,
  `pile_no_k` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pile_no` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `remark` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `direction` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `zdata_trail_fitting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zdata_trail_fitting` (
  `cid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '轨迹唯一标识（cid）',
  `enaxlecount` smallint DEFAULT NULL COMMENT '入口车轴数',
  `entime` datetime DEFAULT NULL COMMENT '入口时间',
  `entolllaneid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口车道编号',
  `entollstationid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口收费站编号',
  `entollstationname` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口收费站名称',
  `envehicleclass` smallint DEFAULT NULL COMMENT '入口车型分类（收费车型）',
  `envehicleid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '入口车辆编号',
  `envehicletype` smallint DEFAULT NULL COMMENT '入口车辆类型代码',
  `enweight` int DEFAULT NULL COMMENT '入口称重（kg）',
  `extime` datetime DEFAULT NULL COMMENT '出口时间（分区键）',
  `extolllaneid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口车道编号',
  `extollstationid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口收费站编号',
  `extollstationname` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口收费站名称',
  `exvehicleclass` smallint DEFAULT NULL COMMENT '出口车型分类（收费车型）',
  `exvehicleid` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '出口车辆编号',
  `exvehicletype` smallint DEFAULT NULL COMMENT '出口车辆类型代码',
  `exweight` int DEFAULT NULL COMMENT '出口称重（kg）',
  `trailpoints` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '拟合轨迹点集合',
  PRIMARY KEY (`cid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='车辆出入口拟合轨迹表（日分区，按 extime 分区）';
/*!40101 SET character_set_client = @saved_cs_client */;
DROP TABLE IF EXISTS `zdata_trail_tracks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `zdata_trail_tracks` (
  `uuid` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '唯一标识符（分布键，用于保证轨迹全局唯一）',
  `type` smallint DEFAULT NULL COMMENT '轨迹类型（如 0=不完整, 1=完整，后续可扩展更多状态码）',
  `point_count` int DEFAULT NULL COMMENT '轨迹点数量（记录该轨迹包含多少个点）',
  `plate_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '车牌唯一标识（可脱敏/加密存储，用于车辆关联）',
  `enter_time` datetime DEFAULT NULL COMMENT '进入时间（分区键，月度分区粒度）',
  `exit_time` datetime DEFAULT NULL COMMENT '离开时间（轨迹结束时间）',
  `trail_points` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '轨迹点集合，推荐存 JSON 格式，包含坐标/时间/速度等信息',
  `create_time` datetime DEFAULT NULL COMMENT '记录创建时间（默认 NOW()，用于数据入库追踪）',
  `enter_locationcode` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '进入位置code',
  `exit_locationcode` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '离开位置code',
  `track_josn` mediumtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '集合详情',
  `enaxlecount` int DEFAULT NULL COMMENT '入口车轴数',
  `entolllaneid` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车道编号',
  `entollstationid` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口收费站编号',
  `entollstationname` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口收费站名称',
  `envehicleclass` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车型分类（收费车型）',
  `envehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车辆编号',
  `envehicletype` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口车辆类型代码',
  `enweight` decimal(19,2) DEFAULT NULL COMMENT '入口称重（kg）',
  `extolllaneid` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车道编号',
  `extollstationid` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口收费站编号',
  `extollstationname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口收费站名称',
  `exvehicleclass` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车型分类',
  `exvehicleid` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车辆编号',
  `exvehicletype` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口车辆类型代码',
  `exweight` decimal(19,2) DEFAULT NULL COMMENT '出口称重（kg）',
  `start_lon` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '起点信息',
  `strat_lat` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '入口收费站维度',
  `end_lon` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '终点信息',
  `end_lat` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '出口收费站维度',
  KEY `trail_tracks_plate_key` (`plate_key`) USING BTREE,
  KEY `trail_tracks_enter_time` (`enter_time`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=DYNAMIC COMMENT='轨迹数据表（分区父表，按 enter_time 月度分区，uuid 哈希分布）';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!50001 DROP VIEW IF EXISTS `ods_rt_szdn_snapshot_flow_view`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_unicode_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `ods_rt_szdn_snapshot_flow_view` AS select `ods_rt_szdn_snapshot_flow_addcode`.`big_id` AS `big_id`,`ods_rt_szdn_snapshot_flow_addcode`.`datasource` AS `datasource`,`ods_rt_szdn_snapshot_flow_addcode`.`cameratype` AS `cameratype`,`ods_rt_szdn_snapshot_flow_addcode`.`deviceid` AS `deviceid`,`ods_rt_szdn_snapshot_flow_addcode`.`gantrycode` AS `gantrycode`,`ods_rt_szdn_snapshot_flow_addcode`.`gantryname` AS `gantryname`,`ods_rt_szdn_snapshot_flow_addcode`.`roadcode` AS `roadcode`,`ods_rt_szdn_snapshot_flow_addcode`.`roadname` AS `roadname`,`ods_rt_szdn_snapshot_flow_addcode`.`sectioncode` AS `sectioncode`,`ods_rt_szdn_snapshot_flow_addcode`.`sectionname` AS `sectionname`,`ods_rt_szdn_snapshot_flow_addcode`.`tollcode` AS `tollcode`,`ods_rt_szdn_snapshot_flow_addcode`.`tollname` AS `tollname`,`ods_rt_szdn_snapshot_flow_addcode`.`orgcode` AS `orgcode`,`ods_rt_szdn_snapshot_flow_addcode`.`orgname` AS `orgname`,`ods_rt_szdn_snapshot_flow_addcode`.`hexcode` AS `hexcode`,`ods_rt_szdn_snapshot_flow_addcode`.`direction` AS `direction`,`ods_rt_szdn_snapshot_flow_addcode`.`pileno` AS `pileno`,`ods_rt_szdn_snapshot_flow_addcode`.`lon` AS `lon`,`ods_rt_szdn_snapshot_flow_addcode`.`lat` AS `lat`,`ods_rt_szdn_snapshot_flow_addcode`.`deviceip` AS `deviceip`,`ods_rt_szdn_snapshot_flow_addcode`.`siteid` AS `siteid`,`ods_rt_szdn_snapshot_flow_addcode`.`laneid` AS `laneid`,`ods_rt_szdn_snapshot_flow_addcode`.`snapshottimeunix` AS `snapshottimeunix`,`ods_rt_szdn_snapshot_flow_addcode`.`snapshottime` AS `snapshottime`,`ods_rt_szdn_snapshot_flow_addcode`.`receivedtimeunix` AS `receivedtimeunix`,`ods_rt_szdn_snapshot_flow_addcode`.`receivedtime` AS `receivedtime`,`ods_rt_szdn_snapshot_flow_addcode`.`platenumber` AS `platenumber`,`ods_rt_szdn_snapshot_flow_addcode`.`platecolor` AS `platecolor`,`ods_rt_szdn_snapshot_flow_addcode`.`platecolorcode` AS `platecolorcode`,`ods_rt_szdn_snapshot_flow_addcode`.`platetype` AS `platetype`,`ods_rt_szdn_snapshot_flow_addcode`.`platetypecode` AS `platetypecode`,`ods_rt_szdn_snapshot_flow_addcode`.`plateconfidence` AS `plateconfidence`,`ods_rt_szdn_snapshot_flow_addcode`.`carbrand` AS `carbrand`,`ods_rt_szdn_snapshot_flow_addcode`.`carcolor` AS `carcolor`,`ods_rt_szdn_snapshot_flow_addcode`.`carcolorcode` AS `carcolorcode`,`ods_rt_szdn_snapshot_flow_addcode`.`cartype` AS `cartype`,`ods_rt_szdn_snapshot_flow_addcode`.`cartypecode` AS `cartypecode`,`ods_rt_szdn_snapshot_flow_addcode`.`cardirection` AS `cardirection`,`ods_rt_szdn_snapshot_flow_addcode`.`snappicturepath` AS `snappicturepath`,`ods_rt_szdn_snapshot_flow_addcode`.`loadtime` AS `loadtime`,`ods_rt_szdn_snapshot_flow_addcode`.`gradelevel` AS `gradelevel`,`ods_rt_szdn_snapshot_flow_addcode`.`datauuid` AS `datauuid`,`ods_rt_szdn_snapshot_flow_addcode`.`reserve3` AS `reserve3` from `ods_rt_szdn_snapshot_flow_addcode` union all select `ods_rt_szdn_snapshot_flow_202508`.`big_id` AS `big_id`,`ods_rt_szdn_snapshot_flow_202508`.`datasource` AS `datasource`,`ods_rt_szdn_snapshot_flow_202508`.`cameratype` AS `cameratype`,`ods_rt_szdn_snapshot_flow_202508`.`deviceid` AS `deviceid`,`ods_rt_szdn_snapshot_flow_202508`.`gantrycode` AS `gantrycode`,`ods_rt_szdn_snapshot_flow_202508`.`gantryname` AS `gantryname`,`ods_rt_szdn_snapshot_flow_202508`.`roadcode` AS `roadcode`,`ods_rt_szdn_snapshot_flow_202508`.`roadname` AS `roadname`,`ods_rt_szdn_snapshot_flow_202508`.`sectioncode` AS `sectioncode`,`ods_rt_szdn_snapshot_flow_202508`.`sectionname` AS `sectionname`,`ods_rt_szdn_snapshot_flow_202508`.`tollcode` AS `tollcode`,`ods_rt_szdn_snapshot_flow_202508`.`tollname` AS `tollname`,`ods_rt_szdn_snapshot_flow_202508`.`orgcode` AS `orgcode`,`ods_rt_szdn_snapshot_flow_202508`.`orgname` AS `orgname`,`ods_rt_szdn_snapshot_flow_202508`.`hexcode` AS `hexcode`,`ods_rt_szdn_snapshot_flow_202508`.`direction` AS `direction`,`ods_rt_szdn_snapshot_flow_202508`.`pileno` AS `pileno`,`ods_rt_szdn_snapshot_flow_202508`.`lon` AS `lon`,`ods_rt_szdn_snapshot_flow_202508`.`lat` AS `lat`,`ods_rt_szdn_snapshot_flow_202508`.`deviceip` AS `deviceip`,`ods_rt_szdn_snapshot_flow_202508`.`siteid` AS `siteid`,`ods_rt_szdn_snapshot_flow_202508`.`laneid` AS `laneid`,`ods_rt_szdn_snapshot_flow_202508`.`snapshottimeunix` AS `snapshottimeunix`,`ods_rt_szdn_snapshot_flow_202508`.`snapshottime` AS `snapshottime`,`ods_rt_szdn_snapshot_flow_202508`.`receivedtimeunix` AS `receivedtimeunix`,`ods_rt_szdn_snapshot_flow_202508`.`receivedtime` AS `receivedtime`,`ods_rt_szdn_snapshot_flow_202508`.`platenumber` AS `platenumber`,`ods_rt_szdn_snapshot_flow_202508`.`platecolor` AS `platecolor`,`ods_rt_szdn_snapshot_flow_202508`.`platecolorcode` AS `platecolorcode`,`ods_rt_szdn_snapshot_flow_202508`.`platetype` AS `platetype`,`ods_rt_szdn_snapshot_flow_202508`.`platetypecode` AS `platetypecode`,`ods_rt_szdn_snapshot_flow_202508`.`plateconfidence` AS `plateconfidence`,`ods_rt_szdn_snapshot_flow_202508`.`carbrand` AS `carbrand`,`ods_rt_szdn_snapshot_flow_202508`.`carcolor` AS `carcolor`,`ods_rt_szdn_snapshot_flow_202508`.`carcolorcode` AS `carcolorcode`,`ods_rt_szdn_snapshot_flow_202508`.`cartype` AS `cartype`,`ods_rt_szdn_snapshot_flow_202508`.`cartypecode` AS `cartypecode`,`ods_rt_szdn_snapshot_flow_202508`.`cardirection` AS `cardirection`,`ods_rt_szdn_snapshot_flow_202508`.`snappicturepath` AS `snappicturepath`,`ods_rt_szdn_snapshot_flow_202508`.`loadtime` AS `loadtime`,`ods_rt_szdn_snapshot_flow_202508`.`gradelevel` AS `gradelevel`,`ods_rt_szdn_snapshot_flow_202508`.`datauuid` AS `datauuid`,`ods_rt_szdn_snapshot_flow_202508`.`reserve3` AS `reserve3` from `ods_rt_szdn_snapshot_flow_202508` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

