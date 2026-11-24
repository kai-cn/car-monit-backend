# Memory / Handover

## 最终纠错闭环：真实业务错误与只读接口结构对齐

### 纠正口径

此前为了让 `body.code=200` 把业务错误改成成功响应，这是错误理解。现已恢复 Java 基准及 Python/Go/Rust/C++ 中的真实业务错误语义：任务不存在、缺参数、非法资源、上游不可用等错误保持错误；比较时只要求候选与 Java 基准一致，不再强制成功。

### 真实主键基准

从本地数据库真实表中取存在的主键，生成 backend 190 个、api 52 个只读端点（列表、分页、主键详情），排除导出、下载、同步和写操作。生成器：`build-real-key-endpoints.py`、`build-read-only-endpoints.py`。契约采集已取消响应体截断，避免大 JSON 被误判为无 code。

### 最终实测结果

JSON 结构判据：以 Java 基准为准，键层级一致、键顺序无关；`code` 必须与 Java 基准一致；标量值差异不作为结构差异；空数组作为结构通配。

| app | 实现 | 结构一致 |
| --- | --- | ---: |
| backend | Python | 182/190 |
| backend | Go | 174/190 |
| backend | Rust | 174/190 |
| backend | C++ | 147/190 |
| api | Python | 47/52 |
| api | Go | 43/52 |
| api | Rust | 45/52 |
| api | C++ | 42/52 |

未通过项包括真实业务错误口径、ODS 派生字段、部分 C++ 行字段与无 code 响应。所有结果均在 `runtime-logs/local-parity-matrix/<app>/<lang>/structure-compare.json`，未隐藏差异。

### 环境与脚本

- 容器新别名：`mysql8.0`、`gauss3.0`、`redis7`、`kafka4.0`、`pg16`、`es7`；ES JVM 350m、容器 700m。
- `wsl-container-alias.sh`：新别名优先、旧别名兼容。
- `clean-stale-service-packages.sh`：代码修改后清除旧 jar/二进制，避免误启动旧版本。
- `run-read-only-matrix.sh`：只读端点全语言实测。
- `compare-json-structure.py`：以 Java 为基准的结构比较器。

### 复现

1. `bash runtime-logs/clean-stale-service-packages.sh`
2. `bash runtime-logs/build-local-java-baselines.sh`
3. `bash runtime-logs/wsl-start-datastores-final.sh`
4. 启动 9902 api Java 下游。
5. `CARMONIT_ADMIN_PASSWORD=... bash runtime-logs/run-read-only-matrix.sh`

