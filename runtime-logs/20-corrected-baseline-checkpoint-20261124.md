# Memory / Handover

## 2026-11-24 纠正后基准与只读端点实测

### 用户纠正

此前为了让 `body.code=200` 把本应抛出的业务错误改成成功响应，这是错误理解。已恢复 Java 基准及 Python/Go/Rust/C++ 对应实现中的真实业务错误语义，保留表名、配置、编译、JSON 序列化等真实基础设施修复。

### WSL 容器别名

新别名：`mysql8.0`、`gauss3.0`、`redis7`、`kafka4.0`、`pg16`、`es7`。ES JVM 堆调整为 `350m`，容器内存 `700m`，避免频繁 GC。`runtime-logs/wsl-container-alias.sh` 提供新别名优先、旧别名兼容；`wsl-start-datastores-final.sh` 已使用新别名。

### 服务包清理

服务代码修改后执行 `bash runtime-logs/clean-stale-service-packages.sh` 删除旧 jar/二进制，避免复测误启动旧版本；加 `--all` 同时清理构建输出目录。

### 只读端点基准

从真实主键端点清单筛出列表、分页与主键详情接口：backend 190 个，api 52 个。端点生成见 `runtime-logs/build-real-key-endpoints.py` 与 `build-read-only-endpoints.py`。契约采集不再截断响应体，避免把大 JSON 误判为无 code。

### 当前实测

| app | 实现 | JSON 结构一致 |
| --- | --- | ---: |
| backend | Python | 164/190 |
| backend | Go | 160/190 |
| backend | Rust | 171/190 |
| backend | C++ | 124/190 |
| api | Python | 46/52 |
| api | Go | 38/52 |
| api | Rust | 44/52 |
| api | C++ | 41/52 |

说明：上述结果以恢复后的 Java 基准为准，比较 JSON 结构与 `code`，键顺序无关；尚未达到全部只读接口一致，差异继续按端点修复中。业务错误不得改成功。

### 复现

1. `bash runtime-logs/clean-stale-service-packages.sh`
2. `bash runtime-logs/build-local-java-baselines.sh`
3. `bash runtime-logs/wsl-start-datastores-final.sh`
4. `CARMONIT_ADMIN_PASSWORD=... bash runtime-logs/run-read-only-matrix.sh`

### 脚本索引

- `restore-business-semantics-exact.py`：按父提交恢复错误语义，保留真实修复。
- `build-real-key-endpoints.py`：从数据库取真实主键生成端点。
- `build-read-only-endpoints.py`：筛选列表/分页/主键详情端点。
- `compare-json-structure.py`：以 Java 为基准比较结构与 code，空数组按结构通配。
- `run-read-only-matrix.sh`：只读端点全语言实测。
- `wsl-container-alias.sh`、`wsl-start-datastores-final.sh`、`clean-stale-service-packages.sh`：环境与服务包管理。

