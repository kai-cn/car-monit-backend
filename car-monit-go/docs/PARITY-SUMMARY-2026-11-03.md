# 双端 parity 修复总结（2026-11-03 批次）

> 范围：`car-monit-go` 对 Java(RuoYi 3.8.7) 的接口响应一致性修复。
> 环境：两端共用 MySQL `127.0.0.1:3307/carmonitdb`，Redis 分别用 **db0(Java) / db2(Go)**；
> Java 服务复用已在跑的 `ruoyi-admin.jar --server.port=9988`，Go 监听 9989。
> 明细数据与逐条定性见同目录 [`PARITY-2026-11-02.md`](./PARITY-2026-11-02.md)，本文只收口「修了什么、凭什么、怎么验」。

## 1. 一页结论

| 校验面 | 覆盖量 | 起点 | 现在 |
|---|---|---|---|
| 路由清单（Java 控制器 vs Go 注册表） | Java 511 条 | 13 条 Go 缺失 | **0** |
| 默认分页专项（不带任何分页参数） | 91 条 | 42 条不一致 | **0** |
| 查询参数矩阵（25 端点 × 18 组合） | 1309 组合 | 183 组合有差异 | **0**（另 73 组为有意差异） |
| 全量 GET 逐字段 | 288 条 URL | 15 条差异 | **14**，全部定性为隔离设定或 Java 侧缺陷 |
| 写接口生命周期（POST→详情→PUT→DELETE） | 32 个资源 | — | 24 个四步全一致；8 个卡在 Java 侧写入缺陷；金额标度差异随测试数据而现 |
| Redis 双 DB 隔离断言 | 24 项 | — | **全部通过**，测试数据零残留 |

Go 侧共 14 项修复，其中 **9 项属于分页语义**——这一类在「固定带 `?pageNum=1&pageSize=3` 的对比」里
完全隐形，只有把参数面单独铺开才暴露。分页专题的独立总结见
[`PAGINATION-PARITY-2026-11-03.md`](./PAGINATION-PARITY-2026-11-03.md)。

## 2. 修复清单

| # | 现象（Go 与 Java 不一致） | 依据 | Go 落点 | 由哪个专项发现 |
|---|---|---|---|---|
| 1 | 登录后 Go 侧没有登录审计行 | `AsyncFactory.recordLogininfor:71-80` 先把 `Success/BadTry` 映射成 `Constants.SUCCESS="0"/FAIL="1"`；Go 直接写语义串，`char(1)` 溢出整行丢失 | `internal/auth/service.go: logininforStatus()` | 写生命周期 + 查库 |
| 2 | `GET /system/user/` 404，`GET /system/user` 却 200 | Spring 把 `{"/", "/{userId}"}` 里的 `"/"` 注册成带斜杠路径，精确路径上只有 POST/PUT | `internal/modules/system/user_handler.go`（带斜杠注册 `GetInfo`，不带斜杠注册 `MethodNotAllowed`） | 路由清单 |
| 3 | 根路径只支持 GET | `SysIndexController:24 @RequestMapping("/")` 不限方法 | `internal/router/router.go: engine.Any("/", …)` | 路由清单 |
| 4 | `/oss/**` 九个端点缺失 | `OssEndpoint.java:26-114` 未迁移 | `internal/modules/systemaux/oss_endpoint.go`（新增）+ `register.go` 挂载 | 路由清单 |
| 5 | `/oss/bucket` 失败耗时 210s vs Java 11.5s | minio-go 沿用 OS TCP 超时（Windows ≈21s）再乘内部重试 | `internal/modules/systemaux/oss.go: newOssStorage` 设 3s 建连超时 | `check_oss.py` |
| 6 | 45 个列表端点在请求不带分页参数时返回全量 | `TableSupport.getPageDomain` 用 `Convert.toInt(参数, 1/10)`，只要调了 `startPage()` 就分页 | 新增 `web.PageAlways(c)`，替换 base/manager 通用 `respondList`、car_track、car_free、quartz、ops、systemaux、generator 等列表路径 | `check_default_page.py` |
| 7 | `pageSize=0/-1` 时 Go 给 10 条、`pageNum=9999` 时 Go 给空、`pageSize=99999` 被截到 500 | `Convert.toInt` 只在「没传/解析不出数字」时回落默认值；`PageDomain.getReasonable()` null→TRUE（越界回末页）；Java 无 pageSize 上限 | `internal/web/pagination.go: Page()/paramInt/Clamp/LimitOffset`，删掉自造的 `MaxPageSize` | `check_query_matrix.py` |
| 8 | 客户端 `orderByColumn` 被 Go 忽略 | `PageUtils.startPage` 把 orderBy 交给 PageHelper，`OrderByParser.converToOrderBySql` 会**剥掉语句最外层 order by** 再拼客户端的 | `manager.orderFor`、`base.orderByFor`、`generator.selectGenTableList` | `check_query_matrix.py` |
| 9 | 代理端点 rows 多出恒为 null 的键、数字字面量被改写 | `/base/feestationexit/list` 走 hutool `JSONUtil.toBean(…, TableDataInfo.class)`（默认丢 null 成员），`/base/feeGantry/list` 走 Forest+Jackson（保留 null） | `internal/modules/base/fees.go: renderRemoteTable(c, table, dropNull)` + 上游 `UseNumber` 解码 | 全量 GET |
| 10 | 空结果 + 非法排序列：Java `200/total=0`，Go `500` | `PageInterceptor.java:137-145`：`afterCount` 返回 false 时直接 `afterPage(new ArrayList())`，数据查询根本不执行 | 新增 `web.PageDomain.SkipQuery(total)`，15 处分页执行器（11 个文件）先问这一句 | `check_query_matrix.py` |
| 11 | `reasonable=false` 且 `pageNum<=0`/越界时，Go 返回一整页而 Java 返回空 | `AbstractHelperDialect.java:86-107` 放行条件是 `pageNum > 0 && count > startRow`；`Page.java:245-256/365-369` 的下界钳位**只在 reasonable 为真**时发生 | `Clamp` 下界加 `Reasonable` 条件；`SkipQuery` 改成照抄放行条件；`Offset()` 复用 `startRow()`（`Page.java:345-348`） | 扩写矩阵组合 |
| 12 | 手拼 SQL 的端点忽略客户端排序（`incomeStatics` 等）、ops 两个日志端点完全不认 `orderByColumn`、`/system/indexmenu/list` 语句自带 order by 时不认 | 同 #8（PageHelper 替换语义） | `manager/car_free.go`（4 处）、`manager/car_track.go`（1 处）、`ops/params.go: orderFor()` + 两个 List、`systemaux/common.go: queryPage` 去掉 Contains 判断、`systemaux/indexmenu.go` 把语句排序移进 defaultOrder | 扩写矩阵组合 + 定点复测 |
| 13 | `isAsc=bogus` 时 Go 按 asc 正常返回，Java 500 | `PageDomain.getOrderBy()` 是 `toUnderScoreCase(col) + " " + isAsc`，方向值**不校验**，交给 MySQL 报错；别名 `ascending/descending` 是在 `setIsAsc` 里转的 | `web.OrderBy` 去掉「非 desc 即 asc」兜底，原样拼接（非法字符仍按白名单拦掉） | 扩写矩阵组合 |
| 14 | `reasonable=1/yes/ok/bogus` Go 当 false（越界页返回空），Java 仍回末页 | `TableSupport` → `getParameterToBool` → `Convert.toBool(值, null)`：`true/yes/ok/1` 真、`false/no/0` 假、空与乱值 null → `PageDomain.getReasonable()` 回落 TRUE | `web.Page` 用同一套词表 + 默认回落真 | 补单测时逐行读源码发现；矩阵新增 2 组 `reasonable` 用例 |

## 3. 分页语义对齐的取证方式

不靠记忆、不靠猜：从本地 Maven 仓库 `pagehelper-5.3.3-sources.jar` 解出源码逐行核对，
再把结论钉成单测 `internal/web/pagination_test.go`（12 组钳位/短路 + 8 组排序拼接）。

| Java 源码 | 语义 | Go 对应 |
|---|---|---|
| `PageInterceptor.java:137-145` | count 后 `afterCount` 为 false 直接返回空 List | `PageDomain.SkipQuery` |
| `AbstractHelperDialect.java:86-107` | 放行条件 `pageNum>0 && count>startRow`；`pageSizeZero` 分支 | `SkipQuery`（`pageSize<0` 由 `Page()` 归一为 0，等价空结果） |
| `Page.java:221-239` | `setTotal` 内 `reasonable && pageNum>pages` 回末页，`pages==0` 不改页码 | `Clamp` 上界 |
| `Page.java:245-256`、`365-369` | `pageNum<=0` 只在 reasonable 为真时拉回 1 | `Clamp` 下界 |
| `Page.java:345-348` | `startRow = pageNum>0 ? (pageNum-1)*pageSize : 0` | `startRow()` / `Offset()` |
| `OrderByParser.java:54-73` | 剥掉最外层 order by，再拼客户端 orderBy；原 order by 含 `?` 抛 `PageException` | `orderFor` / `orderByFor` / `queryPage(defaultOrder 形参)` |
| `PageDomain.setIsAsc` / `getOrderBy` / `SqlUtil.escapeOrderBySql` | 别名转换、方向值原样、字符白名单 | `web.Page()` switch、`web.OrderBy`、`web.orderByPattern` |
| `ServletUtils.getParameterToBool` → `Convert.toBool(值, null)` → `PageDomain.getReasonable()` | `reasonable` 词表 `true/yes/ok/1` 真、`false/no/0` 假、空与乱值 → null → 回落 TRUE | `web.Page` 的 reasonable switch |

## 4. 校验脚本自身的盲区与方法论

1. **固定参数掩盖参数面**：前两轮 GET 对比一律带 `?pageNum=1&pageSize=3`，
   「不带参数也分页」「越界页」「排序覆盖」三类差异结构性不可见。
   现在拆成 `check_default_page.py`（从 Java 源码抽出所有 `startPage()` 路由，不带参数比）
   与 `check_query_matrix.py`（组合矩阵）两个专项。
2. **不要把「响应没有 rows」当作跳过条件**：`check_query_matrix.py` 原来是
   `if "rows" not in a: continue`，于是 Java 返回错误信封的组合被静默跳过 ——
   ops 两个日志端点的排序缺陷正是改完之后才现形（一次报出 24 组）。
   现在：两边都是 TableDataInfo 就逐字段比，否则只比信封；已知有意差异单独计数，不混进失败。
3. **组合表要成对覆盖参数**：`isAsc=bogus` 以前从不与 `orderByColumn` 同时出现、
   `reasonable=false` 从不与越界页码同时出现 —— 两个单参数都「正常」，组合起来才暴露差异。
4. **把语义钉成单测时，要顺着一行行读 Java**：第 14 项（`reasonable` 词表）不是跑出来的，
   是写 `TestPageFromRequest` 时读 `Convert.toBool` 才发现 Go 只认 `"true"`；
   实测 `reasonable=1/yes/ok/bogus` 四种取值 Java 都按 TRUE 处理，Go 当时会给空页。
   读源码的成本低于在灰度后被用户发现的成本。

其它环境层面的坑（写在这里避免重复踩）：Git Bash 会把 `/manager` 之类参数改写成交付路径，
必须 `MSYS2_ARG_CONV_EXCL='*'`；控制台需要 `PYTHONIOENCODING=utf-8`；
仓库 `core.autocrlf=true`，`gofmt -l .` 会列出所有文件，格式化检查要在 LF 归一后的副本上做。

## 5. 有意保留的差异（不修）

| 场景 | Java | Go | 理由 |
|---|---|---|---|
| `orderByColumn=1;drop` 等非法字符 | `UtilException` → `code=500`、`msg="参数不符合规范，不能进行查询"` | 拦掉非法字符后忽略排序，正常返回 | 两边都注入不成功；不让探测请求把列表打成 500。矩阵里计为「已知有意差异」（73 组） |
| `/manager/confimfree/concernedList?orderByColumn=totalAmount` | `500 Unknown column 'total_amount'`（select 别名写成 camelCase `total_amount totalAmount`，外层 order by 认不到） | `200` 正常排序（Go 别名是 `AS total_amount`） | 对齐要改 Go 的列别名，牵动 GORM 列映射；两端响应字段名本来就一致，风险大于收益 |
| `DECIMAL(m,2)` 金额字面量 | `67.00`、`111.00`（BigDecimal 保留标度） | `67`、`111`（`0.33` 这类非整值两边一致） | 数值相等。逐字面对齐需给每个金额字段保留原始标度，涉及上百字段与扫描层 |
| Redis 运行态可见性 | `/monitor/online/list`、`/monitor/cache` 只看得见自己 DB | 同左 | 就是「两端不同 DB」这一设定本身要的效果，隔离断言已验证互不写入 |

## 6. 遗留待办

- `/oss/**` 九个端点的**成功**形态未核对：`oss.endpoint=172.30.100.102:9002` 的 MinIO 在本环境不可达，
  只比过 500 信封与状态码。有可用 MinIO 后逐字段再比一次。
- Go 侧 `/oss` 失败耗时 30s 仍大于 Java 的 11.5s（3s 建连超时 × minio 内部重试）。
- `/base/snapshotflow/list` 的分表遍历是 Go 复刻 Java `SnapshotFlowEnhancedService` 的自定义实现
  （不是 PageHelper），`reasonable`/`orderByColumn` 语义不适用；本轮只验证了空库条件下的等价返回。
- 车辆缓存 `car_list`/`car_list_jc`/`white_car_list` 里留有测试期 `PARITY_*` 行：
  两端行为相同（`deleteCarInfoByIds` 不刷缓存），且没有任何接口会读出来，故不手工清理。

## 7. 复现

```bash
cd D:/work/IdeaProjects/car-monit-backend-new/car-monit-go
go build ./... && go vet ./... && go test ./...

# 重启 Go（启动日志供路由专项解析）
PID=$(netstat -ano | grep -E "TCP +0.0.0.0:9989" | awk '{print $5}' | head -1)
taskkill //PID $PID //F
go build -o bin/carmonit-server.exe ./cmd/server
bin/carmonit-server.exe > C:/Users/abelz/AppData/Local/Temp/carmonit.log 2>&1 &

python scripts/parity/routes.py --log C:/Users/abelz/AppData/Local/Temp/carmonit.log
for m in manager base flow system monitor tool; do
  MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/compare_get.py \
    --prefix "/$m" --out C:/Users/abelz/AppData/Local/Temp/sum_$m.json --workers 5
done
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_default_page.py
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_query_matrix.py
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/compare_write.py
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_redis_isolation.py
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_oss.py
```

## 8. 本批次改动的文件

- 分页语义：`internal/web/pagination.go`（`PageAlways`/`paramInt`/`Page` 的 reasonable 词表/
  `Clamp`/`SkipQuery`/`startRow`/`Offset`/`OrderBy`）、新增 `internal/web/pagination_test.go`
  （16 组钳位/短路 + 21 组参数解析 + 8 组排序 + 3 组 LIMIT）
- 执行器接短路：`base/support.go`、`manager/support.go`、`system/common.go`、`systemaux/common.go`、
  `flow/handler.go`、`flow/repo_messageinfo.go`、`quartz/service.go`（2 处）、`generator/sql.go`、`ops/params.go`、
  `manager/car_track.go`、`manager/car_free.go`（4 处）
- 排序覆盖：`ops/{params,logininfor,operlog}.go`、`systemaux/{common,indexmenu}.go`、
  `manager/{car_free,car_track}.go`、`base/crud.go`、`manager/support.go`
- 校验脚本：`scripts/parity/check_query_matrix.py`（组合扩到 18 种、修掉 rows 盲区、已知差异单列）
- 文档：`docs/PARITY-2026-11-02.md`（§4 第 9–14 项、§4.2/§4.3、§5–§10）、
  `docs/PAGINATION-PARITY-2026-11-03.md`（分页专题）、`docs/PROGRESS.md`（§3.9）、本文
