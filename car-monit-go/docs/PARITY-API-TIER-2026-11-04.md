# car-monit-api 联动校验与分层双端对比（2026-11-04）

范围：`vehicleMonitor.baseUrl` 指向的 `D:\work\IdeaProjects\car-monit-api` 服务双端 +
`D:\work\IdeaProjects\car-monit-backend-new` 的 Java/Go 双端。校验顺序按用户要求：
**先 backend 调 api 的接口 → 再 backend 其它业务接口 → 最后框架接口**。

配套工具（本轮新增/改动）：`scripts/parity/compare_xlsx.py`（xlsx 单元格级对比）、
`scripts/parity/compare_export_all.py`（全部 58 条 `/export` 路由，含 ExcelUtil 落盘型）、
`scripts/parity/dump_templates.py`（EasyPOI 模板真值）、`scripts/parity/dump_excels.py`（`@Excel` 注解真值）、
`scripts/parity/compare_get.py --tier`、`scripts/parity/start_java_ref.ps1` / `start_go_ref.ps1` / `start_api_java.ps1`、
`scripts/parity/api_pair_check.py`；落格规则集中在 `internal/excelx`（带单测）。

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

更大的口子在框架系：`/system/*`、`/monitor/*` 等导出的响应只是"文件名落在 msg 的 AjaxResult"，
光看 JSON 完全看不出内容差异 —— 这部分连同上面的附件流，一起放进 §6.5 的 58 条 `/export` 全量口径。

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

## 6.5 ExcelUtil 落盘型导出：第二轮补上的更大盲区

第一轮把 21 个 EasyPOI 附件流端点做完后，还剩一个更大的口子：RuoYi 框架系（`/system/*`、
`/monitor/*`、`/base/*` 部分、`/manager/*` 部分、`/flow/*`）的导出**不是附件流**，
而是 `ExcelUtil.exportExcel(list, sheet)` 把文件写到 `ruoyi.profile/download`、
只把文件名放在 `AjaxResult.msg` 里返回。`compare_get.py` 看到的是一句 JSON，`compare_xlsx.py`
也够不着 —— 于是新增 `compare_export_all.py`：从 Go 运行态注册日志里取出**全部 58 条 `/export`
路由**，两类形态一起覆盖（附件流直接比字节；落盘型按 msg 里的文件名去 `D:/ruoyi/uploadPath/download`
读两端文件逐格比，比完删掉这两个本次生成的文件）。

结果：`58 条 = 22 附件流 + 33 ExcelUtil 落盘 + 3 非 xlsx`，修复前 **33 条落盘型里有 12 条存在差异**，
含最大的一处 **251011 格**。三条新的落格规则（都是双端对拍反推 + Java 源码印证出来的）：

| 规则 | Java 出处 | 表现 | 修复 |
|---|---|---|---|
| XML 1.0 非法字符写成 `?` | POI/XSSF 序列化（`ExcelUtil` 只调 POI） | `sys_oper_log.json_result`、`sys_job_log.exception_info` 里夹着 U+001A/NUL：Java 落 `?`，excelize 落 U+FFFD | `excelx.Sanitize`，operlog 496 格 + jobLog 4 格清零 |
| 文本以 `= - + @` 开头前补 TAB | `ExcelUtil.java:961-977`（CSV 公式注入防护，仅 STRING/TEXT 分支） | `sys_user.tenant_id=-1` 在 Java 的 xlsx 里是 `"\t-1"`（`@Excel` 没写 cellType ⇒ 默认 STRING） | `excelx.UtilCell`（写手层）+ `excelx.TextValue`（调用点把数字落成 Java 的 STRING 形态） |
| `readConverterExp` / `dictType` **未命中给空串** | `ExcelUtil.convertByExp:1220-1247`、`DictUtils.getDictLabel:82-112`（兜底是 `stripEnd("")`） | 工程里大量注解是代码生成把 Javadoc 括号内容切坏的残骸（`name="收费站编号" readConverterExp="内=部"`），Java 因此**整列空**；Go 原来回退成原值 | `excelx.ConvertByExp`（separator 默认是 `,` 不是 `=`！），base/manager/ops/system/quartz 四个写手全部改为未命中给空 |

取值优先级也照抄了 `ExcelUtil.java:1085-1108`：`dateFormat` → `readConverterExp` → `dictType` →
`BigDecimal+scale` → `handler` → 原值。`base/exportCol` 因此新增 `Exp` 字段（原来没有，
`exports.go:5` 那句"readConverterExp 只影响导入"的前提是错的）。

按 @Excel 注解真值重建的列集（`dump_excels.py` 打印 Java 列序；父类 `BasePlusEntity` 经确认
**没有任何 @Excel**，所以 Java 列集里没有 createTime，Go 原来加的"创建时间"列是凭空多出来的）：

| 端点 | Java 列数 | Go 原列数 | 修复要点 |
|---|---|---|---|
| `/manager/busstest/export` | 17 | 6 | 补 部门id/人员id/申请时间/时间时分秒/附件/流程key/流程实例ID/流程申请ID/流程状态/审核时间/备用字段1/2；`金额` 两位小数；`状态` 用 `Exp:"0=正常1停用"`；删掉 Java 没有的创建时间 |
| `/manager/aduitfree/export` | 14 | 7 | 补 确认补缴id/车辆id/处理单位id/处理人员ids/处理人员/备用字段1/2；**车型/车种 Java 无字典翻译**（原来挂了 `Dict` 输出标签）；`拆分金额` 两位小数且标题不是"处理金额（元）" |
| `/manager/routedetail/export` | 25 | 10 | 整组换成注解列；第 12 列标题含 **Kangxi 部首** `⾏`(U+2F8F)/`⽅`(U+2F45)，不是 行/方，逐字照抄 |
| `/manager/cartrackinfo/export` | 20 | 9 | 补 车辆id/设备类型/接收时间/抓拍图片/管理中心路段id/行驶轨迹id/行驶轨迹josn/备用字段1/2/状态；标题 `车道编号`/`管理中心路段名称`/`维度`（不是"纬度"）；末尾两列是注解里重复声明的经度/维度 |
| `/manager/feerecord/export` | 17 | 10 | 补 车辆id/入口站id/出口站id/异常流水id/备用字段1/2；`交易类型` 用注解里的残缺 `Exp`；`收费金额` 两位小数；删掉两处 `Dict` |
| `/manager/carsuspiciousback/export` | 43 | 43 | 列名列序本来就对；只差 `车牌颜色`/`逃费类型` 两个残缺 `Exp`（键是"字"，除值恰为"字"外恒不命中 ⇒ Java 整列空） |
| `/base/toll/export` | 23 | 23 | 三列（收费站编号/收费站名称/国网编号）加 `Exp:"内=部"` ⇒ 与 Java 一样整列空；真数据在模板后半段的重名列上 |
| `/base/org/export` | 16 | 16 | `是否是养护类` 加 `Exp:"1=：是，0否"`（全角逗号不算分隔符 ⇒ 文案就是 `：是，0否` 这个怪串） |
| `/base/config/export` | 13 | 13 | 三列加 `Exp:"分=离"`/`"分=钟"` ⇒ Java 恒空 |
| `/base/geometry/export` | 5 | 5 | 超 32767 字符的格：POI 抛异常被 `ExcelUtil.addCell` 的单元格级 catch 吞掉 ⇒ **整格留空**，而 excelize 是静默截断到 32767（`paths` 列 149816 字符那一格） |

`internal/excelx` 现在是这套规则的唯一出处，并用 `cell_test.go` 钉住（未命中给空、分隔符是逗号、
全角逗号不参与拆分、指针解引用、非法字符→`?`、超长置空、TAB 前缀只对文本生效、
`TextValue` 的 `-1→"\t-1"` 与 `0→"0"`）。

**更正第一轮的口径**：`/monitor/operlog/export` 的差异不是"自生成审计行"造成的。
按 `列A 操作序号` 建索引对齐后：只在一端存在的行 = 1（就是本次调用自己写进去的那条），
其贡献的**格数为 0**；496 个差异格全在 `列M 返回参数`，是上面第一条 `?` 规则。
`/monitor/logininfor/export` 则连自记录噪声都没有（导出写的是 `sys_oper_log`，不是 `sys_logininfor`），
两端各 3732 行、共同 id 差异 0。
`/base/gantry/export` 的口径也要精确化：Java 读 Redis 快照 `gantry_list`、Go 缓存缺失时回源查库，
两者只在"库与快照不一致"时才有差异 —— 本轮内 `ods_szdn_gantry` 实测回到 1526 行（与快照同），
两端因此直接对齐；上一轮的 1558 vs 1526 已用"把快照复制进 Go 的 db 后逐格 0 差异"证明过是数据源差异。

`/manager/suspicious/exportAbnormalPassage`（Word 模板 `carSuspicious.docx`）顺手对齐了正文：
标签改成模板原文（车辆信息 / 通行异常 / 入站口 / 出站口 / 起始门架 / 起始经过时间 / 终止门架 /
终止经过时间 / 收费金额（元） / 应缴金额（元） / 差额（元） / 核实信息 / 核实结果 / 图片 / 证据材料），
金额按 `BigDecimal.toString()` 落两位（checkList 为 null ⇒ 空串，空列表 ⇒ `0`），
`车种` 复刻 Java 的"字典未命中回落原值"。poi-tl 的图片内嵌仍不做（`susImg1..7` 只留标题行）。

## 6.6 Excel 导入层（本轮收尾的三个上传端点）

对拍工具：`scripts/parity/compare_import.py`（同一份 xlsx 传两端，比响应体 + 落库对照）、
`scripts/parity/compare_upload_errors.py`（10 类畸形请求 × 3 端点 = 30 条错误形态）、
`scripts/parity/dump_local_xlsx.py`（打印本地 xlsx 每一行，用来核对真实模板的表头）。
参照对：Java 9987 / Go 9982，两端都挂 api 9902，Redis db0 vs db8。
两端共用一个 MySQL，所以每端各用自己的标记值（`PARITY_J*` / `PARITY_G*`），比对时归一成 `<PARITY>`。

| 端点 | Java 解析器 | 表头来源 | 数据起始行 | 错误对象 |
|---|---|---|---|---|
| `/system/user/importData` | `ExcelUtil.importExcel`（`WorkbookFactory` 按内容嗅探，**不看后缀**） | SysUser 的 `@Excel(name)` | 第 2 行 | 无，逐行拼中文消息 |
| `/manager/carinfo/import` | `ImportSysUtil` + `ImportUtil.importExcel` | `CarInfoController.initList()` 8 列 | 第 2 行 | `{rowNo,colName,message}` |
| `/manager/exceptrecord/import` | 同上（`colVdaExcel08` / `dataRtnExcel08`） | `initListTwo()` 21 列（含 8 个空标题） | 第 4 行 | 同上 |

### 通用逐列校验：新文件 `internal/modules/manager/import_validate.go`

`ImportUtil.importExcel:43-107` 的规则表原样搬到 `validateImportRow`：`1 必填`、
`2 小数`、`3 整数`、`4 年月日`、`5 身份证`、`6 年月`、`7 数值`、`8 年月日时分秒`，
消息逐字 `不能为空 / 不是小数 / 不是正整数 / 日期格式（年-月-日）不正确 / 身份证号码不正确 /
日期格式（年-月）不正确 / 不是数值 / 日期格式（年月日时分秒）不正确`。四处容易抄错：

- Java 用 `Pattern.matches`（全串匹配）⇒ 没写锚点的 `eLtime2` 在 Go 里要补 `^$`；
  `elTimeYM` 的 `\- \/ \.` 在 Go 正则是非法转义，改成裸字符。
- 规则 token 逐个一轮，`2..8` 之间是 else-if 链 ⇒ 值 `"x"` 配 `"2,3"` 会报 **2** 条，
  而一个 token 内只报 1 条（`import_validate_test.go` 把这条钉住了）。
- `1` 独立于非空判断；2..8 只在值非空时才查 ⇒ 「必填 + 小数」的空格只报 `不能为空`。
- 行号来自 `getErrorBO(index + 1, ...)` 内部又 `row + 1` ⇒ `rowNo = 数据行序号 + 2`，
  与表格真实行号无关（`ImportSysUtil.java:190-197`）。两个阶段的错误都用它，
  所以顺序是「所有行的格式错，全通过才轮到字典/业务错」，不是按行归类。

### `/manager/exceptrecord/import`

- 真实模板 `templates/down/importCarExcept.xlsx` 的前三行实测为：标题行 / `initListTwo` 表头 /
  子表头（`一级类型|二级类型|省内|省外|小计…`）。Java 拿**同一份** `initListTwo` 去比第 2、3 行
  （`CarExceptRecordController.java:353-368`，`initListThree()` 根本没被调用），
  所以只有第 2 行能命中；Go 用 `sameHeader(rows[1]) || sameHeader(rows[2])` 复刻。
- `dataRtnExcel08(sheet, strName, strNum, 3)` 的 `strNum={0,11,12,14,15,17,18,19,21}` 是合并单元格列，
  读值时跳过；这些列在 `initListTwo` 里的属性名也都是空串 ⇒ 跳过与否不影响结果，Go 按列位直取。
- 车种**不取表格里那一列**：由（经 `car_type_change` 转换后的）车型推导，
  1-4→`1`、11-16→`2`、21-26→`3`、其余 `99`（`:438-474`）。
- 收费站查不到时 Java 不碰 `in_station_id` ⇒ 列保持 NULL；Go 之前写空串，已改为不下推该列。
- 第三段写库前有 `isExitsTime` 区间查重（同车牌、区间重叠、排除自身 id），命中就 `return error` ——
  而控制器**忽略返回值**，净效果是「这一行不写库、响应里照样带着它」。抽成 `exceptTimeOverlap`，
  `exceptSave` 一并复用，条件为空时和 XML 的 `<if>` 一样整条不下推。
- 审计列按 `BasePlusEntity` 的 `@TableField(fill=...)`（`MyBatisPlusHandlerConfig.java:20-86`）：
  `insertFill` 只填 `create_by/create_time/eps_id/tenant_id`，**不填** update_*；
  `updateFill` 只填 update_*，且 MP 会把填进去的值写回实体 ⇒ 新增行的响应有 `createBy/createTime/epsId/tenantId`
  而没有 `updateBy`，更新行相反。另外该 handler 的 tenant 段把变量抄错（`if (epsId == null)`），
  于是 `car_except_record` 拿到 `tenant_id=-1`，而 `car_info` 因为 `doImport` 先显式设了 `epsId` 反而拿不到 ——
  两处都照抄，不做"修正"。
- `supplementaryStatus` 是域对象的字段初值 `"0"`（`CarExceptRecord.java:136`），响应体一直带着。
- 车牌列会被 `split("_")` 拆成「车牌_车牌颜色」⇒ 对拍脚本在这一端点的标记值不能含下划线，
  否则两端都落到 `car_no='PARITY'`，共用库又互相看见了（这一坑已踩过一次）。
- 时间列（规则 `1,8`）必须按 **本地时区** 解析：`fastjson` 用 JVM 默认时区，DSN 又带 `loc=Local`，
  Go 这边若用 `time.Parse` 拿到 UTC，入库钟点整体 +8 小时。改用 `web.ParseDate`
  （内部是 `ParseInLocation(..., time.Local)`），并在单测里按 Unix 值钉住。

### `/manager/carinfo/import`

- 两段式（`CarInfoController.java:207-295`）：先把所有行过一遍格式校验，**全通过**才进字典校验段。
- 与 `updateSupport` 无关；`CarInfoServiceImpl.doImport:197-217` 的新增/更新**两个分支都** stamp
  `updateBy/updateTime`，而响应体就是这批就地改过的对象 ⇒ Go 之前只在新增分支 stamp，
  「重复上传」那一轮少两格（就是本轮开头的那条差异）。
- 逃费类型：`CommonUtil.deleteEnd` 只削**一个**尾逗号，`split(",")` 保留中间空串，
  空串查不到字典照样报 ` 逃费类型不存在,请在字典菜单维护！`。
- MP 默认字段策略 NOT_NULL ⇒ null 属性不进 INSERT/UPDATE 列清单。新增 `mpNonNullCols` 剔掉 nil 指针，
  否则轴数/逃费金额为空时更新分支会把库里的旧值擦成 NULL。

### `/system/user/importData`

Java 侧三处结构细节决定了本轮 4 条错误形态的归属：

- `SysUserController.importData:155-161` 既不判后缀也不判空，`file` 为 null 时
  `GlobalExceptionHandler` 拿到 `e.getMessage()==null` ⇒ `{"msg":null,"code":500}`（已对齐）。
- `ExcelUtil.java:353` 以 `sheet.getLastRowNum() > 0` 为闸：只有表头 ⇒ 空列表 ⇒
  `importUser` 报「导入用户数据不能为空！」；有数据行才进解析块。
- `ExcelUtil.java:496` 结尾**无条件** `list.add(entity)`：表头一个 `@Excel` 标题都对不上时 `entity`
  始终为 null，`importUser` 的 catch 里又一次 `user.getUserName()` 抛 NPE ⇒ 又回到
  `{"msg":null,"code":500}`。Go 用「标题全不匹配 ⇒ 空消息错误」复刻（`system/excel.go`）。
- 为此 `readXlsxRows` 从 `GetRows` 换成 `Rows` 迭代器：`GetRows` 会裁掉整行空值的行，
  行号与 POI 的 `getRow(i)` 对不上；迭代器逐行给出、缺行补 nil。
  `endOfImportSheet` 因此只在「行不存在」或首格是 `break/结束` 时收尾，
  「行在、值全空」仍按 Java 送去逐列校验（`ExcelUtil.isRowEmpty:1625-1640` 看的是单元格类型，
  空字符串的 STRING 单元格不算空行）。

### 结果

| 用例 | 响应 | 落库对照 |
|---|---|---|
| `/system/user/importData` 新增/重复/updateSupport + 重复上传 | 除「新增」是 Java 已知缺陷外逐字一致 | Java 0 条 / Go 1 条（同一缺陷） |
| `/manager/carinfo/import` 合法 + 重复上传 | 一致（补上 `updateBy/updateTime` 后） | 1 / 1，差异 0 |
| `/manager/carinfo/import` 规则 1/3/2 报错 | 一致（3 条错误逐字同、顺序同） | 不写库 |
| `/manager/exceptrecord/import` 日期不满足规则 8 | 一致（2 条） | 不写库 |
| `/manager/exceptrecord/import` 合法 + 重复上传 | 一致 | 1 / 1，差异 0；列值逐项核对（`tenant_id=-1`、`in_station_id=NULL`、钟点不偏移、金额/车种推导） |
| 30 条上传错误形态 | 28 条一致 | 2 条已知（见 §9） |

**多行用例**（单行覆盖不到的跨行分支，全部一致）：

| 用例 | 覆盖的分支 | 实测 |
|---|---|---|
| 流水 4 行（时间倒挂 / 收费>应缴 / 字典查不到） | 第二段业务校验的**跨行顺序**与 `rowNo = 序号+2` | 3 条错误 `rowNo 3/4/5`，两端逐字同 |
| 流水 2 行同车牌区间重叠 | `isExitsTime` 命中 ⇒ 控制器忽略返回值 | 响应带 2 行、库里只有 1 行，两端同 |
| 流水「数据行 + 结束行 + 数据行」 | `dataRtnExcel07/08` 的首格 `break/结束` 终止 | 只读第一行，落库 1 条，两端同 |
| 车辆 3 行（中间行轴数非法） | `importList` 只在 `errorList` 仍为空时追加 ⇒ 后续合法行也不入库；第二段字典校验整段跳过 | 只有 1 条 `轴数 不是正整数`，两端同 |
| 车辆 105 行全非法 | `errorList.size() > 100` 的提前 break | 两端都停在 **101 条**错误、`rowNo 2..102`（每行 1 条），第 103~105 行根本不被校验 |

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
| `go build ./... && go vet ./... && go test ./...` | 通过（含新增 `internal/excelx` 规则单测） |
| `gofmt` | 本轮改动文件已格式化 |
| `check_startpage_map.py` 六类静态核对 | 全 0（含新改的 5 个导出分页点） |
| `check_default_page.py` | 91 条比对，不一致 0 |
| `check_query_matrix.py` | 1617 组合，差异 0 |
| `routes.py` 路由比对 | Java 511 全匹配，Go 514（多出 `/healthz`、`HEAD /`、`OPTIONS /`）—— 导入层改动后复跑，仍 0 缺失 |
| `compare_xlsx.py` 21 端点（EasyPOI 附件流） | 单元格差异 0 |
| **`compare_export_all.py` 59 端点（34 条 ExcelUtil 落盘型 + 22 条 EasyPOI 附件流 + 3 条 non-xlsx）** | **单元格差异 0**，临时文件删除 0 失败（3 条 non-xlsx：两条两端逐字节相同的 `{"msg":null,"code":500}`，一条 `upgradeInfo` 缺表）。导入层改动之后复跑过一遍，计数从 58/33 校正为 59/34 —— 差的那条是 `/system/user/importTemplate`，之前按 `/export` 口径没单列 |
| 第 1 档 A/B/C 复跑（最终二进制） | 14/12/**0**/2、14/12/**0**/2、14/11/1/2 |
| 第 2 档 / 第 3 档复跑（最终二进制） | 185/162/2/21、95/82/11/2 |
| 第 3 档扩面后复跑（§11.2 把 5 条顶层路由纳入口径） | 100/86/**11**/3 —— 新增的 5 条里 `/getRouters` 一开始差 `meta.link`（已修，§11.1），`/getInfo`、`/test/user/list`、`/test/user/1` 本来就一直，`/downTemplate/1` 是附件流 |
| 第 1 档导入轮复跑（Java 9987 + Go 9982，同挂 api 9902） | 14/12/**0**/2 |
| **`compare_import.py` 10 组用例（含 5 组多行：跨行顺序/终止行/区间重叠/>100 break）** | **问题 0**（唯一残项是 Java `insertUser` 的 `No group 2` 已知缺陷） |
| **`compare_upload_errors.py` 30 条上传错误形态** | **28 条一致**，2 条已知（§9.7） |
| `compare_write.py` 资源生命周期 | 原 32 资源：差异 15 条，全落在 8 个 Java 侧缺陷资源上。§11.3 扩到 **45 资源**后共 22 条 = 11 条真差异 + 11 条说明性记录；新增的 8 个资源族里 6 个四步全一致，其余 4 条新真差异全部定性完毕（见 §11.4） |
| `check_redis_isolation.py` | 24 项断言全通过，清理 `failures=0`（跑在参照对上，`PARITY_GO_DB` 按实例的 db 指定） |
| `check_oss.py` | 不一致项 0 |
| **`check_coverage.py` 全路由覆盖率盘点（本轮新增）** | 515 条注册路由：437 条被对拍覆盖 / 450 条可比 = **97.1%**；11 条无对拍价值、18 条非 CRUD 语义、36 条按约定不盲打（各有理由），剩 **13 条**待补（§11.5） |
| `/downTemplate/{type}` 7 个合法 type（本轮新纳入逐格口径） | 两端都是 xlsx 附件、**单元格差异 0**；Java 是 easypoi 重写后的字节、Go 是模板原始字节，长度不同但版面一致 |

第 1 档必须让两端 backend 挂**同一个** api 才有意义：本轮导入轮复跑时 Go 版 api（9903）的
`/health` 已是 503（其 `OdsRtSzdnSnapshotFlow*` 仓储连不上 `192.168.*` 数据源），
backend 两端配对 9903 时第 1 档会多出 4 条 `null` vs 缺键的差异 —— 用 9902 复跑即归零，
属 api 侧运行态，不是 backend 的账。

遗留待定性项复测并已销：`GET /manager/carwarning/export`（历史某轮 Java 侧 500）现在两端都是
200 附件流、12 列表头逐字同、**单元格差异 0**；那次 Java 500 反复复测不可复现，不记为差异。
另外收尾时出现过一阵「用户不存在/密码错误」：Java 参照端与 Go 端**同时**失败（重试 3 次均如此，
而 `sys_user` 里 admin 的 `status/del_flag/update_time` 都没变），过一会儿未经任何改动自行恢复，
四个实例（含共享的 9988/9989）用同一凭据重新都能登录 ——
`admin` 的口令散列没有被改过，这条记为环境抖动，不作为代码问题。

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
   交付环境两端共用同一 Redis 键时逐格一致（已用复制快照的方式验证；本轮内库行数回到 1526 后两端直接对齐）。
6. **仍未逐格覆盖的两处**：
   * `poi-tl` 的 Word 导出（`/manager/suspicious/exportAbnormalPassage`）—— 正文标签与金额已按模板对齐，
     但图片（`susImg1..7`）不内嵌，docx 也不在单元格对比工具的口径内；
   * ExcelUtil 落盘型导出**只比对其落盘文件**（`compare_export_all.py` 按 `msg` 里的文件名去
     `ruoyi.profile/download` 读两端文件，比完删除），所以要求两端共用同一个 download 目录 ——
     本环境 Java/Go 的 `profile` 都是 `D:/ruoyi/uploadPath`，成立；若分开部署需换成各自拉取。
   * 单元格**样式**（边框/字体/列宽/合并）一律不比对（POI 与 excelize 的实现差异太大，只保证表头文案、
     列序、取值、行数、文件名规则一致）。
7. 导入层两条已知差异（`compare_upload_errors.py` 里标了 `known`）：
   * `/system/user/importData` 收到「OLE2 魔数 + 垃圾字节」时，Java 走 `WorkbookFactory`，
     报的是 POIFS 头块的 `Unsupported blocksize  (2^12). Expected 2^9 or 2^6.` —— 文本随文件的扇区大小变，
     Go 只有 excelize 的统一格式错误。两个 manager 端点直接 `new XSSFWorkbook`，
     拿到的是 OLE2/HSSF 提示，已逐字一致。顺带一条能力差：真·`.xls` 改名 `.xlsx` 时
     Java 的 `WorkbookFactory` 会按 HSSF 读进去，Go（excelize）只认 OOXML —— 属移植范围外的格式支持。
   * `user 表头 + 一行"有单元格但全是空串"的空白行`：POI 的 `isRowEmpty` 看的是**单元格类型**
     （STRING 空串不算空行），于是 Java 真去插一次，撞的还是 `insertUser` 的 `No group 2` 已知缺陷，
     消息是逐行的 `1、账号  导入失败：…PersistenceException…`。Go 读不到单元格类型，
     按"值全空即空行"跳过，返回「导入用户数据不能为空！」——不镜像 Java 的插入崩溃，
     也不会在库里造出一个空账号。
8. 写侧扩面新出现的 4 条（详见 §11.4，全部是 Java 侧行为，不改 Go）：
   `messagedispose` 的 JSON 415（实体上被生成器写坏的 `@JsonFormat` 日期格式）、
   `dwd_lczt_fwqjcxx` 的 DELETE 缺 `del_flag` 列（两端同 500，只差文本）、
   `dwd_lczt_sfsjcxx/sfzjcxx` 因主键可空且"给主键即更新"而跑不了后三步、
   `sys_upgrade_info` 表在共享库里不存在。

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
python scripts/parity/compare_export_all.py --log "$TEMP/go-ref-9983.log" --out "$TEMP/exports.json"  # 58 条 /export 全覆盖
python scripts/parity/dump_excels.py BussTest CarRouteDetail                # Java @Excel 列真值
python scripts/parity/dump_templates.py carSuspicious                       # EasyPOI 模板真值
python scripts/parity/dump_local_xlsx.py <模板.xlsx> 0 5                     # 本地 xlsx 逐行（导入模板表头真值）
python scripts/parity/compare_import.py            # 导入三层：响应 + 落库（先 --clean 再起，收尾再 --clean）
python scripts/parity/compare_upload_errors.py     # 30 条上传错误形态
python scripts/parity/api_pair_check.py                      # api 双端直连比对（归因用）
```

导入类对拍要先清干净：`compare_write.py --clean` 会顺带扫 `car_except_record`
（`EXTRA_CLEAN_TABLES`，导入用例落的表没有写生命周期）。
`/manager/exceptrecord/import` 的车牌标记值不能带下划线 —— Java 会按 `_` 拆「车牌_车牌颜色」。

`pp.py` 的两个地址与两个 Redis 库都可覆盖：`PARITY_JAVA` / `PARITY_GO` / `PARITY_JAVA_DB` / `PARITY_GO_DB`
（参照实例另占 db，跑隔离类校验时必须一起指定，否则会误报）。

`compare_xlsx.py` 会先裁掉"两端都为空的尾部整行/整列"—— POI 习惯多写一列空样式列、
EasyPOI 空列表时多写一行空格，这不是差异；带值的列不会被裁掉。

## 11. 第四批（2026-11-06→07）：覆盖率盘点挖出的四个真差异 + 写侧扩面

上一批把导入层归零后，本批换了个角度：**不按接口档、而按"Go 注册的每一条路由是否真被某条对拍跑过"来查**。
新增 `scripts/parity/check_coverage.py`，口径全部复用各对拍脚本自己的定义（`compare_get.in_tier`、
`compare_export_all.export_routes`、`compare_write.RESOURCES`、`compare_import.CASES`），
避免"脚本改了、盘点没跟上"。第一轮盘出来 515 条注册路由里 **102 条从没被跑过**，
其中最大一块是 13 个纯 CRUD 资源族没进写生命周期；把口径补齐后又挖出 4 个真差异。

### 11.1 四个已修的真差异

1. **`GET /getRouters` 少 `meta.link`**。Java 的 `SysMenuServiceImpl.buildMenus:149,165` 只走
   `MetaVo(title, icon, noCache)` 三参构造，`link` 从不赋值 —— 但它是实例字段，
   Jackson 照样输出 `"link": null`。Go 的 `model.Meta` 当初写成 `string` + `omitempty`，键直接被省掉。
   改成 `*string` 且不带 omitempty。（这条路由本来就注册着，但因为不在 `/system|/monitor|...`
   任何前缀下，三档跑不到它 —— 见 §11.2。）
2. **`/downTemplate/{type}` 的模板根**。Go 原先只认「配置文件同级 `templates/down`」。
   校验用的临时配置放在 `%TEMP%`，于是 7 个合法 type 全部退成 `200 + 空 body`，
   而 Java 从 classpath 取模板、与配置位置无关，返回 7178~16113 字节的真 xlsx。
   现在按 `dir(configFile)` → `CWD/configs` 两个候选找，都找不着才落回
   「返回目录路径 ⇒ 读文件失败 ⇒ 空 200」这条与 Java 等价的分支。
   `type` 只当 map 的键用，路径每一段都是本包常量 ⇒ 没有 `../` 穿越面（已在注释里写明）。
3. **base 模块写接口多输出 `"data":""`**。Java 是 `AjaxResult.success("操作成功！", entity.getPk())`，
   而 `AjaxResult` 只在 data 非 null 时写 data 键 —— 请求体里**根本没有主键这个键**时实体主键是 null ⇒ 无 data；
   请求体显式给 `""` 时 data 是空串 ⇒ 有 data。Go 的 `bodyString` 把两者都读成 `""`，
   于是 `/base/fwqjcxx`、`/base/sfsjcxx`、`/base/sfzjcxx` 的 POST/PUT 各多一个键。
   新增 `bodyStringValue(body, key) (string, bool)` 区分缺键与空串。
4. **`PUT /manager/suspicious/check`**。Java `CarSuspiciousServiceImpl.cherkCarSuspicious` 在
   `isExcept != "1"` 时不做非空校验，直接 `for (CarSuspiciousCheck check : checkList)` 遍历 null ⇒ NPE ⇒
   GlobalExceptionHandler 的 `getMessage()` 是 null ⇒ 响应 `{"msg":null,"code":500}`；
   而方法带 `@Transactional(rollbackFor = Exception.class)`，NPE 把前面两个 delete 回滚掉，
   净效果是一行都不动。Go 原先直接"操作成功"。现在在删除之前返回同样的空消息错误；
   `checkList: []`（空数组，不是 null）仍然照常走完，与 Java 一致。

### 11.2 读侧口径扩面

`compare_get.FRAMEWORK_EXTRA = ("/getInfo", "/getRouters", "/downTemplate", "/test")`：
5 条顶层单段路由原本不在任何 root 前缀下，从来没被比过。纳入后第 3 档从 95 条变 100 条
（100/86/11/3），其中 `/getInfo`、`/test/user/list`、`/test/user/1` 本来就一直，只有
`/getRouters` 露出 §11.1.1 那条差异。

### 11.3 写侧扩面

`compare_write.RESOURCES` 从 32 个资源族扩到 **45 个**：新增
`/manager/exceptrecord`、`/manager/gantrycar`、`/manager/gantrytrade`、`/manager/suspicious`、
`/manager/aduitfree`、`/flow/applyinfo`、`/flow/currentnode`、`/flow/messagedispose`、
`/base/fwqjcxx`、`/base/sfsjcxx`、`/base/sfzjcxx`、`/system/upgradeInfo`（前三张 dwd 表的
主键是 `agent_pk`，Java 的 `DeleteMapping` 是 `/{agentPks}`，`locate()` 会把 pk 蛇化成列名，
所以条目里写 JSON 键 `agentPk`）。三张 flow 表在共享库里是空的（"无样本行"），必须自带 body。
另外给 RESOURCES 加了 `actions` 钩子：CRUD 四步之外再打一遍该资源的业务动作端点，
只作用在刚建的自己那行上（目前挂了 `PUT /manager/suspicious/check`）。

### 11.4 扩面新出现的差异定性（都是 Java 侧，Go 无需改）

| 资源 | 现象 | 定性 |
|---|---|---|
| `/flow/messagedispose` POST | Java 415 `Content type 'application/json' not supported`，Go 200 | 实体上 `@JsonFormat(pattern = "flow_message_dispose")` —— 代码生成器把表名塞进了日期格式，Jackson 建不出解析器。属 §9.1 缺陷族 |
| `/base/fwqjcxx` DELETE | 两端都 500，只差文本 | Java mapper 对没有 `del_flag` 列的 dwd 表做软删 ⇒ `Unknown column 'del_flag'`；Go 照抄同一条 SQL ⇒ 同 §9.4"同为 500 的错误文本形态"族 |
| `/base/sfsjcxx`、`/base/sfzjcxx` | POST 两端一致，后三步跑不了 | 主键 `agent_pk` 可空且无默认，而 Java 的 `save` 是"给了主键就走 updateById"⇒ 造不出可定位的自建行。记录为口径说明，不是差异 |
| `/system/upgradeInfo` | 全档 500 | 共享库里根本没有 `sys_upgrade_info` 表（§9.1 缺表族） |

### 11.5 盘点后仍剩的 13 条（下一批的活，已登记）

动作型/子资源端点，安全的可以走 `actions` 钩子，不安全的应显式豁免：

- 可补进 `actions`：`PUT /system/role/changeStatus`、`PUT /system/role/dataScope`、
  `PUT /system/user/changeStatus`、`DELETE /flow/messagedispose/delmes/:id`、
  `DELETE /flow/messagedispose/szzdmes/:id`（后两条只传路径参数，用不存在的 id 打即可，
  两端都该回"未找到"形态）。
- 应按约定豁免（会动到当前登录用户或共享缓存/真实数据）：`PUT /system/user/profile`、
  `POST /system/user/profile/avatar`、`POST /system/user/bindUky`、
  `DELETE /system/config/clearCache`、`DELETE /system/dict/type/clearCache`、
  `PUT /manager/cartrackinfo/changeTrailInfo`、`POST /flow/flowname/tbFlow`、
  `DELETE /flow/messageinfo/:id`（该表没有自建行，删的是别人的消息）。

### 11.6 两个会造成"假绿"的脚本坑（先记下来）

- Git Bash 会把 `compare_write.py /manager/xxx` 这样的位置参数转成 Windows 路径，
  于是 `only` 一条都匹配不上、脚本安静地报"差异汇总 (0)" —— 跑生命周期类脚本必须
  先 `export MSYS2_ARG_CONV_EXCL='*'`。这条坑已经吃过一次。
- 19 位雪花 id 不能当 JSON 数字传：Go 侧 `map[string]any` 解码成 float64 直接丢精度
  （`…400` 变 `…352`），Java 的 String 字段拿的是原始 token 不受影响。
  `compare_write.num()` 现在只在 15 位以内才转数字。真实浏览器也存不下 19 位整数，
  前端只会传字符串，所以这不是产品差异。
