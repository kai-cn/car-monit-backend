# MAPPING_BIGSCREEN.md — 大屏接口（`manager/bigscreen`）Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §40。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `getTollList` → `get_toll_list`。
- **本切片是 Phase 3 的最后一个控制器切片**：`BigScreenController` 迁完之后，
  `ruoyi-admin` 下的 **75** 个控制器全部有对应物。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/manager/bigscreen/BigScreenController.java` | `app/api/manager/bigscreen/big_screen_controller.py` | **新建**；**12/12 映射**（全部 `GET`、**零权限点**） |
| `ruoyi-system/.../manager/domain/vo/bigscreen/SectionVO.java` | `app/manager/domain/vo/bigscreen/section_vo.py` | **新建**；只两列 `sectionCode` / `sectionName` |
| `ruoyi-system/.../manager/domain/vo/bigscreen/TollGantryFwqVO.java` | `app/manager/domain/vo/bigscreen/toll_gantry_fwq_vo.py` | **新建**；收费站的"门架"字段名是 `gantryCode` / `gantryName`（**不是** `tollCode`） |
| `ruoyi-system/.../manager/domain/vo/bigscreen/OrgVO.java` | `app/manager/domain/vo/bigscreen/org_vo.py` | **新建**；`orgCode` / `orgName` 两列 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/CarAuditVO.java` | `app/manager/domain/vo/bigscreen/car_audit_vo.py` | **新建**；四个字段都有**非 null 零初值** |
| `ruoyi-system/.../manager/domain/vo/bigscreen/CarStatisticsVO.java` | `app/manager/domain/vo/bigscreen/car_statistics_vo.py` | 早前切片已建（PC 堵漏增收在用），本切片直接复用 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/CarInfoVO.java` | `app/manager/domain/vo/bigscreen/car_info_vo.py` | 同上 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/CarLocationParam.java` | `app/manager/domain/vo/bigscreen/car_location_param.py` | 同上；10 个字符串字段，`type` / `code` 只被控制器用来拼魔法值 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/CarLocationVO.java` | `app/manager/domain/vo/bigscreen/car_location_vo.py` | 同上 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/TopTenVO.java` | `app/manager/domain/vo/bigscreen/top_ten_vo.py` | 同上；`rank` / `rate` 由 service 二次加工 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/IncomeStatisticParam.java` | `app/manager/domain/vo/bigscreen/income_statistic_param.py` | 同上 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/incomeStatisticVO.java` | 同上文件里的 `IncomeStatisticVO` | Java 类名**小写开头**；Python 按 PEP 8 改成 `IncomeStatisticVO`，字段名一字不差 |
| `ruoyi-system/.../manager/domain/vo/bigscreen/BaseBigScreenVo.java`<br>`.../vo/bigscreen/center/*.java`（6 个） | — | **不迁移（死代码）**，见 §5 |

### 1.2 被改动的已有文件（只有五处）

| 文件 | 改动 | 原因 |
|---|---|---|
| `app/base/mapper/ods_yhgl_v_base_org_mapper.py` | 新增 `select_org_list()` | Java 的 `lambdaQuery().select(orgCode, orgName).list()` 只取两列，`select_list` 做不到 |
| `app/base/service/ods_yhgl_v_base_org_service.py` | 新增 `select_org_list()`（转发） | 同上 |
| `app/manager/mapper/car_aduit_free_mapper.py` | 新增 `count_by_car_id(car_id)` | `/exceptRecordList` 逐行判"是否已有补缴记录" |
| `app/manager/service/car_aduit_free_service.py` | 新增 `count_by_car_id(car_id)`（转发） | 同上 |
| `app/base/domain/{ods_szdn_toll,ods_szdn_gantry,dwd_lczt_fwqjcxx}.py` | 各补一个 `section_code_list: Optional[List[str]]` | Java 三个实体都有 `@TableField(exist = false) List<String> sectionCodeList`，Python 侧此前漏建；`/tollGantryFwqList` 要往里塞路段列表 |
| `app/main.py` | 1 行 `import` + 1 行 `include_router` | 挂路由 |

`app/api/manager/bigscreen/__init__.py` 是**新建的包标记**（只有一行 docstring）。

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Controller | `tests/test_big_screen_controller.py` | **30** | 12 条路由表 / 全部 `GET`、无路径变量 / 空权限集恒 200 / `sectionList` 插 `"all"` / `type` 必填 → `code 500` / 空白 `sectionCode` → 空数组且不查库 / `deleteEnd` 只削一个逗号 / `"all"` 清空过滤 / 三型数据源分流 / 未知 `type` 不查库 / `sectionCode` 的 `"all"` **子串**判断 / 三个魔法值 / `type` 空时 `code` 不生效 / `carWarning` 复用同一段规整 / `carAudit` 零初值与双来源 / `queryDateType` 默认 `suo` / `orgList` 只两列 / `exceptRecordList` 逐行补两字段 |

合计 **30** 条。全量套件 **2972 passed**（本切片之前是 **2942**）。

---

## 2. 控制器：12 个映射，全部迁移

| Java | Python | Method / Path | 权限点 |
|---|---|---|---|
| `getCarStatistics` | `get_car_statistics` | GET `/manager/bigScreen/carStatistics` | **无** |
| `getCarLocation` | `get_car_location` | GET `/manager/bigScreen/carLocation` | **无** |
| `getSectionList` | `get_section_list` | GET `/manager/bigScreen/sectionList` | **无** |
| `getTollList` | `get_toll_list` | GET `/manager/bigScreen/tollGantryFwqList` | **无** |
| `carVoList` | `car_vo_list` | GET `/manager/bigScreen/carVoList` | **无** |
| `getCarAudit` | `get_car_audit` | GET `/manager/bigScreen/carAudit` | **无** |
| `getCarWarning` | `get_car_warning` | GET `/manager/bigScreen/carWarning` | **无** |
| `getExceptionCar` | `get_exception_car` | GET `/manager/bigScreen/exceptionCar` | **无** |
| `topTen` | `top_ten` | GET `/manager/bigScreen/topTen` | **无** |
| `getOrgList` | `get_org_list` | GET `/manager/bigScreen/orgList` | **无** |
| `incomeStatistic` | `income_statistic` | GET `/manager/bigScreen/incomeStatistic` | **无** |
| `list` | `list` | GET `/manager/bigScreen/exceptRecordList` | **无** |

两个 **路径** 上的坑：

1. 类上写的是 `@RequestMapping("/manager/bigScreen")` —— `bigScreen` 是**驼峰**。
   包里其它控制器全是全小写（`/manager/carinfo`、`/manager/aduitfree`），这里照抄，
   不要"顺手"改成 `/manager/bigscreen`。
2. Java 方法名 `list` 在 Python 里也叫 `list`（遮蔽内置名）—— 刻意保留，
   这样 `# Java:` 检索能对上；调用方用的是 `module.list`，不冲突。

`@CrossOrigin(origins = "*")` 由全局 `CORSMiddleware` 承担（Java 侧本来就是
`SecurityConfig` + 这个方法注解二者叠加），Python 侧不另挂。

---

## 3. 每个端点背后的 Service 调用

| 端点 | Service 方法（Python / Java 同名） | 备注 |
|---|---|---|
| `carStatistics` | `CarConfimFreeService.get_car_statistics(param)` | 返回 `List<CarStatisticsVO>`；按**字典顺序**补零的逻辑在 service 里，本切片不碰 |
| `carLocation` | `CarInfoService.car_location(param)` | 数据源是 **Redis 车辆列表**，不是 SQL |
| `sectionList` | `OdsSzdnSectionService.select_list_new(OdsSzdnSection())` | 空条件 = 全量；返回前手工 `insert(0, 全部)` |
| `tollGantryFwqList` | `OdsSzdnTollService` / `OdsSzdnGantryService` / `DwdLcztFwqjcxxService` 的 `select_list_new(query)` | 按 `type` 三选一 |
| `carVoList` | `CarInfoService.select_car_vo_list()` | SQL 多选了 `t.id` / `t.escaped_type_name`，`CarInfoVO` 没这两个属性 → 被**丢弃** |
| `carAudit` | `CarAduitFreeService.get_car_audit(param)` + `CarConfimFreeService.get_car_confirm(param)` | 两次查询，顺序固定 |
| `carWarning` | `CarWarningInfoService.select_car_warning_info_list_limit100(param)` | 数据源同样是 Redis |
| `exceptionCar` | `CarSuspiciousService.select_list_limit10()` | 固定 10 条，无入参 |
| `topTen` | `OdsRtSzdnSnapshotFlowAddcodeService.get_top_ten()` | 排名 / 百分比在 service 里算 |
| `orgList` | `OdsYhglVBaseOrgService.select_org_list()` | **本切片新增**；只取 `org_code` / `org_name` |
| `incomeStatistic` | `CarAduitFreeService.income_statistic(param)` | `queryDateType` 的 `suo` 默认值在**控制器**里盖 |
| `exceptRecordList` | `CarExceptRecordService.select_list(param)`<br>+ `CarConfimFreeService.select_org_id(car_id, id)`<br>+ `CarAduitFreeService.count_by_car_id(car_id)` | 后两个是**逐行**调用，见 §4.9 |

---

## 4. 12 个必须照抄的业务细节

1. **一个权限点都没有。** 类上和方法上都没有 `@PreAuthorize`，只要登录就能访问全部 12 个端点
   —— Python 侧也没有 `pre_authorize_permi`。别"顺手"按 CRUD 惯例补权限点。

2. **`tollGantryFwqList` 的 `type` 是必填。** Java 写的是
   `@RequestParam String type`（没有 `required = false`），缺失时 Spring 抛
   `MissingServletRequestParameterException`，被 `GlobalExceptionHandler` 的
   `Exception` 分支接住 → HTTP 200 + `{"code":500,"msg":"Required request parameter 'type' ..."}`。
   Python 侧用模块常量 `MISSING_TYPE_MESSAGE` 复刻同一句英文原文。

3. **`sectionCode` 空白直接回空数组**，不是"不过滤 = 全量"：
   `if (StringUtils.isBlank(sectionCode)) return AjaxResult.success(new ArrayList<>());`

4. **`deleteEnd` 只削一个尾逗号，再按 `,` 切。** `"SD01,SD02,"` → `["SD01","SD02"]`；
   `"SD01,,"` 削成 `"SD01,"`，`String.split` 丢掉尾部空段 → 还是 `["SD01"]`
   （`split_regex` 复刻 `String.split` 的"丢尾部空串"语义）。

5. **`"all"` 判在整串上，不在列表上。** Java 原文是
   `if (sectionCode.indexOf(Constants.section_all) > -1) sectionCodeList = new ArrayList<>();`
   —— `indexOf` 作用在**削完逗号的整串**（不是切分后的列表），所以是**子串**判断：
   `"SD01,all"` 也会把列表清空。Python 侧写作 `section_all in stripped`（同样对整串），
   列表为空 → 三个 XML 里的 `<if>` 不生效 → 全量。
   注意这段判定在 `split` **之后**，但用的仍是 `split` 之前的那个字符串变量。

6. **`all` 在 `carLocation` / `carWarning` 里是子串判断。**
   `if (sectionCode.contains("all")) param.setSectionCode("");` ——
   前端发的 `"all,SD01"` 也会被整串清空。**不是** `equals`。

7. **三个魔法值，不是 `null`。** `type` 非空时：
   `1` → `tollCode`、`2` → `gantryCode`、`3` → `fwqbm`；
   `code` 为空则塞 `StationCapture` / `GantryCapture` / `ServiceAreaCapture`
   （常量在 `app/common/constant/constants.py`）。这段代码在 Java 里
   `getCarLocation` 与 `getCarWarning` **逐字重复了一遍**，Python 抽成
   `_normalise_location_param()` 供两处调用 —— 这是本切片唯一的结构性归并，
   行为完全一致（同一个函数体，调用点顺序不变）。

8. **`type` 为空时整段都不执行。** `code` 再非空也不会写进任何字段；
   `sectionCode` 的清空仍然先做（两件事相互独立）。

9. **`exceptRecordList` 的 N+1 查询原样保留。** 分页结果逐行：
   - `orgId` ← `carConfimFreeService.selectOrgId(carId, id)`；
   - `supplementaryStatus`：`carAduitFreeService` 按 `carId` 数到 **> 0** 条时置 `"1"`
     （实体默认 `"0"`）。
   不要"优化"成一条 join —— 语义不同（`count` 走 `del_flag = '0'` 的逻辑删除条件）。

10. **`carAudit` 的空值语义。** 两个来源各自可能回 `null`，为 `null` 时**保留 VO 的零初值**
    （`0` / `0` / `BigDecimal.ZERO`），不是把响应字段写成 `null`。顺序固定：
    先 `getCarAudit`（异常流水），再 `getCarConfirm`（已追缴）。

11. **`orgList` 只回两列。** Java 走 `lambdaQuery().select(OdsYhglVBaseOrg::getOrgCode,
    OdsYhglVBaseOrg::getOrgName).list()`，再逐条拷进 `OrgVO` —— 所以响应体里
    没有 `orgId` / `delFlag` 这些列。

12. **`incomeStatistic` 的 `queryDateType` 默认值在控制器里。**
    `if (StringUtils.isBlank(param.getQueryDateType())) param.setQueryDateType("suo");`
    —— 不在 SQL 里。所以传 `zhan` 才拿到"按站"粒度，不传就是"按所"。

---

## 5. 不迁移：`bigscreen/center` 6 个 VO + `BaseBigScreenVo`（死代码）

`BaseBigScreenVo.java` 与 `bigscreen/center/` 下的 6 个 VO
（`CenterStatisticsVo` / `OrderAndEnterpriseVo` / `OrderAndEnterpriseInfoVo` /
`OrderDetailVo` / `TransitOrderDetailVo` / `TrackPoint`）在全仓范围内
**没有任何控制器、服务或 Mapper 引用** —— 只有 `CenterStatisticsVo` 为了继承而引用
`BaseBigScreenVo`，其余全是自引用。

它们属于一套**未实现的"城市配送中心大屏"**（`TWaybill` / `TWaybillRoute` 两个实体
在 Java 侧有、业务侧没有调用方），而 `TWaybill` / `TWaybillRoute` 本身也没迁
（`app/manager/domain/` 下没有对应文件）。

按项目约定（见 `MIGRATION_PROGRESS.md` §0 的 `不迁移` 状态）：
**Java 源码一行不动**，Python 侧不造无调用方的空壳，理由记在这里与
`COMPATIBILITY.md` §40.5。若将来那套大屏要上线，这 7 个 VO 连同两个实体一起补。

---

## 6. 已知偏差

| 偏差 | 影响 | 位置 |
|---|---|---|
| `Decimal` 序列化成 **JSON 字符串**（Java/Jackson 输出数字） | `carAudit` 的 `totalAmount` / `finishedAmount`、`carStatistics` 的 `escapedAmount` 等金额字段变成 `"0"` / `"12.5"` | 全局 `ORJSONResponse` 造成，早于本切片；见 `COMPATIBILITY.md` §40.1 |
| 分页结果逐行补字段（N+1） | 与 Java 完全一致，`pageSize` 大时查询次数线性增长 | §4.9 |

---

## 7. 怎么自查

```bash
cd car-monit-py
.venv\Scripts\python.exe -m pytest tests\test_big_screen_controller.py --no-header
.venv\Scripts\python.exe -m pytest --no-header -p no:cacheprovider   # 全量 2972
```

对照 Java 时只要搜这三样：

1. 控制器里 12 个 `@GetMapping` 的 value 与 §2 的表；
2. 三个魔法值常量（`GantryCapture` / `ServiceAreaCapture` / `StationCapture`）；
3. `StringUtils.isBlank` / `contains("all")` / `deleteEnd` 三处字符串语义。
