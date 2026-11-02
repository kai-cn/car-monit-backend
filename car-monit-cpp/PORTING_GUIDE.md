# C++ 移植约定（供后续控制器/服务切片使用）

> 本文件是 `car-monit-cpp` 的内部开发约定，不是最终交付文档。
> 交付文档见 `MIGRATION_GUIDE.md` / `README_CPP.md` / `COMPATIBILITY.md`。

## 1. 目录与命名

| Java | C++ |
|---|---|
| `com.ruoyi.web.controller.system.SysUserController` | `src/cm/web/controller/system/SysUserController.cpp` |
| `com.ruoyi.system.mapper.SysUserMapper` | `include/cm/system/mapper/SysUserMapper.hpp` + `src/.../SysUserMapper.cpp` |
| `com.ruoyi.system.service.ISysXxxService` / `SysXxxServiceImpl` | `include/cm/system/service/SysXxxService.hpp` + `src/.../SysXxxService.cpp` |
| `com.ruoyi.common.core.domain.entity.SysXxx` | `include/cm/common/core/domain/entity/SysXxx.hpp` |
| `com.ruoyi.system.domain.SysXxx`（非 entity 包） | `include/cm/system/domain/SysXxx.hpp` |

* 命名空间：`cm::web`、`cm::system::mapper`、`cm::system::service`、`cm::domain`。
* 所有 SQL 字符串必须与 `ruoyi-*/src/main/resources/mapper/**/*.xml` 的语义一致。

## 2. 路由注册

每个控制器文件暴露一个注册函数，声明在自己的头文件里（不要改 `Controllers.hpp`，
汇总函数由框架维护者统一添加）：

```cpp
namespace cm::web {
void registerSysUserController(Router& r);
}
```

注册示例：

```cpp
void registerSysUserController(Router& r) {
    r.get("/system/user/list", [](RequestContext& ctx) -> cm::http::ApiResponse {
        auto page = ctx.pageRequest();      // 对应 startPage()
        // ... build count/data SQL
        return BaseController::ok(BaseController::dataTable(rows, total));
    }).permi("system:user:list");
}
```

* `@PreAuthorize("@ss.hasPermi('x')")` → `.permi("x")`
* `@PreAuthorize("@ss.hasAnyPermi('a,b')")` → `.anyPermi("a,b")`
* `@PreAuthorize("@ss.hasRole('admin')")` → `.role("admin")`
* 无 `@PreAuthorize` 的方法默认 `.Authenticated`（与 SecurityConfig 的 anyRequest 一致）。
* `@Anonymous` / `permitAll` 白名单由 `Router::securityRule` 统一处理，不需要在控制器标注。

## 3. 返回值

| Java | C++ |
|---|---|
| `AjaxResult.success()` | `BaseController::success()` |
| `AjaxResult.success(data)` | `BaseController::success(json)` |
| `AjaxResult.error(msg)` | `BaseController::error(msg)` |
| `toAjax(rows)` | `BaseController::toAjax(rows)` |
| `getDataTable(list)` | `BaseController::dataTable(rowsArray, total)` |
| `startPage()` + `getDataTable(list)` | `ctx.pageRequest()` + `cm::db::queryPage(countSql, dataSql, page)` |

`TableDataInfo` 字段顺序固定：`total -> rows -> code -> msg`；`AjaxResult` 使用
HashMap 桶序重排（`msg` 在前）。**不要**手工拼 JSON 字符串。

## 4. SQL 与安全

* 一律使用 `cm::db::Db::lit(value)` / `litNull()` / `inList(...)`，禁止字符串拼接外部输入。
* LIKE：`concat('%', ... ,'%')` 用 `"\"" + escapeLike(x) + "\""` 包一层，
  或直接 `Db::lit("%" + x + "%")`（`lit` 会转义引号）。
* 分页：`cm::db::queryPage(countSql, dataSql, page)` 已实现 PageHelper 语义
  （count=0 不查数据、reasonable 夹取、pageNum<=0 offset=0、ORDER BY 仅在缺失时追加）。
* 排序字段来自 `ctx.pageRequest().orderBy`，已过 `SqlUtil::escapeOrderBySql`。

## 5. 实体 JSON

* 每个实体提供 `Json toJson() const` / `void fromJson(const Json&)`，
  字段顺序严格按 Java 字段声明序（Jackson 默认）。
* 使用 `putStr/putI64/putJsonDate/putIsoDate`（见 `BaseEntity.hpp`），null 也要输出。
* `@JsonInclude(NON_EMPTY)` 的 VO（如 `RouterVo`）只在非空时写字段。
* HashMap/HashSet 输出顺序用 `cm::utils::javaMapOrder/javaSetOrder`。

## 6. 异常

直接 `throw cm::exception::ServiceException(msg)` / `CustomException(msg)` /
`BaseException(msg)`，由 `ExceptionMapper` 统一转 AjaxResult（HTTP 200）。
不要捕获后自己拼错误体。

## 7. 请求参数绑定

* `ctx.param("name")` → `String`（缺省 `""`）
* `ctx.optParam("name")` → `optional<string>`
* `ctx.pathVar("userId")` / `ctx.pathVarLong("userId")`
* `ctx.body()` → `Json`（`@RequestBody`）
* 上传：`ctx.req.getPart("file")`（`MultipartPart`）
* 获取当前用户：`cm::security::SecurityUtils::getUserId()` / `getUsername()` / `getLoginUser()`

## 8. 编译

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j8
./build/carmonit_tests
```

新增 `.cpp` 由 `file(GLOB_RECURSE ...)` 自动收集，无需改 CMakeLists。
