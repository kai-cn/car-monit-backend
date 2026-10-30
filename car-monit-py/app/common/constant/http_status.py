"""Return-code constants.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/HttpStatus.java

Java used a ``public class`` with ``public static final int`` fields. Python has no
constants, so the class is only a namespace: never instantiate it. Every value is
copied verbatim so that API responses stay byte-identical.
"""


class HttpStatus:
    """返回状态码 / HTTP status code constants (values unchanged from Java)."""

    # 操作成功
    SUCCESS: int = 200
    # 对象创建成功
    CREATED: int = 201
    # 请求已经被接受
    ACCEPTED: int = 202
    # 操作已经执行成功，但是没有返回数据
    NO_CONTENT: int = 204
    # 资源已被移除
    MOVED_PERM: int = 301
    # 重定向
    SEE_OTHER: int = 303
    # 资源没有被修改
    NOT_MODIFIED: int = 304
    # 参数列表错误（缺少，格式不匹配）
    BAD_REQUEST: int = 400
    # 未授权
    UNAUTHORIZED: int = 401
    # 访问受限，授权过期
    FORBIDDEN: int = 403
    # 资源，服务未找到
    NOT_FOUND: int = 404
    # 不允许的http方法
    BAD_METHOD: int = 405
    # 资源冲突，或者资源被锁
    CONFLICT: int = 409
    # 不支持的数据，媒体类型
    UNSUPPORTED_TYPE: int = 415
    # 系统内部错误
    ERROR: int = 500
    # 接口未实现
    NOT_IMPLEMENTED: int = 501
    # 系统警告消息
    WARN: int = 601
