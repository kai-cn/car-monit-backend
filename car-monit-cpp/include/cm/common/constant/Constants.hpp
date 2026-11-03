#pragma once
// 对应 Java: com.ruoyi.common.constant.Constants
#include <string>

namespace cm::constant {

struct Constants {
    /** 令牌自定义标识 */
    static constexpr const char* TOKEN = "token";
    /** 令牌前缀 */
    static constexpr const char* TOKEN_PREFIX = "Bearer ";
    /** 令牌秘钥 */
    static constexpr const char* TOKEN_SECRET = "abcdefghijklmnopqrstuvwxyz";
    /** 令牌有效期（默认 30 分钟） */
    static constexpr int TOKEN_EXPIRE_TIME = 30;
    /** 用户标识 */
    static constexpr const char* LOGIN_USER_KEY = "login_user_key";
    /** 登录用户 redis key */
    static constexpr const char* LOGIN_TOKEN_KEY = "login_tokens:";
    /** 验证码 redis key */
    static constexpr const char* CAPTCHA_CODE_KEY = "captcha_codes:";
    /** 验证码有效期（分钟） */
    static constexpr long CAPTCHA_EXPIRATION = 2;
    /** 防重提交 redis key */
    static constexpr const char* REPEAT_SUBMIT_KEY = "repeat_submit:";
    /** 限流 redis key */
    static constexpr const char* RATE_LIMIT_KEY = "rate_limit:";
    /** 登录账户密码错误次数 redis key */
    static constexpr const char* PWD_ERR_CNT_KEY = "pwd_err_cnt:";
    /** 登录账户密码错误次数 */
    static constexpr int PWD_ERR_CNT_MAX = 5;
    /** 密码错误锁定时间（10 分钟） */
    static constexpr int PWD_ERR_LOCK_TIME = 10;
    /** 验证码类型 math 数组计算 char 字符验证 */
    static constexpr const char* CAPTCHA_TYPE_MATH = "math";
    static constexpr const char* CAPTCHA_TYPE_CHAR = "char";
    /** 令牌 */
    static constexpr const char* TOKEN_AUTHENTICATION = "Authorization";
    /** 资源映射路径 前缀 */
    static constexpr const char* RESOURCE_PREFIX = "/profile";
    /** 首页地址 */
    static constexpr const char* INDEX = "/index";
    /** 登录成功 */
    static constexpr const char* LOGIN_SUCCESS = "Success";
    /** 注销 */
    static constexpr const char* LOGOUT = "Logout";
    /** 注册 */
    static constexpr const char* REGISTER = "Register";
    /** 登录失败 */
    static constexpr const char* LOGIN_FAIL = "Error";
    /** 授权失败 */
    static constexpr const char* LOGIN_BLOCKED = "Blocked";
    /** 锁定 */
    static constexpr const char* LOGIN_LOCK = "Lock";
    /** 大写用户会话 */
    static constexpr const char* LOGIN_USERID = "login_userid";
    /** 管理员 ID */
    static constexpr long ADMIN_ID = 1L;
    /** UTF-8 */
    static constexpr const char* UTF8 = "UTF-8";
    /** GBK */
    static constexpr const char* GBK = "GBK";
    /** http 请求 */
    static constexpr const char* HTTP = "http://";
    /** https 请求 */
    static constexpr const char* HTTPS = "https://";
    /** 未知 */
    static constexpr const char* UNKNOWN = "unknown";
    /** 本地 IP */
    static constexpr const char* LOCAL_IP = "127.0.0.1";
    /** 是否 */
    static constexpr const char* YES = "Y";
    static constexpr const char* NO = "N";
    /** 通用成功标识 */
    static constexpr const char* SUCCESS_STR = "0";
    /** 通用失败标识 */
    static constexpr const char* FAIL = "1";
    /** 删除的标志 */
    static constexpr const char* DEL_FLAG_NORMAL = "0";
    static constexpr const char* DEL_FLAG_DELETE = "2";
    /** 所有权限标识 */
    static constexpr const char* ALL_PERMISSION = "*:*:*";
    /** 超级管理员角色 */
    static constexpr const char* SUPER_ADMIN = "admin";
    /** 部门树根 ID */
    static constexpr long DEFAULT_DEPT_ID = 100L;
    /** 参数管理 cache key */
    static constexpr const char* SYS_CONFIG_KEY = "sys_config:";
    /** 字典管理 cache key */
    static constexpr const char* SYS_DICT_KEY = "sys_dict:";

    /** 流程审核结论：委托（Java Constants.FLOW_RESULT_ENTRUST_KEY） */
    static constexpr const char* FLOW_RESULT_ENTRUST_KEY = "entrust";
    /** 委托的显示名（flow_list.SH_VALUE） */
    static constexpr const char* FLOW_ENTRUST_NAME = "委托";
    /** 委托语句前后缀：委托<姓名>办理 */
    static constexpr const char* FLOW_RESULT_CONTEXT_PREFIX = "委托";
    static constexpr const char* FLOW_RESULT_CONTEXT_SUFFIX = "办理";
    /** 部门领导角色 key（审批人解析用） */
    static constexpr const char* dept_manager_role = "dept_manager";
    /** 科室值班人角色 key */
    static constexpr const char* dept_duty_emp_role = "dept_duty_emp";
    /** 分管领导角色 key（Java 里是散在代码里的字面量） */
    static constexpr const char* dept_fg_manager_role = "fg_manager";
};

} // namespace cm::constant
