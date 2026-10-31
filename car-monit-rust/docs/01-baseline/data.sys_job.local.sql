
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

LOCK TABLES `sys_job` WRITE;
/*!40000 ALTER TABLE `sys_job` DISABLE KEYS */;
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (1,'系统默认（无参）','DEFAULT','ryTask.ryNoParams','0/10 * * * * ?','3','1','1','admin','2021-05-06 00:36:44','admin','2024-05-20 14:29:15','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (2,'系统默认（有参）','DEFAULT','ryTask.ryParams(\'ry\')','0/15 * * * * ?','3','1','1','admin','2021-05-06 00:36:44','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (3,'系统默认（多参）','DEFAULT','ryTask.ryMultipleParams(\'ry\', true, 2000L, 316.50D, 100)','0/20 * * * * ?','3','1','1','admin','2021-05-06 00:36:44','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (103,'同步收费所','DEFAULT','vehicleMonitoringTask.syncTollBoothInfoInfo','0 30 0 * * ?','1','1','1','admin','2025-08-29 16:15:46','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (104,'同步机构','DEFAULT','vehicleMonitoringTask.syncOrgInfo','0 40 0 * * ?','1','1','1','admin','2025-09-01 09:57:23','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (105,'同步收费站','DEFAULT','vehicleMonitoringTask.syncTollStationInfo','0 50 0 * * ?','1','1','1','admin','2025-09-01 10:01:11','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (106,'同步门架','DEFAULT','vehicleMonitoringTask.syncGantryInfo','0 0 1 * * ?','1','1','1','admin','2025-09-01 11:10:54','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (107,'同步收费所','DEFAULT','vehicleMonitoringTask.syncTollBoothInfoInfo','0 10 1 * * ?','1','1','1','admin','2025-09-01 11:14:01','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (108,'同步收费站位置','DEFAULT','vehicleMonitoringTask.syncSfzjcxxInfoInfo','0 20 1 * * ?','1','1','1','admin','2025-09-01 11:15:54','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (109,'同步服务区','DEFAULT','vehicleMonitoringTask.syncServiceAreaInfoInfo','0 30 1 * * ?','1','1','1','admin','2025-09-01 11:22:34','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (110,'同步机构到本地','DEFAULT','orgTask.syncOrgInfo','0 0 3 * * ?','1','1','1','admin','2025-09-02 14:07:59','admin','2025-10-04 10:04:09','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (111,'同步路段','DEFAULT','vehicleMonitoringTask.syncSectionInfo','0 40 1 * * ?','1','1','1','admin','2025-09-03 10:35:35','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (112,'车俩实时轨迹同步','SYSTEM','trackTask.syncCurrentTrack','0 0/3 * * * ?','1','1','1','admin','2025-09-18 11:40:54','admin','2025-12-02 11:22:01','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (113,'可疑车俩数据同步','SYSTEM','trackTask.syncSuspiciousCar','0 0 5 * * ?','1','1','1','admin','2025-09-19 15:49:00','admin','2025-11-05 10:22:56','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (114,'车辆历史轨迹同步','SYSTEM','trackTask.syncHistoryTrack','0 0 6 * * ?','1','1','1','admin','2025-10-04 17:59:27','admin','2025-11-05 10:22:58','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (115,'车辆历史轨迹（无记录）','SYSTEM','trackTask.syncHistoryTrackNoCar','0 0/10 * * * ?','1','1','1','admin','2025-10-24 17:50:50','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (116,'车辆逃费数据更新','SYSTEM','trackTask.saveCarExcept','0 0 7 * * ?','2','1','1','admin','2025-12-30 13:42:39','admin','2025-12-30 14:43:21','');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (117,'可疑车辆迁移','SYSTEM','trackTask.changeCarSuspicious',' 0 0 21 * * ?','1','1','1','admin','2026-02-05 15:44:55','',NULL,'');
INSERT INTO `sys_job` (`job_id`, `job_name`, `job_group`, `invoke_target`, `cron_expression`, `misfire_policy`, `concurrent`, `status`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) VALUES (130,'__probe__','DEFAULT','ryTask.ryNoParams','0 0 2 * * ?','3','1','1','admin','2026-10-29 11:09:44','',NULL,'');
/*!40000 ALTER TABLE `sys_job` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

