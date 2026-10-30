# car-monit-py

`car-monit-backend-new`（RuoYi-Vue 3.8.7 / Spring Boot 2.5.15）的 **Python 3.12 + FastAPI**
等价实现。与 Java 工程并排放在同一个仓库里，便于逐文件 diff。

> **目标不是「重写一个更好的后端」，而是「让同一份前端、同一批调用方察觉不到后端换了语言」。**
> 路由、请求/响应字段、状态码、错误码、业务规则、边界条件全部按 Java 逐条对齐；
> 任何主动偏离都记在 [`COMPATIBILITY.md`](COMPATIBILITY.md) 里，并标注影响等级。

| 维度 | 数量 |
|---|---|
| 控制器 | **78** 个（`ruoyi-admin` 75 + `ruoyi-quartz` 2 + `ruoyi-generator` 1） |
| 端点 | Java **501**，Python **502**（多出 `GET /health`，可关闭；缺失 **0**） |
| 用例 | **3646** 条，全绿（3563 单测 + 83 条真实 MySQL/Redis 联调） |
| 文档 | `COMPATIBILITY.md`（差异台账）+ `MAPPING_*.md`（逐切片对照）+ `MIGRATION_PROGRESS.md`（进度） |

---

## 1. 目录结构

```text
car-monit-py/
├── app/
│   ├── main.py                 # RuoYiApplication：建 app、挂中间件、注册 78 个控制器
│   ├── settings.py             # 强类型版 application.yml（pydantic-settings）
│   ├── logging_config.py       # 镜像 logback-spring.xml
│   ├── api/                    # 控制器层，按 Java 包分组
│   │   ├── common/  system/  monitor/  tool/
│   │   ├── base/  manager/  flow/  quartz/  generator/
│   ├── common/                 # ruoyi-common：core / utils / annotation / enums / exception
│   ├── framework/              # ruoyi-framework：security / web / aspectj / config / interceptor
│   └── quartz/                 # 自研内存调度器（对应 org.quartz + ruoyi-quartz 的任务 Bean）
├── config/
│   ├── application.yml         # 与 Java 的 application.yml 同名同层级
│   ├── i18n/                   # messages.properties
│   └── templates/down/         # 下载模板
├── tests/                      # pytest；tests/integration 打真实 MySQL/Redis
├── scripts/
│   ├── smoke_test.py           # 部署后自检（真实 socket）
│   ├── app_pid.py              # 给 start.sh / start.bat 用的进程发现
│   ├── audit_endpoints.py      # 对拍：路由（Java 注解 vs @router）
│   ├── audit_domains.py        # 对拍：域字段（Java 字段 vs pydantic 别名）
│   ├── audit_envelopes.py      # 对拍：响应信封（返回类型分类矩阵）
│   ├── audit_messages.py       # 对拍：文案（双向，含 i18n 与拼接折叠）
│   └── gen_mapping_docs.py     # 生成 MAPPING_*.md 对照表
├── run.py                      # 一条命令启动（对应 main()）
├── start.sh / start.bat        # 对应 ry.sh / ry.bat
└── requirements.txt            # 锁定版本；pyproject.toml 是同一份依赖的声明式写法
```

## 2. 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | **3.12+** | `pyproject.toml` 的 `requires-python`；本机验证用 3.12.9 |
| MySQL | 5.7 / 8.x | 沿用 Java 工程的库表，**Python 侧不建表、不改 schema** |
| Redis | 5+ | 缓存、验证码、token、登录失败计数 |

Kafka / Elasticsearch / MinIO **不是启动前提**：默认关闭，不可达时只在启动日志里告警
（见 §7）。

## 3. 安装

```bash
cd car-monit-py
python -m venv .venv
.venv/Scripts/activate          # Windows；Linux/macOS 用 source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 是锁死版本的那一份；`pyproject.toml` 里的 `dependencies` 与它逐行对应。
Phase 4 的中间件适配器（Kafka / ES / MinIO）在 `[project.optional-dependencies].middleware`，
只有真要打开这些开关时才需要装。

## 4. 配置

优先级（高 → 低）：**真实环境变量 > `.env` > `config/application.yml` > `settings.py` 默认值**，
与 Spring Boot 的 `application.yml` + 环境变量一致。

```bash
cp .env.example .env            # 可选：不建也能跑，默认值与 Java 一致
```

键名规则：`application.yml` 的层级用双下划线连接，叶子键转 snake_case。

```text
spring.redis.host                      -> SPRING__REDIS__HOST
spring.datasource.druid.master.url      -> SPRING__DATASOURCE__DRUID__MASTER__URL
token.secret                            -> TOKEN__SECRET
```

`.env.example` 里有逐项的 Java ↔ Python 对照注释。注意 `logging.level.com.ruoyi` 这类带点号的
键**不能**做环境变量名，要改用 `LOGGING__LEVEL`（JSON）或直接改 `config/application.yml`。

## 5. 启动

### 开发 / 前台

```bash
python run.py                   # 端口取 config/application.yml 的 server.port，默认 9989
python run.py --reload          # 对应 spring.devtools.restart.enabled=true，仅开发用
```

等价写法（`run.py` 只是把 `server.port` 交给 uvicorn）：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9989
```

> 需要换端口：`SERVER__PORT=9990 python run.py`，或改 `config/application.yml`。

### 生产 / 后台

`start.sh`（Linux/macOS）与 `start.bat`（Windows）是 `ry.sh` / `ry.bat` 的 Python 版，
四个操作一一对应：

| 操作 | `start.sh` | `start.bat` |
|---|---|---|
| 启动 | `./start.sh start` | `start.bat start` 或双击后选 `1` |
| 停止 | `./start.sh stop` | `start.bat stop`（选 `2`） |
| 重启 | `./start.sh restart` | `start.bat restart`（选 `3`） |
| 状态 | `./start.sh status` | `start.bat status`（选 `4`） |

差异只在「怎么找到进程」：Java 侧用 `jps -l` 按 jar 名匹配，Python 没有同类命令，
两个脚本统一调 `scripts/app_pid.py`（用 `psutil` 读命令行，按入口文件名 `run.py` 匹配）。
解释器优先用工程自带的 `.venv`，其次 `$PYTHON` / PATH 上的 `python`。

**编码注意**：`start.bat` 与 `ry.bat` 一样用 **GBK** 保存。中文 Windows 的 `cmd` 按代码页 936
解析 `.bat`，存成 UTF-8 会让多字节序列把后面的 ASCII 字节（含 CR/LF）吃掉，表现为
「注释行被当成命令执行」。改这个文件请保持 GBK。

仓库**不提供** Dockerfile：Java 工程本身也没有，且 78 个控制器里有大量本地磁盘、
`oshi`/`psutil` 主机指标、真实 MySQL/Redis 依赖，容器化不是这次迁移的目标。

## 6. 验证

### 部署后自检（真实 socket）

```bash
python scripts/smoke_test.py
python scripts/smoke_test.py --base-url http://127.0.0.1:9989
```

5 项检查，退出码 `0` = 全通过，可直接接 CI / 发布后验证。它比 pytest 多走了一层：
真实 uvicorn、真实中间件顺序、真实 socket 字节（能验证 `{"msg":…,"code":…}` 的键序）。

### 全量用例

```bash
python -m pytest                          # 3646 条
python -m pytest tests/test_login_controller.py -v
python -m pytest tests/integration -m integration -v   # 只跑真实 MySQL/Redis 联调
```

`tests/integration` 会自己探测 MySQL/Redis，不可达时**跳过自己**，离线跑仍然全绿。
注意：跳过时 `--collect-only` 也不会展开这 83 条，所以离线数出来是 3563 而不是 3646。

### 与 Java 对拍

四个脚本都只读源码，两侧差异全部机械判定；有任何缺口即非 0 退出：

```bash
python scripts/audit_endpoints.py         # 路由：Java 501 / Python 502 / 缺失 0
python scripts/audit_domains.py           # 域字段：可比 115，属性/Excel/导出列零缺口
python scripts/audit_envelopes.py         # 响应信封：501 个可比端点全部归类
python scripts/audit_messages.py          # 文案：Java 148 种 ↔ Python 155 种，两侧缺口 0
```

对照表也是生成的（改完控制器重跑一次，否则表和代码会漂）：

```bash
python scripts/gen_mapping_docs.py        # 重写 MAPPING_{BASE,MANAGER,FLOW,TOOL,GENERATOR}.md
```

## 7. 中间件开关

| 开关 | 默认 | 说明 |
|---|---|---|
| `APP__KAFKA_ENABLED` | `false` | 4 个 `@KafkaListener`；关闭时启动打印告警，不注册消费者 |
| `APP__ELASTICSEARCH_ENABLED` | `true` | 不可达时降级为「查库」，不影响接口返回 |
| `APP__OSS_ENABLED` | `false` | MinIO/OSS；`sys_file` 的 17 个端点依赖它 |
| `APP__SCHEDULER_ENABLED` | `true` | 自研内存调度器（等价 Quartz 内存 JobStore） |
| `APP__SCHEDULED_ANNOTATIONS_ENABLED` | `false` | 镜像 Java 现实：没有 `@EnableScheduling`，9 个 `@Scheduled` 方法不触发 |
| `APP__HEALTH_ENDPOINT_ENABLED` | `true` | `GET /health`，Java 没有，唯一的多余端点 |

## 8. 常见问题

**Q：为什么所有业务异常都是 HTTP 200？**
因为 Java 就是 HTTP 200 + `{"msg":…,"code":500}`。只有未匹配路由（404）、方法不支持（405）
和 Spring 自己的错误页才带真实 HTTP 状态码，Python 逐条复刻 —— 见 `COMPATIBILITY.md` §2/§3。

**Q：`{"msg":"操作成功","code":200}` 的键序为什么是 `msg` 在前？**
`AjaxResult extends HashMap<String,Object>`，Jackson 按 `HashMap` 的**桶序**输出，不是 `put` 的先后。
`msg` 落在 0 号桶、`code` 落在 3 号桶，所以 `msg` 永远在前。Python 用
`app/common/core/domain/java_hash_map.py` 精确模拟桶序，详见 `COMPATIBILITY.md` §5.1。
`TableDataInfo`（`total, rows, code, msg`）和 `R`（`code, msg, data`）是普通 POJO，按字段序，**不要**套桶序。

**Q：金额字段为什么是字符串 `"12.5"`？**
全局 `ORJSONResponse` 的既有行为，早于本次复核，见 `COMPATIBILITY.md` §40.1。要改就是一次性
全局改动，不要逐接口打补丁。

**Q：启动报 `[WinError 10048]` 端口被占用？**
说明已经有一个实例在跑（`start.sh status` / `start.bat status` 可以确认）。
先用 `stop` 停掉，或换端口：`SERVER__PORT=9990 python run.py`。

**Q：日志在哪？**
`logs/sys-info.log` / `sys-error.log` / `sys-slow.log` / `sys-user.log`，按大小滚动
（Java 是时间 + 大小双策略，见 `COMPATIBILITY.md` §7）。控制台另有访问日志。

**Q：现在还剩什么没做？**
看 `MIGRATION_PROGRESS.md` 的「下一步」一节。控制器、用例、文档都已收尾；剩下的是
运维手册（Kafka / MinIO / ES 什么时候打开）和明确不打算复刻的差异。
