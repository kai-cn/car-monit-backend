"""``SysJobController`` / ``SysJobLogController`` —— ``/monitor/job`` 与 ``/monitor/jobLog``.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobController.java
#   ruoyi-quartz/src/main/java/com/ruoyi/quartz/controller/SysJobLogController.java
#   + the live probe table in evidence/_probe_job_err_out.txt

这一层测什么
------------
Mapper / Service 各有自己的用例文件，这里全部注入假 Service，只测**控制器自己的约定**：

* 13 个映射全部注册，且 ``GET /list`` / ``GET /export`` / ``DELETE /clean`` 必须排在
  路径变量之前（Spring 的 ``AntPathMatcher`` 字面量优先，FastAPI 只看注册顺序）；
* ``list`` 在 Service 之前调 ``startPage()``，``export`` 不调；
* ``run`` 用的是 ``monitor:job:changeStatus`` 权限点（**没有** ``monitor:job:run``）；
* 所有"看起来像 bug"的响应都与 ``evidence/_probe_job_err_out.txt`` 逐条对齐。

``raise_server_exceptions=False`` 的那个 client
-----------------------------------------------
``ValueError`` / ``AttributeError`` / ``SchedulerException`` / ``TaskException`` 都没有
专门处理器，落到 ``@app.exception_handler(Exception)`` —— Starlette 把它挂在
``ServerErrorMiddleware`` 上，**发完响应还会重新抛**。所以凡是走通用处理器的用例都必须
用 ``http_lenient``，否则 ``TestClient`` 会抛而不是返回。走 ``ExceptionMiddleware`` 的
``ServiceException``（参数类型不匹配）两个 client 都能用。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.monitor import sys_job_controller as job_controller
from app.api.monitor import sys_job_log_controller as job_log_controller
from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.core.page.page_helper import clear_page, take_page
from app.common.exception.exceptions import AccessDeniedException
from app.config.exception_handlers import (
    GENERIC_ERROR_MESSAGE,
    PARAMETER_ERROR_MESSAGE,
    register_exception_handlers,
)
from app.framework.security.context.security_context import (
    SecurityContextHolder,
    UsernamePasswordAuthenticationToken,
)
from app.quartz.domain.sys_job import SysJob
from app.quartz.domain.sys_job_log import SysJobLog
from app.quartz.util.schedule_utils import handle_cron_schedule_misfire_policy
from app.quartz.util.scheduler import CronScheduleBuilder, SchedulerException

# --------------------------------------------------------------------------- fakes


class _FakeJobService:
    """Java: ``@Autowired ISysJobService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysJob] = []
        #: 库里的行（``delete_job_by_ids`` / ``run`` 靠它判断"查不到"）。
        self.jobs: Dict[int, SysJob] = {}
        self.insert_rows = 1
        self.update_rows = 1
        #: Service 被调用时挂起中的分页参数（真实 mapper 会在这里 ``take_page()``）。
        self.page_taken: Any = None

    def select_job_list(self, job: SysJob) -> List[SysJob]:
        self.calls.append(("select_job_list", job.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_job_by_id(self, job_id: int) -> Optional[SysJob]:
        self.calls.append(("select_job_by_id", job_id))
        return self.jobs.get(job_id)

    def insert_job(self, job: SysJob) -> int:
        self.calls.append(("insert_job", job.model_copy(deep=True)))
        # 真实 service 的第一步就是按 misfirePolicy 选 builder，非法值抛 TaskException。
        handle_cron_schedule_misfire_policy(
            job, CronScheduleBuilder.cron_schedule(job.cron_expression)
        )
        return self.insert_rows

    def update_job(self, job: SysJob) -> int:
        self.calls.append(("update_job", job.model_copy(deep=True)))
        return self.update_rows

    def change_status(self, job: SysJob) -> int:
        self.calls.append(("change_status", job.model_copy(deep=True)))
        return self.update_rows

    def run(self, job: SysJob) -> None:
        self.calls.append(("run", job.model_copy(deep=True)))
        if job.job_id not in self.jobs:
            # Java: scheduler.triggerJob(...) -> SchedulerException
            raise SchedulerException(
                "The job (%s.%s%s) referenced by the trigger does not exist."
                % (job.job_group or "DEFAULT", "TASK_CLASS_NAME", job.job_id)
            )

    def delete_job_by_ids(self, job_ids: List[int]) -> None:
        self.calls.append(("delete_job_by_ids", list(job_ids)))
        for job_id in job_ids:
            if job_id not in self.jobs:
                # Java: deleteJob(null) -> job.getJobId() 的 NPE
                raise AttributeError("'NoneType' object has no attribute 'job_id'")

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _FakeJobLogService:
    """Java: ``@Autowired ISysJobLogService``."""

    def __init__(self) -> None:
        self.calls: List[tuple] = []
        self.list_result: List[SysJobLog] = []
        self.delete_rows = 0
        self.page_taken: Any = None

    def select_job_log_list(self, job_log: SysJobLog) -> List[SysJobLog]:
        self.calls.append(("select_job_log_list", job_log.model_copy(deep=True)))
        self.page_taken = take_page()
        return self.list_result

    def select_job_log_by_id(self, job_log_id: int) -> Optional[SysJobLog]:
        self.calls.append(("select_job_log_by_id", job_log_id))
        return None

    def add_job_log(self, job_log: SysJobLog) -> int:
        self.calls.append(("add_job_log", job_log))
        return 1

    def delete_job_log_by_ids(self, log_ids: List[int]) -> int:
        self.calls.append(("delete_job_log_by_ids", list(log_ids)))
        return self.delete_rows

    def delete_job_log_by_id(self, job_id: int) -> int:
        self.calls.append(("delete_job_log_by_id", job_id))
        return self.delete_rows

    def clean_job_log(self) -> None:
        self.calls.append(("clean_job_log",))

    def of(self, name: str) -> List[tuple]:
        return [call for call in self.calls if call[0] == name]


class _Fakes:
    """两个假 Service 的容器（fixture 一次注入两个控制器）。"""

    def __init__(self) -> None:
        self.job = _FakeJobService()
        self.log = _FakeJobLogService()


# --------------------------------------------------------------------------- 装配


@pytest.fixture(autouse=True)
def services(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Java ``@DirtiesContext``：每个用例都拿到干净的假协作者与安全上下文。"""
    SecurityContextHolder.clear_context()
    clear_page()
    fakes = _Fakes()
    monkeypatch.setattr(job_controller, "_JOB_SERVICE", fakes.job)
    monkeypatch.setattr(job_log_controller, "_JOB_LOG_SERVICE", fakes.log)
    # 直调函数时没有 ``JwtAuthenticationTokenFilter``，得自己放一个 *:*:* 的登录态
    authenticate()
    yield fakes
    SecurityContextHolder.clear_context()
    clear_page()
    job_controller.reset_job_controller()
    job_log_controller.reset_job_log_controller()


@pytest.fixture
def http() -> Any:
    """已登录的 mini app（``*:*:*``，等同超级管理员）。"""
    return TestClient(_build_app(login=True))


@pytest.fixture
def http_lenient() -> Any:
    """把服务端异常当响应的 mini app（``@ExceptionHandler(Exception)`` 会再重抛）。"""
    return TestClient(_build_app(login=True), raise_server_exceptions=False)


def _login_user(permissions: Optional[set] = None) -> LoginUser:
    user = SysUser(user_id=1, user_name="admin", dept_id=103)
    # 注意 ``set()`` 是**假值** —— 必须用 ``is None`` 区分"没指定"与"指定为空"。
    granted = {"*:*:*"} if permissions is None else permissions
    return LoginUser(token="t", user=user, permissions=granted)


def authenticate(permissions: Optional[set] = None) -> SysUser:
    """直调函数时用的登录态（默认超级管理员 ``*:*:*``；传 ``set()`` 就是无权限）。"""
    user = SysUser(user_id=1, user_name="admin", dept_id=103)
    granted = {"*:*:*"} if permissions is None else permissions
    login_user = LoginUser(token="t", user=user, permissions=granted)
    SecurityContextHolder.get_context().set_authentication(
        UsernamePasswordAuthenticationToken(login_user, None, [])
    )
    return user


def _build_app(login: bool) -> FastAPI:
    application = FastAPI()
    register_exception_handlers(application)
    if login:

        @application.middleware("http")
        async def _fake_jwt(request: Any, call_next: Any) -> Any:
            SecurityContextHolder.get_context().set_authentication(
                UsernamePasswordAuthenticationToken(_login_user(), None, [])
            )
            return await call_next(request)

    application.include_router(job_controller.router)
    application.include_router(job_log_controller.router)
    return application


# --------------------------------------------------------------------------- 路由表


class TestJobRoutes:
    def test_the_eight_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods))) for route in job_controller.router.routes
        }
        assert registered == {
            ("/monitor/job/list", ("GET",)),
            ("/monitor/job/export", ("GET",)),
            ("/monitor/job/{job_id}", ("GET",)),
            ("/monitor/job", ("POST",)),
            ("/monitor/job", ("PUT",)),
            ("/monitor/job/changeStatus", ("PUT",)),
            ("/monitor/job/run", ("PUT",)),
            ("/monitor/job/{job_ids}", ("DELETE",)),
        }

    def test_literal_paths_come_before_the_path_variable(self) -> None:
        """``GET /list`` / ``GET /export`` 若排在 ``/{job_id}`` 之后会被当成 ``jobId``。"""
        paths = [route.path for route in job_controller.router.routes]
        assert paths.index("/monitor/job/list") < paths.index("/monitor/job/{job_id}")
        assert paths.index("/monitor/job/export") < paths.index("/monitor/job/{job_id}")

    def test_the_sheet_name_is_the_java_literal(self) -> None:
        assert job_controller.EXPORT_SHEET_NAME == "定时任务"

    def test_the_java_controller_fqcn_is_the_quartz_one(self) -> None:
        """审计日志 ``method`` 列写的是全类名；SysJob 属于 quartz 包，不在 web.monitor。"""
        assert job_controller.JAVA_CONTROLLER == "com.ruoyi.quartz.controller.SysJobController"


class TestJobLogRoutes:
    def test_the_five_paths_are_registered(self) -> None:
        registered = {
            (route.path, tuple(sorted(route.methods)))
            for route in job_log_controller.router.routes
        }
        assert registered == {
            ("/monitor/jobLog/list", ("GET",)),
            ("/monitor/jobLog/export", ("GET",)),
            ("/monitor/jobLog/{config_id}", ("GET",)),
            ("/monitor/jobLog/clean", ("DELETE",)),
            ("/monitor/jobLog/{job_log_ids}", ("DELETE",)),
        }

    def test_clean_comes_before_the_path_variable(self) -> None:
        paths = [route.path for route in job_log_controller.router.routes]
        assert paths.index("/monitor/jobLog/clean") < paths.index("/monitor/jobLog/{job_log_ids}")

    def test_export_comes_before_the_broken_detail_route(self) -> None:
        paths = [route.path for route in job_log_controller.router.routes]
        assert paths.index("/monitor/jobLog/export") < paths.index("/monitor/jobLog/{config_id}")

    def test_clean_is_not_swallowed_by_the_path_variable_over_http(
        self, http: Any, services: _Fakes
    ) -> None:
        response = http.delete("/monitor/jobLog/clean")

        assert response.status_code == 200
        assert response.json()["code"] == 200
        assert services.log.of("clean_job_log") == [("clean_job_log",)]

    def test_the_sheet_name_is_the_java_literal(self) -> None:
        assert job_log_controller.EXPORT_SHEET_NAME == "调度日志"

    def test_the_java_controller_fqcn_is_the_quartz_one(self) -> None:
        assert (
            job_log_controller.JAVA_CONTROLLER
            == "com.ruoyi.quartz.controller.SysJobLogController"
        )


# --------------------------------------------------------------------------- list


class TestJobList:
    def test_returns_a_table_data_info(self, services: _Fakes) -> None:
        services.job.list_result = [SysJob(job_id=1, job_name="系统默认（无参）")]
        body = job_controller.list_jobs(SysJob()).to_dict()

        assert body["code"] == 200
        assert body["msg"] == "查询成功"
        assert body["rows"][0].model_dump(by_alias=True)["jobId"] == 1
        assert body["total"] == 1

    def test_start_page_runs_before_the_query(self, services: _Fakes) -> None:
        job_controller.list_jobs(SysJob())

        assert services.job.page_taken is not None
        assert services.job.page_taken.get_page_num() == 1
        assert services.job.page_taken.get_page_size() == 10

    def test_query_parameters_are_bound_to_the_entity(self, http: Any, services: _Fakes) -> None:
        http.get(
            "/monitor/job/list",
            params={"jobName": "系统", "jobGroup": "SYSTEM", "status": "0"},
        )

        bound = services.job.of("select_job_list")[0][1]
        assert bound.job_name == "系统"
        assert bound.job_group == "SYSTEM"
        assert bound.status == "0"


class TestJobLogList:
    def test_returns_a_table_data_info(self, services: _Fakes) -> None:
        services.log.list_result = [SysJobLog(job_log_id=1507, job_name="可疑车俩数据同步")]
        body = job_log_controller.list_job_logs(SysJobLog()).to_dict()

        assert body["code"] == 200
        assert body["rows"][0].model_dump(by_alias=True)["jobLogId"] == 1507
        assert body["total"] == 1

    def test_start_page_runs_before_the_query(self, services: _Fakes) -> None:
        job_log_controller.list_job_logs(SysJobLog())

        assert services.log.page_taken is not None
        assert services.log.page_taken.get_page_size() == 10

    def test_query_parameters_are_bound_to_the_entity(self, http: Any, services: _Fakes) -> None:
        http.get("/monitor/jobLog/list", params={"jobName": "同步", "jobGroup": "SYSTEM"})

        bound = services.log.of("select_job_log_list")[0][1]
        assert bound.job_name == "同步"
        assert bound.job_group == "SYSTEM"


# --------------------------------------------------------------------------- export


class TestExport:
    def test_job_export_puts_the_filename_in_msg(self, services: _Fakes) -> None:
        services.job.list_result = [SysJob(job_id=1, job_name="系统默认（无参）")]
        body = job_controller.export(SysJob())

        assert body["code"] == 200
        assert body["msg"].endswith("_定时任务.xlsx")
        # ``AjaxResult.success(String)`` 重载 —— 没有 ``data`` 键
        assert "data" not in body

    def test_job_export_does_not_start_a_page(self, services: _Fakes) -> None:
        job_controller.export(SysJob())
        assert services.job.page_taken is None

    def test_job_log_export_puts_the_filename_in_msg(self, services: _Fakes) -> None:
        services.log.list_result = [SysJobLog(job_log_id=1507)]
        body = job_log_controller.export(SysJobLog())

        assert body["code"] == 200
        assert body["msg"].endswith("_调度日志.xlsx")
        assert "data" not in body

    def test_export_routes_are_reachable_over_http(self, http: Any) -> None:
        """两条 ``/export`` 都不能被路径变量吃掉。"""
        assert http.get("/monitor/job/export").json()["msg"].endswith("_定时任务.xlsx")
        assert http.get("/monitor/jobLog/export").json()["msg"].endswith("_调度日志.xlsx")


# --------------------------------------------------------------------------- 详情


class TestGetInfo:
    def test_a_missing_job_has_no_data_key(self, http: Any) -> None:
        """线上 ``GET /monitor/job/999999`` -> ``{"msg":"操作成功","code":200}``."""
        response = http.get("/monitor/job/999999")

        assert response.status_code == 200
        assert response.json() == {"msg": "操作成功", "code": 200}

    def test_a_found_job_is_put_under_data(self, http: Any, services: _Fakes) -> None:
        services.job.jobs[7] = SysJob(job_id=7, job_name="系统默认（无参）", job_group="DEFAULT")
        body = http.get("/monitor/job/7").json()

        assert body["code"] == 200
        assert body["data"]["jobId"] == 7

    def test_the_log_detail_route_always_fails(self, http_lenient: Any) -> None:
        """Java: ``/{configId}`` 配的是 ``@PathVariable Long jobLogId`` -> 参数缺失."""
        for path in ("/monitor/jobLog/1", "/monitor/jobLog/abc"):
            response = http_lenient.get(path)

            assert response.status_code == 200
            assert response.json() == {
                "msg": "请求路径中缺少必需的路径变量[jobLogId]",
                "code": 500,
            }

    def test_the_log_detail_route_never_reaches_the_service(
        self, http_lenient: Any, services: _Fakes
    ) -> None:
        http_lenient.get("/monitor/jobLog/1")
        assert services.log.of("select_job_log_by_id") == []


# --------------------------------------------------------------------------- add / edit


class TestAdd:
    def test_a_valid_cron_is_inserted_with_the_current_user(
        self, http: Any, services: _Fakes
    ) -> None:
        response = http.post(
            "/monitor/job",
            json={
                "jobName": "__probe__",
                "jobGroup": "PROBE",
                "invokeTarget": "ryTask.ryNoParams",
                "cronExpression": "0 0 2 * * ?",
                "misfirePolicy": "3",
                "concurrent": "1",
                "status": "1",
            },
        )

        assert response.json() == {"msg": "操作成功", "code": 200}
        inserted = services.job.of("insert_job")[0][1]
        assert inserted.create_by == "admin"

    def test_an_empty_cron_is_rejected_before_the_service(
        self, http: Any, services: _Fakes
    ) -> None:
        response = http.post(
            "/monitor/job",
            json={"jobName": "__probe__", "cronExpression": "", "misfirePolicy": "3"},
        )

        assert response.json() == {"msg": "cron表达式不正确", "code": 500}
        assert services.job.of("insert_job") == []

    def test_a_missing_cron_is_a_parameter_error(self, http_lenient: Any) -> None:
        """``isValid(null)`` 抛 ``IllegalArgumentException`` -> 客户端参数问题，回“参数错误”."""
        response = http_lenient.post("/monitor/job", json={})

        assert response.status_code == 200
        assert response.json() == {"msg": PARAMETER_ERROR_MESSAGE, "code": 500}

    def test_a_bad_cron_wins_over_a_bad_misfire_policy(self, http_lenient: Any) -> None:
        """cron 校验在落库/注册之前，所以先报 cron。"""
        response = http_lenient.post(
            "/monitor/job",
            json={
                "jobName": "__probe__",
                "invokeTarget": "ryTask.ryNoParams",
                "cronExpression": "bogus",
                "misfirePolicy": "9",
            },
        )

        assert response.json() == {"msg": "cron表达式不正确", "code": 500}

    def test_an_unknown_misfire_policy_is_a_masked_task_exception(self, http_lenient: Any) -> None:
        response = http_lenient.post(
            "/monitor/job",
            json={
                "jobName": "__probe__",
                "jobGroup": "PROBE",
                "invokeTarget": "ryTask.ryNoParams",
                "cronExpression": "0 0 2 * * ?",
                "misfirePolicy": "9",
                "concurrent": "1",
                "status": "1",
            },
        )

        assert response.json() == {
            "msg": GENERIC_ERROR_MESSAGE,
            "code": 500,
        }


class TestEdit:
    def test_zero_rows_is_the_error_envelope(self, http: Any, services: _Fakes) -> None:
        """线上 ``PUT /monitor/job jobId=999999`` -> ``{"msg":"操作失败","code":500}``."""
        services.job.update_rows = 0
        response = http.put(
            "/monitor/job",
            json={
                "jobId": 999999,
                "jobName": "__probe__",
                "jobGroup": "PROBE",
                "invokeTarget": "ryTask.ryNoParams",
                "cronExpression": "0 0 2 * * ?",
                "misfirePolicy": "3",
                "concurrent": "1",
                "status": "1",
            },
        )

        assert response.json() == {"msg": "操作失败", "code": 500}

    def test_the_current_user_is_written_to_update_by(self, http: Any, services: _Fakes) -> None:
        http.put(
            "/monitor/job",
            json={"jobId": 7, "cronExpression": "0 0 2 * * ?", "status": "0"},
        )

        assert services.job.of("update_job")[0][1].update_by == "admin"

    def test_an_empty_cron_is_rejected_before_the_service(
        self, http: Any, services: _Fakes
    ) -> None:
        response = http.put("/monitor/job", json={"jobId": 7, "cronExpression": ""})

        assert response.json() == {"msg": "cron表达式不正确", "code": 500}
        assert services.job.of("update_job") == []


# --------------------------------------------------------------------------- 状态 / 立即执行


class TestChangeStatus:
    def test_only_the_status_is_overwritten(self, http: Any, services: _Fakes) -> None:
        services.job.jobs[7] = SysJob(
            job_id=7, job_name="系统默认（无参）", job_group="SYSTEM", status="1"
        )
        response = http.put("/monitor/job/changeStatus", json={"jobId": 7, "status": "0"})

        assert response.json() == {"msg": "操作成功", "code": 200}
        passed = services.job.of("change_status")[0][1]
        assert passed.status == "0"
        # 请求体里的其它字段全部丢弃，其余字段来自库里的旧值
        assert passed.job_name == "系统默认（无参）"
        assert passed.job_group == "SYSTEM"

    def test_a_missing_job_is_a_masked_npe(self, http_lenient: Any) -> None:
        """Java 是 ``{"msg":null,"code":500}``；P1-6 起非业务异常统一脱敏文案."""
        response = http_lenient.put(
            "/monitor/job/changeStatus", json={"jobId": 999999, "status": "0"}
        )

        assert response.status_code == 200
        assert response.json() == {"msg": GENERIC_ERROR_MESSAGE, "code": 500}


class TestRun:
    def test_a_missing_job_is_a_masked_scheduler_exception(self, http_lenient: Any) -> None:
        response = http_lenient.put("/monitor/job/run", json={"jobId": 999999})

        assert response.json() == {"msg": GENERIC_ERROR_MESSAGE, "code": 500}

    def test_an_existing_job_returns_success(self, http: Any, services: _Fakes) -> None:
        services.job.jobs[7] = SysJob(job_id=7, job_group="SYSTEM")
        response = http.put("/monitor/job/run", json={"jobId": 7})

        assert response.json() == {"msg": "操作成功", "code": 200}
        assert services.job.of("run")[0][1].job_id == 7

    def test_run_reuses_the_change_status_permission(
        self, services: _Fakes
    ) -> None:
        """Java 的 ``@PreAuthorize("@ss.hasPermi('monitor:job:changeStatus')")``."""
        authenticate({"monitor:job:changeStatus"})
        services.job.jobs[7] = SysJob(job_id=7, job_group="SYSTEM")

        assert job_controller.run(SysJob(job_id=7))["code"] == 200

    def test_run_is_denied_without_that_permission(self) -> None:
        """``monitor:job:run`` 这个串不存在，带它照样 403."""
        authenticate({"monitor:job:run"})

        with pytest.raises(AccessDeniedException):
            job_controller.run(SysJob(job_id=7))


# --------------------------------------------------------------------------- 删除


class TestJobRemove:
    def test_comma_separated_ids_are_parsed(self, services: _Fakes) -> None:
        services.job.jobs[1] = SysJob(job_id=1)
        services.job.jobs[2] = SysJob(job_id=2)
        body = job_controller.remove("1,2")

        assert services.job.of("delete_job_by_ids")[0][1] == [1, 2]
        assert body["code"] == 200

    def test_a_missing_id_is_a_masked_npe(self, http_lenient: Any) -> None:
        """Java 是 ``{"msg":null,"code":500}``；P1-6 起非业务异常统一脱敏文案."""
        response = http_lenient.delete("/monitor/job/999999")

        assert response.status_code == 200
        assert response.json() == {"msg": GENERIC_ERROR_MESSAGE, "code": 500}

    def test_a_non_numeric_id_uses_the_java_locale(self, http: Any) -> None:
        """线上 ``DELETE /monitor/job/abc`` 的中文文案，注意 ``[Ljava.lang.Long;``."""
        response = http.delete("/monitor/job/abc")

        assert response.status_code == 200
        assert response.json() == {
            "msg": "请求参数类型不匹配，参数[jobIds]要求类型为：'[Ljava.lang.Long;'，"
            "但输入值为：'abc'",
            "code": 500,
        }


class TestJobLogRemove:
    def test_zero_rows_is_an_error_envelope(self, http: Any, services: _Fakes) -> None:
        """与 ``SysJobController#remove`` 不同：这里是 ``toAjax(rows)``."""
        services.log.delete_rows = 0
        response = http.delete("/monitor/jobLog/999999")

        assert response.status_code == 200
        assert response.json() == {"msg": "操作失败", "code": 500}

    def test_rows_are_parsed_and_forwarded(self, http: Any, services: _Fakes) -> None:
        services.log.delete_rows = 2
        response = http.delete("/monitor/jobLog/1,2")

        assert response.json() == {"msg": "操作成功", "code": 200}
        assert services.log.of("delete_job_log_by_ids")[0][1] == [1, 2]

    def test_a_non_numeric_id_names_the_right_parameter(self, http: Any) -> None:
        response = http.delete("/monitor/jobLog/abc")

        assert response.json() == {
            "msg": "请求参数类型不匹配，参数[jobLogIds]要求类型为：'[Ljava.lang.Long;'，"
            "但输入值为：'abc'",
            "code": 500,
        }


class TestJobLogClean:
    def test_clean_returns_success_without_a_data_key(self, services: _Fakes) -> None:
        body = job_log_controller.clean()

        assert body["code"] == 200
        assert "data" not in body

    def test_clean_does_not_delete_by_ids(self, services: _Fakes) -> None:
        job_log_controller.clean()

        assert services.log.of("delete_job_log_by_ids") == []
        assert services.log.of("clean_job_log") == [("clean_job_log",)]


# --------------------------------------------------------------------------- 权限点


#: ``函数名 -> 调用参数``。控制器被 ``functools.wraps`` 包过，``__name__`` 仍是原名。
_JOB_ARGUMENTS: Dict[str, tuple] = {
    "list_jobs": (SysJob(),),
    "export": (SysJob(),),
    "get_info": (1,),
    "add": (SysJob(cron_expression="0 0 2 * * ?"),),
    "edit": (SysJob(cron_expression="0 0 2 * * ?"),),
    "change_status": (SysJob(job_id=1),),
    "run": (SysJob(job_id=1),),
    "remove": ("1",),
}

_JOB_LOG_ARGUMENTS: Dict[str, tuple] = {
    "list_job_logs": (SysJobLog(),),
    "export": (SysJobLog(),),
    "clean": (),
    "remove": ("1",),
}


def _expect_permission(function: Any, arguments: tuple, permission: str) -> None:
    """没这个权限点 -> 403；给了这个权限点 -> 不再被权限拦下（可能因业务原因报别的错）。"""
    authenticate(set())
    with pytest.raises(AccessDeniedException):
        function(*arguments)

    authenticate({permission})
    try:
        function(*arguments)
    except AccessDeniedException:  # pragma: no cover - 只有权限点写错才会走到
        pytest.fail("%s 应当接受权限点 %s" % (function.__name__, permission))
    except Exception:  # noqa: BLE001 - 业务/参数异常与权限无关
        pass


class TestPermissions:
    @pytest.mark.parametrize(
        ("function", "permission"),
        [
            (job_controller.list_jobs, "monitor:job:list"),
            (job_controller.export, "monitor:job:export"),
            (job_controller.get_info, "monitor:job:query"),
            (job_controller.add, "monitor:job:add"),
            (job_controller.edit, "monitor:job:edit"),
            (job_controller.change_status, "monitor:job:changeStatus"),
            (job_controller.run, "monitor:job:changeStatus"),
            (job_controller.remove, "monitor:job:remove"),
        ],
    )
    def test_the_job_permission_strings(self, function: Any, permission: str) -> None:
        _expect_permission(function, _JOB_ARGUMENTS[function.__name__], permission)

    @pytest.mark.parametrize(
        ("function", "permission"),
        [
            (job_log_controller.list_job_logs, "monitor:job:list"),
            (job_log_controller.export, "monitor:job:export"),
            (job_log_controller.clean, "monitor:job:remove"),
            (job_log_controller.remove, "monitor:job:remove"),
        ],
    )
    def test_the_job_log_permission_strings(self, function: Any, permission: str) -> None:
        """调度日志**没有**自己的权限点，全部复用 ``monitor:job:*``."""
        _expect_permission(function, _JOB_LOG_ARGUMENTS[function.__name__], permission)
