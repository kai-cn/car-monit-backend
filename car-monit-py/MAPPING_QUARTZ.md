# MAPPING_QUARTZ.md — 定时任务（`ruoyi-quartz`）Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §42 / §43。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectJobList` → `select_job_list`。
- **`sys_job.invoke_target` 里存的是 Java 方法名**（`ryTask.ryNoParams`），
  Python 的方法名是 `ry_no_params` —— 唯一的桥在
  `app/quartz/util/job_invoke_util.py::_declared_method`（`COMPATIBILITY.md` §42.5）。
- **本切片是最后一个控制器切片**：`ruoyi-admin` 的 75 个控制器 + `ruoyi-quartz` 的 2 个，
  一共 **77** 个，全部有对应物。
- 下面 §2 的路径列写的是 **Java 的 URI 模板**；Python 侧路径变量按 PEP8 改成 snake_case
  （`{jobId}` → `{job_id}`、`{jobLogIds}` → `{job_log_ids}`），路由匹配结果不受影响。

---

## 1. 文件级对照

### 1.1 逐文件（Java 25 个 → Python 21 个模块）

| Java（`ruoyi-quartz/src/main/java/com/ruoyi/quartz/`） | Python | 说明 |
|---|---|---|
| `config/ScheduleConfig.java` | `app/quartz/config/schedule_config.py` | **Java 原文 58 行全被 `//` 注释**；这里只做存档（`CLUSTERED_SCHEDULER_PROPERTIES` + `SCHEDULER_FACTORY_SETTINGS`），无运行期行为 |
| `controller/SysJobController.java` | `app/api/monitor/sys_job_controller.py` | 8 映射；注意路径是 `/monitor/job`（在 **monitor** 下，不在 quartz 下） |
| `controller/SysJobLogController.java` | `app/api/monitor/sys_job_log_controller.py` | 5 映射；`getInfo` **恒定 500**（Java 的路径变量名对不上） |
| `domain/SysJob.java` | `app/quartz/domain/sys_job.py` | `extends BaseEntity`；`nextValidTime` 是**只读计算属性**（`@computed_field`） |
| `domain/SysJobLog.java` | `app/quartz/domain/sys_job_log.py` | `extends BaseEntity`；`startTime` / `stopTime` 恒 `null` |
| `mapper/SysJobMapper.java` + `resources/mapper/quartz/SysJobMapper.xml` | `app/quartz/mapper/sys_job_mapper.py` | 7 个 statement，见 §4 |
| `mapper/SysJobLogMapper.java` + `resources/mapper/quartz/SysJobLogMapper.xml` | `app/quartz/mapper/sys_job_log_mapper.py` | 7 个 statement |
| `service/ISysJobService.java` + `service/impl/SysJobServiceImpl.java` | `app/quartz/service/sys_job_service.py` | 接口 + 实现合成一个类；单例由 `get_job_service()` / `reset_job_service()` 管 |
| `service/ISysJobLogService.java` + `service/impl/SysJobLogServiceImpl.java` | `app/quartz/service/sys_job_log_service.py` | `BEAN_NAME = "ISysJobLogService"`（Java 接口简单名），`AbstractQuartzJob` 按它取 Bean |
| `task/RyTask.java` | `app/quartz/task/ry_task.py` | `@Component("ryTask")`；四个方法全是空壳（只 `print`） |
| `task/OrgTask.java` | `app/quartz/task/org_task.py` | `@Component("orgTask")` |
| `task/TrackTask.java` | `app/quartz/task/track_task.py` | `@Component("trackTask")` |
| `task/VehicleMonitoringTask.java` | `app/quartz/task/vehicle_monitoring_task.py` | `@Component("vehicleMonitoringTask")` |
| `task/PartitionMaintenanceTask.java` | `app/quartz/task/partition_maintenance_task.py` | `@Component("partitionMaintenanceTask")`；用 `JdbcTemplate` 执行 DDL |
| `task/SnapshotFlowSyncTask.java` | `app/quartz/task/snapshot_flow_sync_task.py` | 裸 `@Component` → Bean 名 `snapshotFlowSyncTask`；**Java 里就是空转的**（§42.4）|
| `util/AbstractQuartzJob.java` | `app/quartz/util/abstract_quartz_job.py` | `execute` / `before` / `after` / `doExecute` 四段，顺序即语义 |
| `util/QuartzJobExecution.java` | `app/quartz/util/quartz_job_execution.py` | `concurrent == "0"` 时用（允许并发） |
| `util/QuartzDisallowConcurrentExecution.java` | `app/quartz/util/quartz_disallow_concurrent_execution.py` | 其余情况；per-job 锁在调度器里 |
| `util/JobInvokeUtil.java` | `app/quartz/util/job_invoke_util.py` | 反射调用；`getDeclaredMethod` → `_declared_method` |
| `util/ScheduleUtils.java` | `app/quartz/util/schedule_utils.py` | `getJobKey` / `getTriggerKey` / `createScheduleJob` / `handleCronScheduleMisfirePolicy` |
| `util/CronUtils.java` | `app/quartz/util/cron_utils.py` | 只有 3 个静态方法，真正的解析在 §1.2 的 `cron_expression.py` |

### 1.2 新增：Java 侧是**第三方库**，本工程没有源码

| Java（第三方） | Python | 说明 |
|---|---|---|
| `org.quartz.*`（`quartz:2.3.2`） | `app/quartz/util/scheduler.py` | 本工程真正用到的 **12 个 API** 的内存实现（`JobKey` / `TriggerKey` / `checkExists` / `deleteJob` / `scheduleJob` / `pauseJob` / `resumeJob` / `triggerJob` / `clear` / `JobDataMap` / `JobExecutionContext` / `SchedulerException`） |
| `org.quartz.CronExpression` | `app/quartz/util/cron_expression.py` | Quartz 2.3.2 的 `CronExpression` 逐行转写（含 `StringTokenizer` 分词、`Calendar.set` lenient 等 6 条怪癖） |

**没有引 APScheduler**：换库会让 `Key.toString()`（`group.name`）、"删不存在的任务不报错"、
`SchedulerException` 文案、cron 方言这四类**可观察行为**漂移。理由与逐条对照见
`COMPATIBILITY.md` §12 / §42.1。

### 1.3 被改动的已有文件（只有一处）

| 文件 | 改动 | 原因 |
|---|---|---|
| `app/main.py` | `import app.quartz.task`（模块导入期副作用：注册 6 个任务 Bean）+ `lifespan` 里的 `_init_quartz` / `_shutdown_quartz` + 两条 `include_router` | 对应 `@ComponentScan` 扫到 `com.ruoyi.quartz.task` 与 `@PostConstruct init()` |

`app/api/monitor/` 与 `app/quartz/` 下新建的 `__init__.py` 只是包标记
（`app/quartz/__init__.py` 除外，它写明了模块划分）。

### 1.4 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_quartz_controllers.py` | **58** | 13 条路由表、权限点、`@Log` 的 `title`/`businessType`、`AjaxResult` 的"null 不给 `data` 键"、`/{id}` 兜住 `export`、`abc` 的 `[Ljava.lang.Long;` 文案 |
| cron + 装配 | `tests/test_quartz_cron_and_schedule.py` | **101** | `CronExpression` 方言与边界（`*/0` / `?` / `L` / `W` / `#` / 6-7 段）、`CronUtils`、`ScheduleUtils` 的 key 拼接、`JobInvokeUtil` 的类型判定顺序与 `NoSuchMethodException` 文案 |
| Service | `tests/test_quartz_services.py` | **42** | 事务边界（open/commit/rollback 计数）、`insertJob` 强制 `status="1"`、misfire 非法时回滚且不留调度器条目、`changeStatus` 只认 `"0"`/`"1"`、批量删除首个缺失即中断、`init()` 先 `clear` 后重建 |
| 任务 | `tests/test_quartz_tasks.py` | **80** | 6 个 Bean 的注册名与"无基类"前提、`execute` 成功/失败两条路径（含 2000 字截断）、每个任务的协作对象调用顺序、分表的月边界 |

合计 **281** 条。全量套件 **3400 passed**（Phase 3.23 当时的数字；当前全量为 **3591**，见 `MIGRATION_PROGRESS.md` §6.8）。

---

## 2. 控制器：13 个映射，全部迁移

### 2.1 `/monitor/job`（`SysJobController`，8 个）

| Java | Python | Method / Path | 权限点 | `@Log` |
|---|---|---|---|---|
| `list(SysJob)` | `list` | GET `/monitor/job/list` | `monitor:job:list` | — |
| `export(SysJob)` | `export` | GET `/monitor/job/export` | `monitor:job:export` | `EXPORT` |
| `getInfo(Long)` | `get_info` | GET `/monitor/job/{jobId}` | `monitor:job:query` | — |
| `add(SysJob)` | `add` | POST `/monitor/job` | `monitor:job:add` | `INSERT` |
| `edit(SysJob)` | `edit` | PUT `/monitor/job` | `monitor:job:edit` | `UPDATE` |
| `changeStatus(SysJob)` | `change_status` | PUT `/monitor/job/changeStatus` | `monitor:job:changeStatus` | `UPDATE` |
| `run(SysJob)` | `run` | PUT `/monitor/job/run` | **`monitor:job:changeStatus`** | `UPDATE` |
| `remove(Long[])` | `remove` | DELETE `/monitor/job/{jobIds}` | `monitor:job:remove` | `DELETE` |

### 2.2 `/monitor/jobLog`（`SysJobLogController`，5 个）

| Java | Python | Method / Path | 权限点 | `@Log`（`title`）|
|---|---|---|---|---|
| `list(SysJobLog)` | `list` | GET `/monitor/jobLog/list` | `monitor:job:list` | — |
| `export(SysJobLog)` | `export` | GET `/monitor/jobLog/export` | `monitor:job:export` | `EXPORT`（任务调度日志）|
| `getInfo(Long)` | `get_info` | GET `/monitor/jobLog/{configId}` | `monitor:job:query` | — |
| `remove(Long[])` | `remove` | DELETE `/monitor/jobLog/{jobLogIds}` | `monitor:job:remove` | `DELETE`（定时任务调度日志）|
| `clean()` | `clean` | DELETE `/monitor/jobLog/clean` | `monitor:job:remove` | `CLEAN`（调度日志）|

三个 `title` 各不相同，**不是复制粘贴漏改**：Java 原文就是
「任务调度日志」（导出）/「定时任务调度日志」（删除）/「调度日志」（清空）。

### 2.3 四个"看起来像 bug、但必须照抄"的点

1. **`run` 用 `changeStatus` 的权限点**。Java 里压根没有 `monitor:job:run` 这个串。
2. **`GET /{jobId}` 查不到时没有 `data` 键**：`AjaxResult.success(Object)` 里
   `if (StringUtils.isNotNull(data))` 成立才放 `data`，所以响应是
   `{"code":200,"msg":"操作成功"}`。
3. **`GET /jobLog/{configId}` 永远 500**：`@PathVariable Long jobLogId` 没写名字，
   URI 模板却只有 `configId` → `MissingPathVariableException`。
   `jobLogService.selectJobLogById(...)` 因此**永远走不到**（方法本身照搬保留）。
4. **`DELETE /jobLog/clean` 必须排在 `/{jobLogIds}` 之前**：FastAPI 按注册顺序匹配，
   而 `/{job_log_ids}` 会把 `"clean"` 当成 id 再在 `int()` 处报错。Java 靠
   `AntPathMatcher` 的"字面量优先"规则，两种机制结果一致。

---

## 3. 领域对象

| Java 字段 | Python 字段 | 要点 |
|---|---|---|
| `Long jobId` | `job_id: Optional[int]` | 主键，`insertJob` 回写（`useGeneratedKeys`） |
| `String jobName` / `jobGroup` | `job_name` / `job_group` | `@Excel` 列；`jobGroup` 为 `null` 时调度器用 `DEFAULT` |
| `String invokeTarget` | `invoke_target` | 形如 `ryTask.ryNoParams()`；**存的是 Java 方法名** |
| `String cronExpression` | `cron_expression` | Quartz 方言；空串时 `nextValidTime` 为 `null` |
| `String misfirePolicy` | `misfire_policy` | **默认 `"0"`**（`ScheduleConstants.MISFIRE_DEFAULT`） |
| `String concurrent` | `concurrent` | `"0"` = 允许并发，其余 = 串行 |
| `String status` | `status` | `"0"` 正常 / `"1"` 暂停；`insertJob` **强制写 `"1"`** |
| `Date nextValidTime`（只有 getter） | `next_valid_time`（`@computed_field`） | 每次序列化按当前时间重算，永远在 JSON 最后一个键 |

`SysJobLog` 的两个坑：

- `startTime` / `stopTime` **永远是 `null`** —— `resultMap` 里没有这两列，
  `selectJobLogVo` 也没查；`insertJobLog` 同样不写。
- `status` 是 **`String`**（`char(1)`），与 `SysOperLog.status`（`Integer`）不同。

`@NotBlank` / `@Size` 挂在 getter 上、控制器又没有 `@Validated`，所以**一条都不生效**：
Python 侧因此**不加** pydantic 约束（否则会凭空多出 Java 没有的 400/500）。

---

## 4. Mapper 语句（14 个）

| `SysJobMapper.xml` | Python |
|---|---|
| `selectJobList` | `select_job_list(job, session=None)` |
| `selectJobAll` | `select_job_all(session=None)` |
| `selectJobById` | `select_job_by_id(job_id, session=None)` |
| `insertJob` | `insert_job(job, session=None)` |
| `updateJob` | `update_job(job, session=None)` |
| `deleteJobById` | `delete_job_by_id(job_id, session=None)` |
| `deleteJobByIds` | `delete_job_by_ids(job_ids, session=None)` |

| `SysJobLogMapper.xml` | Python |
|---|---|
| `selectJobLogList` | `select_job_log_list(...)` |
| `selectJobLogAll` | `select_job_log_all(session=None)` |
| `selectJobLogById` | `select_job_log_by_id(...)` |
| `insertJobLog` | `insert_job_log(job_log, session=None)` |
| `deleteJobLogById` | `delete_job_log_by_id(job_log_id, session=None)` |
| `deleteJobLogByIds` | `delete_job_log_by_ids(...)` |
| `cleanJobLog` | `clean_job_log(session=None)` |

两个"动态 SQL 助手"是 Python 独有的（MyBatis 用 OGNL，这里用函数拼片段）：
`text_like(attribute)` 等价 `<if test="x != null and x != ''">`，
`text_equals(attribute)` 等价 `<if test="x != null">`。
**片段不带前导 `AND`**（与全仓其它 mapper 的约定一致）。

`cleanJobLog` 是 `truncate table sys_job_log` —— **DDL、隐式提交、不可回滚**，
接口 `AjaxResult.success()` 不看影响行数。

---

## 5. Service

| `SysJobServiceImpl` | Python（`app/quartz/service/sys_job_service.py`） | 要点 |
|---|---|---|
| `@PostConstruct init()` | `init()` | `scheduler.clear()` + 逐条 `createScheduleJob`；`status='1'` 的会被 `pause_job` |
| `selectJobList` / `selectJobById` | `select_job_list` / `select_job_by_id` | 直接转发 |
| `@Transactional insertJob` | `insert_job` | **强制 `status="1"`**；`createScheduleJob` 抛错则整笔回滚（`with session_scope()`） |
| `@Transactional updateJob` | `update_job` | 先 `updateSchedulerJob(job, 旧 group)` 再落库 |
| `@Transactional deleteJob` | `delete_job` | `deleteJob(null)` 是 NPE（Java 原样） |
| `@Transactional deleteJobByIds` | `delete_job_by_ids` | 逐条，**第一个查不到就中断** |
| `@Transactional pauseJob` / `resumeJob` | `pause_job` / `resume_job` | 只动调度器，不碰库 |
| `@Transactional changeStatus` | `change_status` | 只认 `"0"` / `"1"`，其它值**一个 mapper 都不调**、返回 0 |
| `@Transactional run` | `run` | key 用**参数里**的 `job_group`，`TASK_PROPERTIES` 用**库里那行**（可能是 `None`） |
| `updateSchedulerJob(job, jobGroup)` | `update_scheduler_job` | `check_exists` → `delete_job` → `create_schedule_job`（后者会**再 check 一次**） |

| `SysJobLogServiceImpl` | Python（`sys_job_log_service.py`） |
|---|---|
| `selectJobLogList` / `selectJobLogAll` / `selectJobLogById` | `select_job_log_list` / `select_job_log_all` / `select_job_log_by_id` |
| `insertJobLog` / `deleteJobLogById` / `deleteJobLogByIds` / `cleanJobLog` | `insert_job_log` / `delete_job_log_by_id` / `delete_job_log_by_ids` / `clean_job_log` |

`ISysJobLogService` 这个 **Bean 名**必须存在：`AbstractQuartzJob#after` 按类型取它
（`SpringUtils.getBean(ISysJobLogService.class)`），`get_job_log_service()` 会把自己
注册进 `SpringUtils` 的注册表。

---

## 6. 六个任务 Bean（`@Component` 名 = `invoke_target` 的第一段）

| Bean 名 | Java | Python | 可直接调用的方法 |
|---|---|---|---|
| `ryTask` | `RyTask` | `app/quartz/task/ry_task.py` | `ryNoParams` / `ryParams` / `ryMultipleParams` / `autoBuildGoodsHb` |
| `orgTask` | `OrgTask` | `org_task.py` | `syncOrg` 等 |
| `trackTask` | `TrackTask` | `track_task.py` | `syncHistoryTrack` / `syncSuspiciousCar` … |
| `vehicleMonitoringTask` | `VehicleMonitoringTask` | `vehicle_monitoring_task.py` | `syncVehicleData` … |
| `partitionMaintenanceTask` | `PartitionMaintenanceTask` | `partition_maintenance_task.py` | `createFuturePartitions` … |
| `snapshotFlowSyncTask` | `SnapshotFlowSyncTask`（裸 `@Component`） | `snapshot_flow_sync_task.py` | `manualIncrementalSync` / `manualFullSync`；`syncSingleMonth` **不行**（要 `AtomicInteger` 参数，`JobInvokeUtil` 造不出） |

六个类都是**叶子类**（没有基类）—— 这是 `getattr` 能代替 `getDeclaredMethod` 的前提，
`tests/test_quartz_tasks.py::TestTaskRegistry` 逐类断言 `__bases__ == (object,)`。

`RyTask` 的参数按 Java `String.valueOf` 拼：`true` **小写**、`null` 拼成 `"null"`
（`_java_str`），见 `COMPATIBILITY.md` §42.6。

---

## 7. 工具层

| Java | Python | 要点 |
|---|---|---|
| `JobInvokeUtil.invokeMethod(SysJob)` | `invoke_method(sys_job)` | 先按 `isValidClassName` 决定"取 Bean"还是"反射造对象" |
| `getBeanName` / `getMethodName` / `getMethodParams` | `get_bean_name` / `get_method_name` / `get_method_params` | 后者返回 `[(值, 类型名)]`，类型判定顺序：`'` → `Boolean` → `Long` → `Double` → `Integer` |
| `getMethodParamsType` / `getMethodParamsValue` | `get_method_params_type` / `get_method_params_value` | 纯辅助，无调用点以外的作用 |
| `isValidClassName` | `is_valid_class_name` | 判据是"**点号多于 1 个**"（`count_matches(target, ".") > 1`）—— 决定走"取 Bean"还是"反射造对象" |
| `CronUtils.isValid` / `getInvalidMessage` / `getNextExecution` | `is_valid` / `get_invalid_message` / `get_next_execution` | 控制器只用 `is_valid`；`get_invalid_message` **无调用方**（照搬保留） |
| `ScheduleUtils.getJobKey(jobId, jobGroup)` | `get_job_key` | name = `"TASK_CLASS_NAME" + jobId`；`jobId` 为 `null` 时是 `"TASK_CLASS_ENAMEnull"` 那种字符串拼接 |
| `ScheduleUtils.createScheduleJob` | `create_schedule_job` | `JobDetail.jobDataMap` 只放**一个**键 `TASK_PROPERTIES`；存在则先删后建，`status='1'` 的再 `pauseJob` |
| `ScheduleUtils.handleCronScheduleMisfirePolicy` | `handle_cron_schedule_misfire_policy` | `misfire_policy` 三个"有值"分支实际只区分"补一次"与"跳过" |

---

## 8. 怎么跑

```bash
# 起服务（默认加载 sys_job 并重建调度器）
.venv\Scripts\python.exe -m uvicorn app.main:app --port 9989

# 不连库、只验证接口形状
set APP__SCHEDULER_ENABLED=false

# 只跑本切片
.venv\Scripts\python.exe -m pytest tests/test_quartz_controllers.py tests/test_quartz_cron_and_schedule.py ^
    tests/test_quartz_services.py tests/test_quartz_tasks.py
```

`app.scheduler-enabled=false` 会跳过 `_init_quartz`（**Java 没有这个开关**，
是本工程为"没有 MySQL 的环境也能起服务"加的，见 `COMPATIBILITY.md` §42.7）。
