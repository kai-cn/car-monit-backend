# 分页语义修复总结（2026-11-03）

> 专题范围：只讲分页。双端整体校验见 [`PARITY-2026-11-02.md`](./PARITY-2026-11-02.md)（§4 第 6–13 项、§4.2、§4.3），
> 全批次收口见 [`PARITY-SUMMARY-2026-11-03.md`](./PARITY-SUMMARY-2026-11-03.md)。
> 依据来源：本地 Maven 仓库 `pagehelper-5.3.3-sources.jar`（`pagehelper-spring-boot-starter 1.4.7`）
> 与 RuoYi `ruoyi-common` 的 `TableSupport` / `PageDomain` / `PageUtils` / `SqlUtil`，逐行核对，不是凭记忆。

## 1. 结论

| 项 | 数据 |
|---|---|
| 分页相关修复 | 9 项（§4 第 6–14 项） |
| 受影响 Go 代码 | `internal/web/pagination.go` + 15 处分页执行器（11 个文件） |
| 默认分页专项（不带参数） | 42 条不一致 → **0** |
| 查询参数矩阵 | 1309 组合（25 端点 × 18 组合）：起点 183 → 中间 24 → **0**（另 73 组为有意差异） |
| 全量 GET 回归 | 288 条 URL，250 逐字段一致 / 14 差异全部定性 / 24 非 JSON —— 与修复前逐格相同，无回归 |
| 单测 | `internal/web/pagination_test.go`：16 组钳位/短路 + 21 组参数解析 + 8 组排序拼接 + 3 组 LIMIT；`pagination.go` 12 个函数语句覆盖 **100%** |

## 2. Java 侧到底怎么分页

一条列表请求的实际链路：

```
Controller → PageUtils.startPage()
              ├─ TableSupport.getPageDomain()   // Convert.toInt(pageNum,1)、toInt(pageSize,10)
              ├─ SqlUtil.escapeOrderBySql(pageDomain.getOrderBy())   // 白名单不过 → UtilException
              └─ PageHelper.startPage(pageNum,pageSize,orderBy).setReasonable(reasonable)
           → mapper 方法（MyBatis 执行）
              └─ PageInterceptor.intercept()
                    ├─ dialect.skip()?                      否
                    ├─ dialect.beforeCount()?               是 → 执行 count
                    ├─ dialect.afterCount(count)?           ← 放行条件在这里
                    │     不放行 → return dialect.afterPage(new ArrayList(), …)   // 数据查询一次都不执行
                    └─ ExecutorUtil.pageQuery()
                          ├─ dialect.getPageSql()           // 追加分页；orderBy 非空时 OrderByParser 替换排序
                          └─ dialect.afterPage(list)        // 把 Page 塞回结果
Controller ← getDataTable(list)：new PageInfo(list).getTotal()
```

关键取值语义（`ruoyi-common`）：

| Java | 语义 |
|---|---|
| `TableSupport.getPageDomain` | `Convert.toInt(参数, 默认)` —— **只有没传或解析不出数字**才用默认值；显式 `0`、`-1` 是合法入参 |
| `PageDomain` 字段默认 | `isAsc = "asc"`、`reasonable = true`；`getReasonable()` 在字段为 null 时返回 **Boolean.TRUE** |
| `ServletUtils.getParameterToBool` → `Convert.toBool(值, null)` | `reasonable` 的词表：`true/yes/ok/1` → 真、`false/no/0` → 假、**空值与乱值 → null**（再被 `getReasonable()` 回落成 TRUE） |
| `PageDomain.setIsAsc` | 有 `isNotEmpty` 保护；`ascending→asc`、`descending→desc`，其它值原样保留 |
| `PageDomain.getOrderBy` | `toUnderScoreCase(orderByColumn) + " " + isAsc`，**方向值不校验** |
| `SqlUtil.escapeOrderBySql` | 白名单 `^[a-zA-Z0-9_\ \,\.]+$` + SQL 关键字黑名单，不过则抛 `UtilException("参数不符合规范，不能进行查询")` |

PageHelper 内部的三个决定点：

| 源码 | 语义 |
|---|---|
| `PageInterceptor.java:137-145` | `afterCount` 返回 false 时直接 `afterPage(new ArrayList())` —— **数据查询不执行**，因此非法 ORDER BY 也不报错 |
| `AbstractHelperDialect.java:86-107` | 先 `page.setTotal(count)`，放行条件 `page.getPageNum() > 0 && count > page.getStartRow()`；另有 `pageSizeZero` 分支（`pageSize<0` 不放行；`pageSize=0` 仍执行） |
| `Page.java:221-239` | `setTotal` 里 `pages = ceil(total/pageSize)`；`reasonable && pageNum > pages` 时回末页，且 **`pages==0` 时连页码都不改** |
| `Page.java:245-256`、`365-369` | `pageNum<=0` 回到 1 的前提是 **reasonable 为真** |
| `Page.java:345-348` | `startRow = pageNum > 0 ? (pageNum-1)*pageSize : 0` |
| `OrderByParser.java:54-73` | 客户端给了 orderBy：**剥掉语句最外层的 order by** 再拼（原 order by 含 `?` 抛 `PageException`，解析失败则降级为直接拼接） |
| `PageInfo(List)` | 入参不是 `Page`（例如 service 又把结果重新聚合成了新 `ArrayList`）时，`total` 退化为 `list.size()` |

## 3. Go 侧实现

`internal/web/pagination.go` 是唯一的语义出处，字段一一对应 Java：

| Go | 对应 Java | 说明 |
|---|---|---|
| `Page(c)` | `TableSupport.getPageDomain` + `PageDomain` setter | `paramInt` 复刻 `Convert.toInt`；负 `pageSize` 归一为 0；`reasonable` 用 `Convert.toBool` 的同一套词表（只有 `false/no/0` 置假，乱值回落真）；`HasPage` = `pageNum` 与 `pageSize` **都传了** |
| `PageAlways(c)` | 无条件调过 `startPage()` 的端点 | 与 `Page(c)` 只差 `HasPage=true`（Java 缺省就是 1/10 一页） |
| `Clamp(total)` | `Page.setTotal` + `setReasonable` | 上下界钳位都受 `Reasonable` 约束 |
| `startRow()` / `Offset()` | `Page.calculateStartAndEndRow` | `pageNum<=0` 时起始行是 0 |
| `LimitOffset(total)` | — | 调用方唯一入口：先钳位再算 LIMIT/OFFSET |
| `SkipQuery(total)` | `AbstractHelperDialect.afterCount` | `!(pageNum>0 && total>startRow)`，15 处执行器先问这一句 |
| `OrderBy()` / `OrderByWithDefault()` | `PageDomain.getOrderBy` + `SqlUtil.escapeOrderBySql` | 白名单不过 → 忽略排序（Java 是 500，见 §6） |

排序覆盖统一成一个函数（避免每个包各写一套）：`base/crud.go:138 orderByFor`、
`manager/support.go:306 orderFor`、`ops/params.go:116 orderFor`、`system/common.go:214 orderByOr`、
其余走 `web.OrderByWithDefault`（`systemaux`/`flow`/`quartz`），`generator/sql.go` 用 `pd.OrderBy()`。

接入短路的 15 处执行器（11 个文件）：

```
base/support.go            list()                     1
manager/support.go         list()                     1
manager/car_free.go        pcIncomeStatics / incomeDetailList / concernedList / pcCarStatistics   4
manager/car_track.go       trackQuery()               1
system/common.go           queryPaged()               1
systemaux/common.go        queryPage()                1
ops/params.go              queryPage()                1
flow/handler.go            queryList()                1
flow/repo_messageinfo.go   messageInfoList()          1
quartz/service.go          ListJobs / ListJobLogs     2
generator/sql.go           queryPagedTables()         1
```

**不需要接的两类**（避免误改）：
`generator/handler.go:281 pageColumns`（内存分页，没有 SQL）、
`base/snapshotflow.go` 分表遍历（Java 侧是 `SnapshotFlowEnhancedService` 自定义 `LIMIT #{offset},#{pageSize}`，
不是 PageHelper；Go 已按同样的「`total<=offset` 直接空 + 单表失败 continue」复刻）。

## 4. 八项修复逐条

| # | 现象 | 依据 | 落点 | 回归用例 |
|---|---|---|---|---|
| 6 | 45 个列表端点在不带分页参数时返回全量，Java 只给一页 | `Convert.toInt(参数, 1/10)`：Java 永远分页 | `web.PageAlways` 替换所有 Java 侧调过 `startPage()` 的列表路径 | `check_default_page.py`（42 → 0）+ `TestPageAlwaysForcesPaging` |
| 7a | `pageSize=0/-1` Go 给 10 条；`pageSize=99999` 被 Go 截到 500 | `Convert.toInt` 只有解析失败才回落；Java 无 pageSize 上限 | `Page()` + `paramInt`，删除 `MaxPageSize` | `TestPageFromRequest`（显式 0/-5/abc） |
| 7b | `pageNum=9999` 时 Go 返回空，Java 返回末页 | `Page.setTotal` 的 reasonable 回末页 | `Clamp(total)` + `LimitOffset(total)`，分页点接上 total | `TestClampAndSkipQuery`（回末页、pages=0 不改页码） |
| 8 | 客户端 `orderByColumn`+`isAsc` 被 Go 忽略 | `OrderByParser.converToOrderBySql` 替换语句排序 | `manager.orderFor`、`base.orderByFor`、`generator` | `TestOrderByMirrorsPageDomain` + 矩阵 |
| 9 | 空结果 + 非法排序列：Java `200/total=0`，Go `500` | `PageInterceptor:137-145` count=0 时不执行数据查询 | 新增 `SkipQuery`，9 个执行器接入 | 矩阵 `/base/geometry/list?lxbh=G` |
| 10 | `reasonable=false` 的 `pageNum=0/-1/9999` Go 给一整页 | `afterCount` 的 `pageNum>0 && count>startRow`；下界钳位只在 reasonable 时发生 | `SkipQuery` 重写为该条件；`Clamp` 下界加 `Reasonable` 判断；`Offset` 复用 `startRow()` | `TestClampAndSkipQuery` 4 组越界角 |
| 11 | 手拼 SQL 的端点仍忽略客户端排序 | 同 #8（Java 是拦截器级的替换） | `car_free` 4 处、`car_track` 1 处：语句自带的 order by 改由 `orderFor` 传入；语句里没有排序的只在客户端给了才追加 | 定点复测（`incomeStatics?orderByColumn=amount&isAsc=asc` 等） |
| 12 | ops 两个日志 List、`/system/indexmenu/list` 不认 `orderByColumn` | 同 #8 | `ops.orderFor` 新增并接两个 List；`systemaux.queryPage` 去掉「语句里有 order by 就不追加」；`indexmenu` 把语句排序移进 `defaultOrder` | 矩阵（一次报出 24 组 → 修后 0） |
| 13 | `isAsc=bogus` Go 按 asc 正常返回，Java 500 | `getOrderBy()` 原样拼接方向值 | `web.OrderBy` 去掉「非 desc 即 asc」兜底 | `TestOrderByMirrorsPageDomain`（`car_no bogus`） |
| 14 | `reasonable=1/yes/ok/bogus` 时 Go 当作 false（越界页返回空行），Java 仍回末页 | `Convert.toBool(值, null)` 的词表是 `true/yes/ok/1` 真、`false/no/0` 假、**空值与乱值 → null**，再由 `PageDomain.getReasonable()` 回落 TRUE | `web.Page` 的 reasonable 解析改成同一套词表 + 默认回落真 | `TestPageFromRequest` 9 组 reasonable + 矩阵 2 组（`reasonable=1`/`=bogus`） |

## 5. 单测

`internal/web/pagination_test.go`（全部按 §2 的源码行为写）：

| 用例 | 组数 | 钉住的行为 |
|---|---|---|
| `TestClampAndSkipQuery` | 16 | 钳位后的页码、`startRow`、`SkipQuery` 三值同验；含 `!HasPage`、count=0、pages=0、`pageSize=0`、`startRow==total`、reasonable 真假两路 |
| `TestPageFromRequest` | 21 | 缺省 / 只传一个参数 / 非数字回落 / 显式 0 与负数 / 负 pageSize 归一 / `reasonable` 九种取值 / `isAsc` 别名与空值 / `orderByColumn` 原样 |
| `TestPageAlwaysForcesPaging` | 1 | 无参数时 `PageAlways` 仍 1/10 且 `HasPage=true` |
| `TestLimitOffsetKeepsLimit` | 3 | 越界钳位后 LIMIT 不变、`pageSize=0 → LIMIT 0`、不分页时不给 LIMIT |
| `TestOrderByMirrorsPageDomain` | 8+2 | 驼峰转下划线、方向值原样、非法字符忽略、客户端排序覆盖默认排序 |

覆盖率：`go tool cover` 下 `pagination.go` 的 `Page/paramInt/PageAlways/Clamp/SkipQuery/startRow/LimitOffset/Offset/Limit/OrderBy/OrderByWithDefault/toUnderScoreCase`
全部 **100%** 语句覆盖。

## 6. 有意不一致（不修）

| 场景 | Java | Go | 理由 |
|---|---|---|---|
| `orderByColumn=1;drop` 等非法字符 | `UtilException` → `code=500` | 拦掉非法字符后忽略排序，正常返回 | 两边都注入不成功；不让探测请求把列表打成 500。矩阵单列为「已知有意差异」（73 组） |
| `pageSize<0` 且排序列非法 | `pageSizeZero` 分支跳过查询 → 不报错 | 归一成 `LIMIT 0`，仍会执行 SQL → 报错 | 归一为 0 才能保证 `LIMIT ?` 永远是合法 SQL；正常流量不会命中这一角 |
| `/manager/confimfree/concernedList?orderByColumn=totalAmount` | `500`（select 别名 camelCase，外层 order by 认不到） | `200`（Go 别名是 `AS total_amount`） | 对齐要改列别名并牵动 GORM 列映射，收益不足 |
| `DECIMAL(m,2)` 金额字面量 | `67.00` | `67` | 数值相等；逐字面对齐需保留原始标度，涉及上百字段 |
| service 重新聚合的端点（如 `/manager/confimfree/carStatics`） | `PageInfo` 拿到 `ArrayList` → `total = list.size()` | 同（`SkipQuery` 命中时返回 0，而不是 count） | Java 原样，不修正 |

## 7. 复跑（本轮回归）

静态门：`go build ./... && go vet ./... && go test ./...` 全过；`pagination.go` 语句覆盖 100%。

| 专项 | 批次复跑（pF） | 终轮复跑（pG，含 §4 第 14 项） |
|---|---|---|
| 路由清单 | Java 511 全匹配；Go 注册 514（多出 `/healthz`、`HEAD /`、`OPTIONS /`） | 同（未改路由） |
| 默认分页专项 | 比对 91 条，不一致 **0** | 比对 91 条，不一致 **0** |
| 查询参数矩阵 | 1155 组合，差异 **0**，已知有意差异 73 | **1309** 组合（18 种参数组合），差异 **0**，已知有意差异 73 |
| 全量 GET（六模块） | 288 条 URL / 250 一致 / 14 差异 / 24 非 JSON | **逐格相同**（manager 99/80/0/19、base 70/60/6/4、flow 30/30/0/0、system 66/61/4/1、monitor 13/9/4/0、tool 10/10/0/0） |
| 写生命周期（32 资源） | 16 条差异 = 15 条 Java 侧写入缺陷（8 个资源）+ 1 条 `suspiciouscheck` 金额标度 | 15 条差异（全部是 Java 侧写入缺陷的 8 个资源；那条金额标度随测试数据而现，见 §6） |
| Redis 双 DB 隔离 | 24 项断言全通过，失败 0 | 24 项断言全通过，失败 0 |
| `/oss` 与根路径端点 | 不一致项 **0** | 未改，沿用 pF |
| 收尾清理 | `failures=0`（`PARITY*` 行与测试键两端都扫） | `failures=0` |

14 条 GET 差异与 8 个写资源，逐条定性与清单见 `PARITY-2026-11-02.md` §8。

```bash
cd D:/work/IdeaProjects/car-monit-backend-new/car-monit-go
go build ./... && go vet ./... && go test ./...
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_default_page.py
MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/check_query_matrix.py
for m in manager base flow system monitor tool; do
  MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 python -u scripts/parity/compare_get.py \
    --prefix "/$m" --out C:/Users/abelz/AppData/Local/Temp/pF_$m.json --workers 5
done
```
