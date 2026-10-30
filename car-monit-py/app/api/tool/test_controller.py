"""Swagger 用户测试方法 / dev-only in-memory user CRUD.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool/TestController.java

这是一段**开发期脚手架**，不碰数据库、不碰 Redis，数据只在进程内存里。迁移原则第 4 条
要求"不擅自删除 Java 中看似无用的代码"，所以整块照搬，包括那几个刻意的怪癖。

5 个映射，全部迁移
------------------
=================  ==============================  ==================================
Java               Method / Path                   权限点
=================  ==============================  ==================================
``userList``       GET ``/test/user/list``         **无**（登录即可）
``getUser``        GET ``/test/user/{userId}``     **无**
``save``           POST ``/test/user/save``        **无**
``update``         PUT ``/test/user/update``       **无**
``delete``         DELETE ``/test/user/{userId}``  **无**
=================  ==============================  ==================================

``SecurityConfig`` 里没有一条规则命中 ``/test/**``，于是落到
``anyRequest().authenticated()`` —— **登录即可，无需权限点**。

``save`` 与 ``update`` 的绑定方式**不同**
-----------------------------------------
* ``update`` 的形参带 ``@RequestBody`` -> 读 **JSON 请求体**；
* ``save`` 的形参**没有** ``@RequestBody`` -> 走
  ``ServletModelAttributeMethodProcessor``，读的是 **request parameter**，
  也就是 **query string 或 ``application/x-www-form-urlencoded`` 表单**。

于是 ``POST /test/user/save`` 发一段 JSON 是**无效**的：Spring 会把三个字段全绑成
``null``，直接回 ``{"code":500,"msg":"用户ID不能为空"}``。照搬这条 —— 用 JSON 调这个端点
永远失败。

同名参数同时出现在 query 与表单体里时，Tomcat 的 ``getParameter`` 取**先解析到的**
那个（query string 先于请求体），所以这里让 query 覆盖表单。

``users`` 是 ``LinkedHashMap<Integer, UserEntity>``
--------------------------------------------------
* 顺序是**插入顺序**（不是排序），``list`` 直接按这个顺序回；
* ``put`` 一个已存在的键只改值、**不动位置**（``accessOrder=false``）；
* ``update`` 先 ``remove`` 再 ``put``，于是被更新的用户会被**挪到末尾** —— 这是
  ``LinkedHashMap`` 与 Python ``dict`` 在本用例下的**唯一**可见差异点，两边行为恰好
  一致（Python ``dict`` 的 ``del`` + 赋值同样把键挪到末尾）；
* Java 侧没有任何同步措施（``LinkedHashMap`` 非线程安全），Python 侧同样不加锁。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Request

from app.common.core.controller.base_controller import bind_query_params
from app.common.core.domain.domain_model import DomainModel, JavaString
from app.common.core.domain.r import R

router = APIRouter(prefix="/test/user", tags=["tool"])


class UserEntity(DomainModel):
    """Java: the package-private ``class UserEntity`` declared in ``TestController.java``.

    Java 把它写在**同一个文件**里（包级可见），这里保持在同一个模块，位置也照抄。
    """

    #: 用户ID（Java: ``Integer userId``）
    user_id: Optional[int] = None
    #: 用户名称
    username: JavaString = None
    #: 用户密码
    password: JavaString = None
    #: 用户手机
    mobile: JavaString = None


#: Java: ``private final static Map<Integer, UserEntity> users``（实例初始化块里灌两条）。
_SEED_USERS: Dict[int, Dict[str, Any]] = {
    1: {"userId": 1, "username": "admin", "password": "admin123", "mobile": "15888888888"},
    2: {"userId": 2, "username": "ry", "password": "admin123", "mobile": "15666666666"},
}

#: 进程级内存表（Java 的 static map）。键序 = 插入序。
_USERS: Dict[int, Dict[str, Any]] = dict(_SEED_USERS)


def reset_users() -> None:
    """Test helper: restore the two seeded rows (Java 只能重启进程)."""
    _USERS.clear()
    _USERS.update({key: dict(value) for key, value in _SEED_USERS.items()})


# --------------------------------------------------------------------------- 依赖


async def _bind_user_from_parameters(request: Request) -> UserEntity:
    """Java: 形参 ``UserEntity user``（**没有** ``@RequestBody``）。

    Spring 读的是 ``HttpServletRequest#getParameter``，它同时覆盖 query string 与
    ``application/x-www-form-urlencoded`` 请求体。FastAPI 的同步端点读不到表单体
    （``request.form()`` 是协程），所以 ``save`` 声明成 ``async def`` —— 这是本切片
    唯一"为了绑定语义牺牲同步端点"的地方。
    """
    merged: Dict[str, Any] = {}

    content_type = (request.headers.get("content-type") or "").lower()
    if content_type.startswith("application/x-www-form-urlencoded") or content_type.startswith(
        "multipart/form-data"
    ):
        form = await request.form()
        for key, value in form.items():
            merged[key] = value if isinstance(value, str) else getattr(value, "filename", None)

    # Tomcat 先解析 query string，再解析请求体 -> 同名时 query 的值胜出。
    for key, value in request.query_params.multi_items():
        merged[key] = value

    return bind_query_params(UserEntity, merged)


#: 已按 Spring 语义绑定好的实体（query string / 表单），不是 JSON 请求体。
SaveUser = Annotated[UserEntity, Depends(_bind_user_from_parameters)]


# --------------------------------------------------------------------------- 端点


@router.get("/list", response_model=None)
def user_list() -> R:
    """获取用户列表. Java: ``@GetMapping("/list") public R<List<UserEntity>> userList()``."""
    return R.ok_data([row for row in _USERS.values()])


@router.get("/{user_id}", response_model=None)
def get_user(user_id: int) -> R:
    """获取用户详细. Java: ``@GetMapping("/{userId}") public R<UserEntity> getUser(...)``.

    ``user_id: int`` 非数字时由 ``RequestValidationError`` 处理器接住 -> HTTP 200 +
    ``code 500``，与 Java 的 ``MethodArgumentTypeMismatchException`` 一致（文案不同）。
    """
    if _USERS and user_id in _USERS:
        return R.ok_data(_USERS[user_id])
    # Java: R.fail("用户不存在") —— 选中的是 ``fail(String msg)`` 重载，不是 ``fail(T data)``
    return R.fail_msg("用户不存在")


@router.post("/save", response_model=None)
async def save(user: SaveUser) -> R:
    """新增用户. Java: ``@PostMapping("/save") public R<String> save(UserEntity user)``."""
    # Java: StringUtils.isNull(user) 恒为 false（Spring 总会 new 一个），只有 userId 判据有效
    if user.user_id is None:
        return R.fail_msg("用户ID不能为空")
    # Java: users.put(user.getUserId(), user) —— 已存在则改值、位置不变
    _USERS[user.user_id] = user.to_json_dict()
    return R.ok()


@router.put("/update", response_model=None)
def update(user: UserEntity) -> R:
    """更新用户. Java: ``@PutMapping("/update") public R<String> update(@RequestBody UserEntity user)``."""
    if user.user_id is None:
        return R.fail_msg("用户ID不能为空")
    if not _USERS or user.user_id not in _USERS:
        return R.fail_msg("用户不存在")
    # Java: remove + put —— 在 LinkedHashMap 里等于"删了再插"，位置推到末尾
    del _USERS[user.user_id]
    _USERS[user.user_id] = user.to_json_dict()
    return R.ok()


@router.delete("/{user_id}", response_model=None)
def delete(user_id: int) -> R:
    """删除用户信息. Java: ``@DeleteMapping("/{userId}") public R<String> delete(...)``."""
    if _USERS and user_id in _USERS:
        del _USERS[user_id]
        return R.ok()
    return R.fail_msg("用户不存在")


__all__ = ["router", "UserEntity", "reset_users", "user_list", "get_user", "save", "update", "delete"]
