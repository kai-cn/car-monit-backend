# backend Python ↔ Java V3 对齐：交接记录

> 记录时间：2026-11-20（会话内实时记录）
> 分支：`py-v3-align`（源自 `car-monit-py-V2`，工作树 `d:/work/IdeaProjects/car-monit-py-V2-wt`）
> 对齐目标：`car-monit-backend-java-V3`

## 1. 已完成（P0 端点全量对齐）

| 项 | 结果 | 证据 |
|---|---|---|
| 新增导出 Controller | 10 个端点 `/manager/bigScreen/export/**` | `app/api/manager/bigscreen/big_screen_export_controller.py` |
| 新增运维 Controller | 6 个端点 `/monitor/bigscreen/**` | `app/api/monitor/big_screen_ops_controller.py` |
| `topTen` 时间参数 | 新增 `startTime`/`endTime`，默认最近 7 天 | `app/api/manager/bigscreen/big_screen_controller.py:407` |
| 服务层 | 导出状态机 + 下载令牌 + FeatureSwitch + DictVersion + ApiClientException | `app/manager/service/bigscreen/big_screen_v3_services.py` |
| 指标注册表 | Java `MetricsRegistry` 镜像 | `app/common/core/metrics/metrics_registry.py` |
| 响应过滤 | ETag/304 + X-Cache/X-Degrade/X-Data-* + 下载流排除 | `app/middleware/bigscreen_response.py` |
| 路由注册 | 总路由 **515**（原 499 + 16） | `create_app()` 实测 |
| 专用测试 | 6/6 通过 | `tests/test_v3_alignment.py` |
| 映射文档 | `MAPPING_MANAGER.md` 由幂等生成器自动更新 | 20 → 21 个 manager 控制器模块 |

## 2. 未完成 / 已知差异

1. **P1 真实 HTTP 调用**：`BigScreenExportService.api_client` 未注入，导出提交目前走本地状态机；
   Java V3 调用 api 的 `/api/v3/export/*` 由 `ResilientApiExecutor` 完成（Forest + 熔断 + 重试）。
2. **P1 其余 12 个 bigScreen GET 的服务层重写**：Java V3 改为 `BigScreenStatsService` /
   `BigScreenRealtimeService` / `BigScreenDictService` 等经 HTTP 取数；Python 仍走 master 的本地
   MyBatis 服务。路径/响应体一致，数据源不同（Java V3 为 api-first）。
3. **P2 字典版本自增**：`DictVersionService` 已实现，但尚未挂到 `SysDictDataController` /
   `SysDictTypeController` 的 8 个写端点上（Java V3 在这些端点里调用 `bump`）。
4. **P2 base 14 个 Controller 数据源切 API**：Java V3 从本地表切到 api HTTP；Python 仍查本地库。
   `ZdataTrailFittingController` 的 `dataSource=LOCAL_DB` 响应字段也未加。
5. **P2 权限 SQL**：`v3-bigscreen-export-permissions.sql` 的三个权限点需在生产库执行后才可访问新端点。

## 3. 测试环境说明

* venv：`D:\work\IdeaProjects\car-monit-backend-new\car-monit-py\.venv\Scripts\python.exe`（Python 3.12.9）。
* 密钥门禁：`TOKEN__SECRET` / `SPRING__DATASOURCE__DRUID__MASTER__PASSWORD` / `HENGDA__SECRET`
  必须提供高熵值；测试文件用 `monkeypatch` 注入，不污染其它测试。
* 全量 `pytest -q`：仅 1 个失败 `test_quartz_tasks.py::test_sync_full_data_aggregates_the_month_counts`
  —— 期望 20 个月但实际按当前日期（2026-11-20）算出 4 个月，是**时间依赖型既有失败**，与 V3 改动无关。
* 推荐门禁：
  ```powershell
  .venv\Scripts\python.exe -m pytest tests/test_v3_alignment.py -q
  ```

## 4. 云 runner 实测（2026-11-20 增补）

复用 `ci.yml` 的 `py` job（run `44712980926`）：**completed success**，coverage 73%。
云上暴露并修复时间炸弹用例（`ac960499`）。复用 `crosslang-parity-cloud.yml`（run `44713232995`）：
整条 success，Python vs Java8 对拍 `endpoints=2 fails=0`。探针已扩展 `--headers-env`
（Java V3 分支提交 `61462810`），供下个会话覆盖认证端点。详见 `V3-CLOUD-VERIFICATION.md`。

## 5. 文档索引

* `V3-ALIGNMENT-PLAN.md` —— 差距矩阵与实施顺序
* `V3-ALIGNMENT-INDEX.md` —— 文件级索引
* `V3-ALIGNMENT-HANDOVER.md` —— 本文件
* `V3-CLOUD-VERIFICATION.md` —— 云 runner 实测与对拍验收记录
* `MAPPING_MANAGER.md` / `COMPATIBILITY.md` —— master 基线对照（仍有效）
* `../docs/v3/review/` —— Java V3 审阅记录（决策依据）

## 5. 下一条命令

```powershell
Set-Location d:\work\IdeaProjects\car-monit-py-V2-wt
git add -A
git add -f car-monit-py/docs/V3-ALIGNMENT-*.md
git commit -m "feat(py): 对齐 Java V3 16 个新端点与导出/开关服务"
```
