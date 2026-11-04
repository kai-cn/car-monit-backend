# car-monit-api 联动校验与分层双端对比（2026-11-04）

范围：`vehicleMonitor.baseUrl` 指向的 `D:\work\IdeaProjects\car-monit-api` 服务双端 +
`D:\work\IdeaProjects\car-monit-backend-new` 的 Java/Go 双端。校验顺序按用户要求：
**先 backend 调 api 的接口 → 再 backend 其它业务接口 → 最后框架接口**。

配套工具（本轮新增/改动）：`scripts/parity/compare_xlsx.py`（xlsx 单元格级对比）、
`scripts/parity/dump_templates.py`（EasyPOI 模板真值打印）、`scripts/parity/compare_get.py --tier`、
`scripts/parity/start_java_ref.ps1` / `start_go_ref.ps1`、`scripts/parity/api_pair_check.py`。

---

## 1. 接线与环境

| 进程 | 端口 | Redis | 说明 |
|---|---|---|---|
| car-monit-api Java（pro-business-api-1.0.jar） | 9902 | db0 | 复用已存在进程 |
| car-monit-api Go（`bin/api.exe -c configs/config.verify.yaml`） | 9903 | db1 | 复用已存在进程 |
| backend Java（共享实例） | 9988 | db0 | 被其它会话重启为 `baseUrl=9901`（mock），本轮不依赖它 |
| backend Go（共享实例） | 9989 | db2 | 同上 |
| **backend Java 参照**（本轮自起） | 9987 | db0 | `--vehicleMonitor.baseUrl=http://127.0.0.1:9902` |
| **backend Java 参照** | 9985 | db0 | `--vehicleMonitor.baseUrl=http://127.0.0.1:9903` |
| **backend Go 参照** | 9986 | db5 | `configs` 副本 `config.ref9902.yaml`（api→9902） |
| **backend Go 参照** | 9984 | db6 | `config.ref9903.yaml`（api→9903） |

要点：
- api 双端与 backend 双端都**共用 MySQL 3307/carmonitdb**，Redis 各占不同 db（0/1/2，参照实例另占 5/6）。
- 9988 由别的会话重启成了 `baseUrl=http://127.0.0.1:9901`（mock）。不改别人的进程、不改被打包的 jar，
  改为**自起参照实例 + 命令行覆盖** `--vehicleMonitor.baseUrl`，并让 `pp.py` 支持
  `PARITY_JAVA` / `PARITY_GO` 环境变量。参照实例跑的是本地重建的二进制，避免"源码已改、进程还是旧的"。
- 交付接线（Java→9902、Go→9903）与钉版接线（双端同指一个 api）都跑，钉版用来**归因**：
  钉版 0 差异 ⇒ 交付接线的残余差异来自 api 双端自身，而不是 backend。

---

## 2. 第 1 档：backend 调 api 的接口（14 条 URL）

档位定义在 `compare_get.py` 的 `API_ROUTES`（`/base/feeGantry|feerecords|feestationexit|snapshotflow`、
`/manager/cartrackinfo/{listByCarId,listByCarByTime,carSnapShot}`），路由清单取自 Go 运行态注册日志。

| 接线 | total | 一致 | 差异 | 非 JSON | 备注 |
|---|---|---|---|---|---|
| A 双端→api Java 9902 | 14 | 12 | **0** | 2 | 2 条 xlsx 另做单元格对比（0 差异） |
| B 双端→api Go 9903 | 14 | 12 | **0** | 2 | 同上（含 3 行真实数据的导出） |
| C 交付接线 | 14 | 11 | 1 | 2 | 唯一差异 `/base/feerecords/1`：Java 侧 500、Go 侧 200 |

- **A/B 都是 0 差异** ⇒ backend 的 Forest 转发层（参数拼装、`TableDataInfo` 反序列化、
  裸数组导出、`dropNullMembers`、错误传播）与 Java 等价。
- C 的 1 条差异完全归因到 api 双端：api Java `/base/feerecords/list`、`/base/feerecords/{id}` 直接 500
  （见 §4），Go 端 200。backend 只是把上游状态透传，两端表现一致。
- 「空表让数据比对失明」在这一档尤其明显：`/base/feerecords/list` 不带 `inApplyTime1/2` 时
  两端都是 `total=0`（Java 的门禁条件），必须补时间参数才有真实数据；补上后
  Java(→9902) 与 Go(→9902) 仍然一致（都是上游 500 的同一份错误信封），
  Java(→9903) 与 Go(→9903) 都是 `total=1016` 的同一份数据。

## 3. 第 2 档：其它业务接口（185 条 URL）

`--tier business` = `/manager`、`/base`、`/flow` 里不属于第 1 档的端点。

`total=185 一致=162 差异=2 非 JSON=21`

| 差异 | 结论 |
|---|---|
| `/base/fitting/list` | Java 500（Mapper 引用实体上不存在的 `id` 属性）vs Go 200 —— Java 侧缺陷，已记录于 PARITY-2026-11-02 §8.2 |
| `/base/geometry/syncAllGeometry` | 两端都 500，缺表 `geometry_copy1`，只有错误文本形态不同 |

21 条"非 JSON"全部是 xlsx 附件流。旧的 `compare_get.py` 只能把它们标成 non-json 就放过，
本轮用 `compare_xlsx.py` 落到单元格：**修复前 20 个端点里有 18 个存在差异，合计 19633 格；
修复后 21 个端点全部 0 格差异**（含 `/base/feerecords/export` 的真实数据页）。详见 §5。

## 4. 第 3 档：框架接口（95 条 URL）

`--tier framework` = `/system`、`/monitor`、`/tool`、`/oss`、`/common`、`/v3`、`/swagger`。

`total=95 一致=82 差异=11 非 JSON=2`，逐条归类：

| 端点 | 类别 |
|---|---|
| `/monitor/cache`（1） | 运行态：Redis `commandStats` 是各自实例的累计计数 |
| `/monitor/online/list`（1） | 运行态：会话各写自己的 db，行数/`loginTime`/`sessionId` 必然不同 |
| `/monitor/server`（1） | Java 500（JNA 版本冲突）vs Go 200 —— Java 侧缺陷 |
| `/monitor/jobLog/1`（1） | Java 侧 `@GetMapping` 少了路径变量 ⇒ 恒 500 —— Java 侧缺陷 |
| `/system/upgradeInfo/{list,newest,export,1}`（4） | 两端都 500，缺表 `sys_upgrade_info`，错误文本形态不同 |
| `/oss/bucket`、`/oss/bucket/1`、`/oss/object/1/1`（3） | 两端都 500；MinIO 端点不可达，Java 是 SDK 连接超时文本，Go 是 net/http 文本或 minio-go 的桶名校验文本 |
| `/common/download/resource`、`/system/file/1/1` | 非 JSON：两端都是 200 空体，逐字节一致 |

框架侧另有一处**行为差异已修**（`/common/download`，见 §6.3），修完这一条本档差异从 12 降到 11。

---

## 5. 导出层（本轮最大的盲区）

`/manager/*` 的导出在 Java 侧不是 `ExcelUtil` + `@Excel`，而是 **EasyPOI 模板导出**
（`ruoyi-admin/src/main/resources/templates/export/*.xlsx`）：列名、列序、列数全部来自模板文件，
实体上的 `@Excel` 注解对这些端点是死代码。模板第 2 行的 `{{$fe:entitylist t.a|t.b|...}}` 才是真值，
`dump_templates.py` 用来打印它。

单元格渲染规则（由模板导出路径反推，逐条被线上一致性验证）：

| 规则 | Java 表现 | Go 修复 |
|---|---|---|
| 模板引用了实体上不存在的属性 | 空格子（`String.valueOf` 缺失属性 ⇒ 空） | `exportCol` 只给 Title 不给 Field ⇒ 空格子 |
| `*string` 等指针字段 | 值本身 | `buildStaticWorkbook` 对每格过一遍 `plainValue`，杜绝 `0xc000…`/`&lt;nil&gt;` |
| `java.util.Date` 且模板不做格式化 | `Thu Aug 21 00:00:00 CST 2025` | `exportCol.JavaDate` ⇒ `javaDateText()` |
| `java.sql.Timestamp`（`BasePlusEntity.createTime`） | `2026-02-03 16:19:19.572` / `…27.0` | `exportCol.Stamp` ⇒ `stampText()`（小数秒去尾零、至少 1 位） |
| `decimal(x,2)` ⇒ `BigDecimal` | `225.30` | `exportCol.Money` ⇒ `moneyText()` 恒两位 |
| 聚合金额（`BigDecimal.ZERO` 起算再 add） | 没累加到任何行时是 `0`，累加过是 `x.xx` | `moneySumText()` |
| 字典翻译 | `CommonUtil.isNull(map.get(code))` ⇒ **未命中给空串** | `exportCol.BlankOnMiss` |
| `exceptrecord` 的字典翻译 | 控制器用 `containsKey` 守卫 ⇒ **未命中原样** | `dictOrRaw()`（与上一行刻意不同，两处都有据） |
| 超 32767 字符的格子 | POI 拒绝 ⇒ 写出「有样式无值」空格 | `normalizeRow` 置空（excelize 原本是静默截断） |
| 三行静态表头（标题行 + 列名行 + 副表头行） | 模板原生 | 新增 `buildStaticWorkbook(sheet, static, rows)` |

各端点的具体修复：

| 端点 | 修复 |
|---|---|
| `/manager/suspiciouscheck/export` | 列集整组换掉：Java 打印 车牌号/规则名称/预警范围/通知/通知方式/通知人员/所属站/所/备注，除车牌号与备注外实体都没有该属性 ⇒ 空列；Go 原来打印的是 `concernedList` 的 6 列 |
| `/manager/gantrycar/export` | 补 出口门架/出口时间/交易类型/收费金额 4 个空列，删掉 Java 模板没有的 抓拍图片；`通行时间` 改 `Date.toString()` |
| `/manager/gantrytrade/export` | 11 列 ⇒ 15 列（补 通行标识/应缴金额/差额/逃费类型/管理中心名称，删掉 Java 从未引用的 收费类型/金额）；两个时间列改 `Date.toString()` |
| `/manager/warningrule/export` | A 列标题与字段都错（`预警规则`/`ruleName` ⇒ `预警对象`/`noticeRangeAnme`） |
| `/manager/splitrecord/export` | 标题 `通行标识` ⇒ `通信标识`；并复刻 Java 的错键：`pass_type` 字典用 `carVehicle` 去查 |
| `/manager/whiteinfo/export` | 字典未命中 ⇒ 空串（`plate_color` 里没有值 `2`，Java 给空、Go 给了 `2`） |
| `/manager/querylog/export` | 标题 `模块说明`/`查询时间` ⇒ `模块菜单`/`创建时间`；时间戳带小数秒；超长查询条件置空 |
| `/manager/carinfo/export` | 逃费类型列不再挂 `Dict`（此前 transform 拿到的是标签而不是原码，二次映射必然落空 ⇒ 整列空）；金额两位小数；字典未命中给空 |
| `/manager/carwarning/export` | 12 列对齐模板（F 列是 `最新经过位置`=`gantrytStation`，不是 `最新经纬度`；补 `备注`）；金额两位小数 |
| `/manager/exceptrecord/{export,exportOrgId}` | 16 列 ⇒ 3 静态表头行 + 21 列（`序号`=行号、`carNoQuery` 恒空、金额列按模板落在 N/Q/T） |
| `/manager/suspicious/{export,exportHistory}` | 列集对齐 `carSuspicious.xlsx`（C 列是**车种**不是车型，`通行标识` 不做字典翻译 —— Java 把那行注释掉了）；`txTime/txAddress/mjTime/mjAddress` 按「A至B」两段独立拼接；**补上 Java 的 `startPage()`**（原来 Go 导出全量 63 行、Java 30 行） |
| `/manager/confimfree/export` | 11 列 ⇒ 模板 9 列（Java 翻译了车型/车种但模板不打印）；标题 `司机姓名`/`补缴金额（元）` ⇒ `司机名称`/`拆分金额（元）`；金额两位小数；录入时间带小数秒 |
| `/manager/confimfree/exportConcernedList` | 去掉 Go 自己加的分页（Java 未 `startPage`，全量 31 行）；金额两位小数 |
| `/manager/confimfree/exportCarStatics` | 15 个标题按模板逐字替换（`入口少轴车辆数`/`大车小标车辆数`/`假冒其他优免车车辆数`/`合计数量`…）；去掉分页 |
| `/manager/aduitfree/exportIncomeStatics` | 标题 `车辆数`/`金额（元）` ⇒ `车辆数量`/`逃费金额（元）`；聚合金额用 `moneySumText`；去掉分页 |
| `/manager/aduitfree/exportIncomeDetailList` | 去掉分页；金额两位小数；录入时间用 `Timestamp.toString()`；用 `?orgId=25367` 才拿得到 25 行真实数据（默认查询两端都是 0 行） |
| `/base/gantry/export` | 不是代码差异：Java 读 Redis 键 `gantry_list`（db0，仓库里没有写入点，是外部快照，1526 行），Go 缓存缺失时回源查库（1558 行）。把同值快照 `COPY` 到参照实例的 db 后**逐格 0 差异**，验证完已删除该键（db0 原键未动） |

## 6. 框架层修复

1. **`/base/feerecords/export` 写出 `0xc000b2f560`**：`enrichFeeRecords` 把 GORM 模型的 `*string`
   放进 row map，JSON 编码会自动解引用所以列表看不出问题，xlsx 写手用 `fmt.Sprint` 就露出来了。
   `base/excel.go` 的 `cellValue` 增加 reflect 解引用。
2. **`/oss/object/{bucket}/{object}/{expires}` 恒 500**：原来用 minio-go 的 `PresignedGetObject`，
   它会先向端点发 `GET /{bucket}/?location=` 取区域，MinIO 不可达时整条链路 500；而 Java 用的是
   AWS SDK v1 的 `generatePresignedUrl`，**离线签名、从不联网**。新增 `systemaux/oss_presign.go`
   按 SigV4 查询串签名复刻（区域 `us-east-1` 即 Java 未配置时的默认值，返回 URL 的 credential scope 印证），
   参数顺序也照抄 Java 下发的形态。修复后两端 host/path/参数集/credential scope 全等，
   只有 `X-Amz-Expires` 相差 1 秒（Java SDK 用第二次 `currentTimeMillis` 反算，本实现同理，
   86399/86400 都出现过）—— 签名本身含时间戳，不做逐字节比对。
   同时 Go 不再因桶名长度提前拒绝：`/oss/object/1/1/1`、`/oss/object/ab/x/1` 现在和 Java 一样返回成功。
3. **`/common/download` 对已登录请求返回 200**：Java 的 `SecurityConfig` 把它配成
   `antMatchers("/common/download**").anonymous()`，Spring 的 `AuthenticatedVoter` 对
   `IS_AUTHENTICATED_ANONYMOUSLY` 只认**匿名令牌** ⇒ 带有效 token 的请求 403（带无效 token 反而 200）。
   实测：`good=403 bogus=200 anon=200`。Go 侧把 `anonymousOnly` 从 systemaux 局部函数提到
   `middleware.AnonymousOnly(app)`，判定条件从"有没有 Authorization 头"改成"令牌能否解析出登录态"
   （`/system/notice/view/{id}`、`/system/file/view/{ids}/{file}` 同样受益：此前带无效 token 会被误判 403），
   并挂到 `/common/download`。三个端点现在都是 `good=403 bogus=200 anon=200`。
   注意 `Auth` 只挂在 `reg.Authed` 上，所以这个中间件自己解析一次 token。

## 7. api 双端自身的不一致（第 1 档残余差异的根因）

`api_pair_check.py` 直连 9902/9903 比对 backend 会用到的 11 条列表路径 + 8 条详情路径：

| 路径 | Java(9902) | Go(9903) |
|---|---|---|
| `/base/feerecords/list` | **500** | 200，`total=1016` |
| `/base/snapshotflow/list` | `total=900` | `total=251`（分表枚举不同） |
| `/base/snapshotflow/listToExport` | `/6/carcolor=红色` | `未知`（车颜色翻译） |
| 其余 8 条列表 + 8 条详情 + `earliest-time` | 一致 | 一致 |

观察项：某一轮 `/base/gantry|org|fwqjcxx/listAll` 在 Java 侧只返回 3 条（正好等于当轮 backend 测试用的
`pageSize=3`），随后多次复测都是全量 1526/481/218 且与 Go 端逐字节等长 —— 未能复现，
记为 api 侧的一次抖动，不作为结论。

## 8. 门禁与回归（本轮最后一次跑）

| 项 | 结果 |
|---|---|
| `go build ./... && go vet ./... && go test ./...` | 通过 |
| `gofmt` | 本轮改动文件已格式化 |
| `check_startpage_map.py` 六类静态核对 | 全 0（含新改的 5 个导出分页点） |
| `check_default_page.py` | 91 条比对，不一致 0 |
| `check_query_matrix.py` | 1617 组合，差异 0 |
| `compare_xlsx.py` 21 端点 | 单元格差异 0 |
| `check_redis_isolation.py` | 24 项断言全通过，清理 `failures=0`（跑在交付接线 9988/9989 上；参照实例因为另占 db5/db6，用它跑这项会误报） |
| `check_oss.py` | 不一致项 0 |

## 9. 已知差异（不改）

1. Java 侧框架/库缺陷：`fitting/list`、`upgradeInfo/*`（缺表）、`geometry/syncAllGeometry`（缺表）、
   `monitor/server`（JNA）、`monitor/jobLog/{id}`（缺路径变量）、`/base/cdc/config`
   （控制器 `AjaxResult.success(cdcConfig)` 直接序列化 CGLIB 代理，写到一半溢出错误页，
   响应是**非法 JSON**：54464 字节尾部追了一个 `{"msg":"Type definition error…","code":500}`，
   HTTP 仍是 200。Go 返回 400 字节的干净配置，前缀 `data.kafka` 段与 Java 一致）。
2. api 双端自身的 3 条不一致（§7）—— 属 `car-monit-api` 项目，backend 只如实透传。
3. 运行态数据：`monitor/cache`、`monitor/online/list`。
4. 同为 500 时的错误文本形态（`/oss/*`、`upgradeInfo/*`）。
5. `/base/gantry/export` 的行集取决于 Redis 快照 `gantry_list`（Java 读缓存、Go 缓存缺失时回源）。
   交付环境两端共用同一 Redis 键时逐格一致（已用复制快照的方式验证）。
6. `ExcelUtil` 型导出（`/system/*`、`/monitor/*`）返回的是"文件名落在 msg 的 AjaxResult"，
   落盘文件内容不在本档对比范围内 —— 本轮做的是 EasyPOI 附件流的 21 个端点。

## 10. 复现

```bash
cd D:/work/IdeaProjects/car-monit-backend-new/car-monit-go
# 参照实例（PowerShell 起，命令行覆盖 baseUrl；pp.py 用环境变量选两端）
powershell -NoProfile -File scripts/parity/start_java_ref.ps1 -Port 9985 -ApiUrl http://127.0.0.1:9903
powershell -NoProfile -File scripts/parity/start_go_ref.ps1 -Cfg $TEMP/config.ref9903.yaml -Log $TEMP/go-ref-9984.log

export MSYS2_ARG_CONV_EXCL='*' PYTHONIOENCODING=utf-8 PARITY_JAVA=http://127.0.0.1:9985 PARITY_GO=http://127.0.0.1:9984
python scripts/parity/compare_get.py --tier api --out $TEMP/t1.json --log $TEMP/go-ref-9984.log
python scripts/parity/compare_get.py --tier business --out $TEMP/t2.json --log $TEMP/go-ref-9984.log
python scripts/parity/compare_get.py --tier framework --out $TEMP/t3.json --log $TEMP/go-ref-9984.log
python scripts/parity/compare_xlsx.py "/manager/carinfo/export?pageNum=1&pageSize=30"
python scripts/parity/dump_templates.py carSuspicious        # EasyPOI 模板真值
python scripts/parity/api_pair_check.py                      # api 双端直连比对（归因用）
```

`compare_xlsx.py` 会先裁掉"两端都为空的尾部整行/整列"—— POI 习惯多写一列空样式列、
EasyPOI 空列表时多写一行空格，这不是差异；带值的列不会被裁掉。
