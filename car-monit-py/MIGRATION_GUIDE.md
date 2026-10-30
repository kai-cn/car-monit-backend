# MIGRATION_GUIDE.md — 迁移是怎么做的（以及怎么接着做）

> 三份文档分工不同，别混着看：
>
> | 文件 | 回答什么 |
> |---|---|
> | **`MIGRATION_GUIDE.md`**（本文件） | **怎么迁的** —— 原则、分层映射、步骤、坑 |
> | `COMPATIBILITY.md` | **差在哪** —— 逐条差异 + 影响分级 + 规避方式 |
> | `MAPPING_*.md` | **哪个对哪个** —— 每个切片的文件/端点/SQL/字段对照表 |
> | `MIGRATION_PROGRESS.md` | **做到哪了** —— 范围、状态、剩余项 |
>
> 迁移**已经全部完成**（78 个控制器 / 501 个端点 / 3646 条用例全绿）。本文件的作用是：
> 以后要补一个端点、或者升级 RuoYi 上游版本时，按同一套规矩改，不要破坏已经对齐的行为。

---

## 1. 五条硬性约束

1. **行为等价优先。** 路由、请求/响应字段、状态码、错误码、业务规则、表结构、字段类型、
   默认值、边界条件，全部按 Java 逐条对齐。不「顺手优化」，不「现代化」。
2. **结构镜像。** 目录、模块、类、函数名跟 Java 走；Python 侧用 snake_case，但保持可读的对应关系。
3. **可追溯。** 每个文件首行 `# Migrated from: com/xxx/UserService.java`；
   关键函数上方 `# Java: com.ruoyi.xxx.UserService#getUserById`。
4. **不加功能。** Java 里「看起来没用但存在」的代码**照抄**，不删不改；确实要动，先记进
   `COMPATIBILITY.md` 并标注等级。Java 自己没实现的（比如 `captchaEnabled` 标志）也不补。
5. **能跑起来。** `pip install -r requirements.txt` + 一条 `python run.py` + `scripts/smoke_test.py`。

## 2. 分层映射

| Spring Boot / RuoYi | Python 实现 |
|---|---|
| `RuoYiApplication` | `run.py` + `app/main.py` |
| `application.yml` | `config/application.yml` + `app/settings.py`（pydantic-settings） |
| `logback-spring.xml` | `app/logging_config.py` |
| `@RestController` + `@XxxMapping` | `APIRouter` 的 `@router.get/post/put/delete` |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi(...)`（必须写在 `@router.xxx` **下面**） |
| `@Log(title, businessType)` | `@log(title, business_type)` → `app/framework/aspectj/log_aspect.py` |
| `@RepeatSubmit` | `dependencies=[Depends(repeat_submit())]`（`app/framework/interceptor/`） |
| `@DataScope` | `app/framework/aspectj/data_scope_aspect.py`（只对 `sys_role` 生效，见 §27.1） |
| `GlobalExceptionHandler` | `app/framework/security/handle/exception_handlers.py` |
| `FilterSecurityInterceptor` 过滤器链 | `app/framework/security/filter/` 里的 ASGI 中间件 |
| `TokenService`（JWT + Redis） | `app/framework/web/service/token_service.py` |
| `AjaxResult`（**HashMap**） | `app/common/core/domain/ajax_result.py` + `java_hash_map.py` |
| `TableDataInfo` / `R<T>`（POJO） | `app/common/core/page/table_data_info.py` / `app/common/core/domain/r.py` |
| `BaseEntity` / `BaseUuidEntity` | `app/common/core/domain/base_entity.py` / `base_uuid_entity.py` |
| `PageHelper.startPage()` | `app/common/core/page/page_helper.py` 的 `start_page()` + mapper 的 `take_page()` |
| MyBatis XML（`resources/mapper/**`） | SQLAlchemy Core `text()`，SQL 原样搬进 `*_mapper.py` |
| `ExcelUtil`（Apache POI） | `app/common/utils/poi/excel_util.py` + `app/common/annotation/excel.py` |
| `DictUtils` / `SysConfig` 缓存 | `app/common/utils/dict_utils.py` / `sys_config_service.py` |
| `StringUtils.split` | `app/common/core/text/convert.py` 的 `_java_split` |
| `org.quartz` | `app/quartz/util/scheduler.py` + `cron_expression.py`（自研，不引 APScheduler） |

## 3. 加一个控制器切片的六步

1. **先读 Java。** 把 `XxxController` 的 8 个注解（`@PreAuthorize` / `@Log` / `@GetMapping` …）
   逐个抄成清单：端点、HTTP 方法、权限点、参数类型、返回类型。
2. **读 Service + Mapper XML。** SQL 原样搬（含 `#{}` → `:named` 的等价改写、
   `<where>` 吞掉首个 `AND` 的语义、`<if test>` 的默认分支）。
3. **建/复用领域模型。** 先看 Java 的 `extends`：
   `BaseEntity`（String 审计列、`params` 为空时**缺键**）还是
   `BaseUuidEntity`（UUID 主键、`Long` 审计列、`params` 输出 `null`）。**不要默认用前者。**
4. **写控制器。** 装饰器顺序 `@router.xxx` → `@pre_authorize_permi` → `@log`；
   返回 `AjaxResult` 时**只准**用 `success()` / `success_data()` / `put_chain()`，
   不要 `result["x"] = ...`（见 §4.1）。
5. **写四条用例**（见 §5）：mapper / service / controller / e2e（或 integration）。
6. **补文档三件套。** `MAPPING_<切片>.md` + `COMPATIBILITY.md` 新编号小节 +
   `MIGRATION_PROGRESS.md` 的切片表与「最后更新」。

## 4. 六个高频坑

### 4.1 `AjaxResult` 是 `HashMap`，键序是**桶序**

`AjaxResult extends HashMap<String,Object>`（`AjaxResult.java:14`），Jackson 按 HashMap
的迭代顺序输出，不是 `put` 的先后。`msg`(桶 0) 永远在最前，`code`(桶 3) 在 `data`(桶 4) 之前。

```python
result = AjaxResult.success()
result.put_chain("uuid", uuid)        # ok：内部按桶号重排
result["uuid"] = uuid                 # 错：变成插入序，真实字节不同
```

回归阀：`tests/test_core_types.py::TestAjaxResult::test_put_chain_places_keys_by_bucket_not_by_call_order`。
`TableDataInfo`（`total, rows, code, msg`）和 `R`（`code, msg, data`）是普通 POJO，
按**字段声明序**，不要套桶序。

### 4.2 `String.split` 的三种反直觉行为

* 尾部空串被丢弃：`"a,b,,".split(",")` → `["a","b"]`；
* **全分隔符返回空数组**：`",".split(",")` → `[]`，不是 `[""]` ——
  `to_long_array(",")` 必须得 `[]`，否则 Java 的 `in ()` 语法错误（500）会被降级成「删 0 行」；
* 不匹配时返回原串的单元素数组。

### 4.3 NPE 的文案是 `null`，不是异常类名

`e.getMessage()` 对 NPE 是 `null`，`"导入失败：" + e.getMessage()` 拼出来是
`"导入失败：null"`。Python 侧用 `_java_exception_message()` / `AttributeError("java.lang.NullPointerException: ...")`
两种形态还原，全局处理器据哨兵值决定 `msg` 是 `null` 还是文案。
**拼接场景要拼成字面量 `"null"`。**

### 4.4 权限校验与参数校验的先后顺序相反

Java 是 AOP 切在方法调用上，路径变量在调用**之前**解析完，所以「参数缺失 500 → 权限 403」；
Python 的装饰器先执行，顺序反了。唯一受影响的端点恒定 500，真实调用方两边一致 ——
**不要为了对齐去改全仓 242 处装饰器**（`COMPATIBILITY.md` §43.1）。

### 4.5 MyBatis 嵌套集合「一列都对不上」时是 `null`，不是 `[]`

`<collection resultMap="...">` 的 `applyNestedResultMappings` 拿嵌套映射的列去比
`mappedColumnNames`，一个都不匹配就**根本不构造**嵌套对象，属性停在 `null`。
`GenTable` 列表行的 `"columns": null` 就是这个原因，别「修正」成 `[]`。

### 4.6 分页是「线程本地」的，不是参数

`start_page()` 把分页信息放进上下文，mapper 末尾的 `take_page()` 取出来。
漏了 `take_page()` 会静默返回全表，漏了 `start_page()` 会变成不分页 —— 两种都不报错。
新加列表接口先确认 Java 是否调了 `PageHelper.startPage()`。

## 5. 测试的分层要求

| 层 | 文件命名 | 钉住什么 |
|---|---|---|
| mapper | `tests/test_<模块>_mapper.py` | 生成的 SQL 文本、参数绑定、`None`/空串归一 |
| service | `tests/test_<模块>_service.py` | 业务分支、缓存清理时机、事务边界 |
| controller | `tests/test_<模块>_controller.py` | 路由、状态码、**响应体键序**、权限拒绝 |
| e2e | `tests/test_e2e_*.py` | 真 ASGI + 假 DB，走完整中间件链 |
| integration | `tests/integration/test_real_backend.py` | 真 MySQL + 真 Redis（`-m integration`） |

约定：断言响应体时**断言 `list(body)` 的键序**，不要只断言 `body["code"]`。
`pytest` 的 `addopts` 已带 `-q`；全量 **3646** 条（3563 单测 + 83 条联调），跑一遍约 36 秒。

## 6. 回归与对拍

四个审计脚本都是**只读源码**的，不写库、不改代码，跑完共约 10 秒；
任一层检出差异都以**非 0 退出码**结束，可以直接写进 CI：

```bash
python -m pytest                                   # 全量套件（含 83 条真实 MySQL/Redis 联调）
python scripts/audit_endpoints.py                  # 路由对拍（Java @XxxMapping vs @router.xxx）
python scripts/audit_domains.py                    # 域字段对拍（Java 字段 + getter vs pydantic 别名）
python scripts/audit_envelopes.py                  # 响应信封对拍（返回类型 -> AjaxResult/TableDataInfo/R/Response）
python scripts/audit_messages.py                   # 文案双向对拍（Java 字面量 ↔ Python 字面量）
python scripts/smoke_test.py --base-url http://127.0.0.1:9989   # 真 socket 自检（需先起服务）
```

对照表也是在仓库里生成的，改完控制器就重跑一次，否则表和代码会漂：

```bash
python scripts/gen_mapping_docs.py                 # 重写 MAPPING_{BASE,MANAGER,FLOW,TOOL,GENERATOR}.md
```

当前基线（`COMPATIBILITY.md` §44.1）：

| 指标 | 值 |
|---|---|
| 端点 | Java 501 / Python 502（多 `GET /health`）/ 缺失 **0** |
| 域字段 | 可比 115，属性/Excel/导出列 **零缺口** |
| 响应信封 | 可比 501 全部归类：`AjaxResult`→`AjaxResult` 359、`TableDataInfo`→`TableDataInfo` 100、`AjaxResult`→`Response` 24、`void`→`Response` 8、`R`→`R` 5、`String`→`str` 5 |
| 文案 | Java 148 种 / Python 155 种，两侧缺口均 **0** |
| 用例 | **3646 passed / 0 failed / 0 skipped** |
| 对照表 | 5 份 `MAPPING_*.md`：54 个控制器 / 341 个端点，且生成器幂等 |
| 自检 | smoke **5/5** |

改完代码后请重跑这几项，并把结果与基线对照；如果数字变了，先问「是不是我多写/漏写了一个端点」，
再问「是不是我改了一个 `msg`」。
