"""业务任务 bean 包（``com.ruoyi.quartz.task``）.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/

六个 ``@Component`` 类的 Python 镜像：

    ==============================  =========================================
    Java 类                          Bean 名（``SpringUtils.getBean`` 的键）
    ==============================  =========================================
    ``RyTask``                       ``ryTask``（``@Component("ryTask")``）
    ``OrgTask``                      ``orgTask``（``@Component("orgTask")``）
    ``TrackTask``                    ``trackTask``（``@Component("trackTask")``）
    ``VehicleMonitoringTask``        ``vehicleMonitoringTask``（显式 value）
    ``PartitionMaintenanceTask``     ``partitionMaintenanceTask``（裸注解 -> 类名首字母小写）
    ``SnapshotFlowSyncTask``         ``snapshotFlowSyncTask``（同上）
    ==============================  =========================================

导入本包 = Spring 的组件扫描
----------------------------
Java 的 ``@Component`` 由 ``ClassPathBeanDefinitionScanner`` 在启动时实例化并放进容器，
所以 ``JobInvokeUtil.invokeMethod`` 里 ``SpringUtils.getBean("trackTask")`` 才拿得到单例。
Python 没有扫描器，**导入即注册**：下面这一串 :func:`~app.common.utils.spring_utils.register_named`
就是"扫描"的等价物，必须在应用启动路径上执行一次。

:mod:`app.main` 在模块导入期 ``import app.quartz.task``（在 ``create_app()`` 之前），
理由和 ``@Component`` 一样 —— 注册表要在第一个请求之前就绪。

为什么是 ``register_named`` 而不是 ``register_bean``
----------------------------------------------------
``register_bean`` 用类名首字母小写推导 Bean 名，对裸 ``@Component`` 的两个类是**巧合正确**的；
但 ``RyTask`` 等四个类在 Java 里写的是 ``@Component("ryTask")`` 这种**显式 value**，
一旦有人重命名类，推导名就会静默漂移。所以六个一律显式给名，且名字取自各模块的
``BEAN_NAME`` 常量（该常量就是 Java 注解里的 value 的逐字转写）。

单例语义
--------
每个类只实例化**一次**，与 Spring 的默认 ``singleton`` 作用域一致。任务类本身不持有
"每次执行"的状态（``SnapshotFlowSyncTask`` 的线程池是唯一例外，对应 Java 的
``@PostConstruct`` 里创建的那个 ``ExecutorService``），所以单例是安全的。
注意 ``Scheduler._run_job`` 走的是 ``job_class()`` 直接新建实例（对应 Quartz 的
``SimpleJobFactory``）—— 那是 ``QuartzJobExecution`` 包装器，**不是**这里的业务 bean。

``PartitionMaintenanceTask`` / ``SnapshotFlowSyncTask`` 的 Bean 名值得留意
------------------------------------------------------------------------
Java 里它们是裸 ``@Component``，而 ``sys_job.invoke_target`` 的 18 条记录里**没有**
指向它们的目标。但它们照样在容器里，手工往 ``sys_job`` 插一行
``snapshotFlowSyncTask.manualIncrementalSync()`` 是能跑起来的（``syncSingleMonth``
不行 —— 它要一个 ``AtomicInteger``，``JobInvokeUtil`` 造不出这种类型）。所以两者也注册。
"""

from __future__ import annotations

from app.common.utils.spring_utils import register_named
from app.quartz.task.org_task import BEAN_NAME as ORG_TASK_BEAN_NAME
from app.quartz.task.org_task import OrgTask
from app.quartz.task.partition_maintenance_task import (
    BEAN_NAME as PARTITION_MAINTENANCE_TASK_BEAN_NAME,
)
from app.quartz.task.partition_maintenance_task import PartitionMaintenanceTask
from app.quartz.task.ry_task import BEAN_NAME as RY_TASK_BEAN_NAME
from app.quartz.task.ry_task import RyTask
from app.quartz.task.snapshot_flow_sync_task import BEAN_NAME as SNAPSHOT_FLOW_SYNC_TASK_BEAN_NAME
from app.quartz.task.snapshot_flow_sync_task import SnapshotFlowSyncTask
from app.quartz.task.track_task import BEAN_NAME as TRACK_TASK_BEAN_NAME
from app.quartz.task.track_task import TrackTask
from app.quartz.task.vehicle_monitoring_task import (
    BEAN_NAME as VEHICLE_MONITORING_TASK_BEAN_NAME,
)
from app.quartz.task.vehicle_monitoring_task import VehicleMonitoringTask

#: Bean 名 -> 实例，顺序与上面表格一致（顺序无运行期意义，只为可读）。
TASK_BEANS = {
    RY_TASK_BEAN_NAME: RyTask(),
    ORG_TASK_BEAN_NAME: OrgTask(),
    TRACK_TASK_BEAN_NAME: TrackTask(),
    VEHICLE_MONITORING_TASK_BEAN_NAME: VehicleMonitoringTask(),
    PARTITION_MAINTENANCE_TASK_BEAN_NAME: PartitionMaintenanceTask(),
    SNAPSHOT_FLOW_SYNC_TASK_BEAN_NAME: SnapshotFlowSyncTask(),
}

for _bean_name, _bean in TASK_BEANS.items():
    register_named(_bean_name, _bean)


def get_bean_by_name(bean_name: str):
    """Java: ``SpringUtils.getBean(beanName)`` 的**本包内**快捷方式（测试用）."""
    return TASK_BEANS[bean_name]


__all__ = [
    # 类
    "OrgTask",
    "PartitionMaintenanceTask",
    "RyTask",
    "SnapshotFlowSyncTask",
    "TrackTask",
    "VehicleMonitoringTask",
    # Bean 名
    "ORG_TASK_BEAN_NAME",
    "PARTITION_MAINTENANCE_TASK_BEAN_NAME",
    "RY_TASK_BEAN_NAME",
    "SNAPSHOT_FLOW_SYNC_TASK_BEAN_NAME",
    "TRACK_TASK_BEAN_NAME",
    "VEHICLE_MONITORING_TASK_BEAN_NAME",
    # 注册表
    "TASK_BEANS",
    "get_bean_by_name",
]
