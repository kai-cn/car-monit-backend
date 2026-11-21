# backend Python ↔ Java V3 对齐：文档与文件索引

> 更新：2026-11-20

## 1. 文档

| 文件 | 用途 | 状态 |
|---|---|---|
| `V3-ALIGNMENT-PLAN.md` | 16 个新端点差距矩阵 + 行为级变更 | 已完成 |
| `V3-ALIGNMENT-HANDOVER.md` | 交接：已完成 / 未完成 / 阻断项 | 实时更新 |
| `V3-ALIGNMENT-INDEX.md` | 本文件 | 实时更新 |
| `ARCHITECTURE.md` / `COMPATIBILITY.md` / `MAPPING_*.md` | master 基线对照手册 | 仍有效 |

## 2. 新增/修改文件

### Controller
- `app/api/manager/bigscreen/big_screen_export_controller.py` —— 10 个导出端点
- `app/api/monitor/big_screen_ops_controller.py` —— 6 个可观测/灰度端点
- `app/api/manager/bigscreen/big_screen_controller.py` —— `topTen` 增加时间参数

### Service / 中间件
- `app/manager/service/bigscreen/big_screen_v3_services.py` —— 导出/审批/开关/字典版本服务
- `app/common/core/metrics/metrics_registry.py` —— Java `MetricsRegistry` 镜像
- `app/middleware/bigscreen_response.py` —— ETag/304 与可观测响应头
- `app/main.py` —— 注册两个新 Router + 响应过滤中间件

### 测试 / 文档
- `tests/test_v3_alignment.py` —— 6 个对齐用例
- `MAPPING_MANAGER.md` —— 幂等生成器自动更新（20 → 21 个 controller 模块）

## 3. 验证结果（2026-11-20 实测）

```
create_app() 路由总数 : 515（master 基线 499 + 16）
pytest tests/test_v3_alignment.py : 6 passed
pytest -q : 全部通过，除 1 个既有时间依赖失败（test_quartz_tasks）
```
