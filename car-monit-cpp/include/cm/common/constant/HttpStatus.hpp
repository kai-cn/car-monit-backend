#pragma once
// 对应 Java: com.ruoyi.common.constant.HttpStatus
namespace cm::constant {

struct HttpStatus {
    /** 操作成功 */
    static constexpr int SUCCESS = 200;
    /** 对象创建成功 */
    static constexpr int CREATED = 201;
    /** 请求已经被接受 */
    static constexpr int ACCEPTED = 202;
    /** 操作已经执行成功，但是没有返回数据 */
    static constexpr int NO_CONTENT = 204;
    /** 资源已被移除 */
    static constexpr int MOVED_PERM = 301;
    /** 重定向 */
    static constexpr int SEE_OTHER = 303;
    /** 资源没有被修改 */
    static constexpr int NOT_MODIFIED = 304;
    /** 参数列表错误（缺少，格式不匹配） */
    static constexpr int BAD_REQUEST = 400;
    /** 未授权 */
    static constexpr int UNAUTHORIZED = 401;
    /** 访问受限，授权过期 */
    static constexpr int FORBIDDEN = 403;
    /** 资源，服务未找到 */
    static constexpr int NOT_FOUND = 404;
    /** 不允许的 http 方法 */
    static constexpr int BAD_METHOD = 405;
    /** 资源冲突，或者资源被锁 */
    static constexpr int CONFLICT = 409;
    /** 不支持的数据，媒体类型 */
    static constexpr int UNSUPPORTED_TYPE = 415;
    /** 系统内部错误 */
    static constexpr int ERROR = 500;
    /** 接口未实现 */
    static constexpr int NOT_IMPLEMENTED = 501;
    /** 系统警告消息 */
    static constexpr int WARN = 601;
};

} // namespace cm::constant
