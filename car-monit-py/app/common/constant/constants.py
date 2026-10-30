"""Common constants.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/constant/Constants.java

Java declared ``public class Constants`` with ``public static final`` fields. Python has no
constants, so this module is only a namespace of module-level values. Every literal is copied
verbatim -- several of them leak into HTTP responses (Redis key prefixes, the ``token`` field
name, the ``admin`` role key), so changing one changes observable behaviour.

Two Java idioms had to be translated:

* ``Constants.JWT_USERNAME = Claims.SUBJECT`` -- jjwt's ``Claims.SUBJECT`` is the literal
  ``"sub"``. Python has no jjwt type, so the string is inlined and the origin is documented.
* ``Constants.DEFAULT_LOCALE = Locale.SIMPLIFIED_CHINESE`` -- stored as the BCP-47-ish tag
  ``"zh_CN"`` that :mod:`app.common.utils.message_utils` already keys its bundle on.
"""

from __future__ import annotations

from typing import Final, List

# --------------------------------------------------------------------------- 字符集

#: UTF-8 字符集
UTF8: Final[str] = "UTF-8"
#: GBK 字符集
GBK: Final[str] = "GBK"
#: 系统语言 (Java: ``Locale.SIMPLIFIED_CHINESE``)
DEFAULT_LOCALE: Final[str] = "zh_CN"

# --------------------------------------------------------------------------- URL

#: www主域
WWW: Final[str] = "www."
#: http请求
HTTP: Final[str] = "http://"
#: https请求
HTTPS: Final[str] = "https://"

# --------------------------------------------------------------------------- 通用标识

#: 通用成功标识
SUCCESS: Final[str] = "0"
#: 通用失败标识
FAIL: Final[str] = "1"

#: 登录成功 (写入 sys_logininfor.status)
LOGIN_SUCCESS: Final[str] = "Success"
#: 注销
LOGOUT: Final[str] = "Logout"
#: 注册
REGISTER: Final[str] = "Register"
#: 登录失败
LOGIN_FAIL: Final[str] = "Error"

# --------------------------------------------------------------------------- 权限

#: 所有权限标识
ALL_PERMISSION: Final[str] = "*:*:*"
#: 管理员角色权限标识
SUPER_ADMIN: Final[str] = "admin"
#: 角色权限分隔符
ROLE_DELIMETER: Final[str] = ","
#: 权限标识分隔符
PERMISSION_DELIMETER: Final[str] = ","

# --------------------------------------------------------------------------- 令牌

#: 验证码有效期（分钟）
CAPTCHA_EXPIRATION: Final[int] = 2
#: 令牌 (登录响应里的字段名，前端按此读取)
TOKEN: Final[str] = "token"
#: 令牌前缀
TOKEN_PREFIX: Final[str] = "Bearer "
#: 令牌前缀 (JWT claim 名)
LOGIN_USER_KEY: Final[str] = "login_user_key"
#: 用户ID
JWT_USERID: Final[str] = "userid"
#: 用户名称 (Java: ``Claims.SUBJECT`` == ``"sub"``)
JWT_USERNAME: Final[str] = "sub"
#: 用户头像
JWT_AVATAR: Final[str] = "avatar"
#: 创建时间
JWT_CREATED: Final[str] = "created"
#: 用户权限
JWT_AUTHORITIES: Final[str] = "authorities"

#: 资源映射路径 前缀
RESOURCE_PREFIX: Final[str] = "/profile"

# --------------------------------------------------------------------------- 远程调用黑名单

#: RMI 远程方法调用
LOOKUP_RMI: Final[str] = "rmi:"
#: LDAP 远程方法调用
LOOKUP_LDAP: Final[str] = "ldap:"
#: LDAPS 远程方法调用
LOOKUP_LDAPS: Final[str] = "ldaps:"

#: 自动识别json对象白名单配置（仅允许解析的包名，范围越小越安全）
JSON_WHITELIST_STR: Final[List[str]] = ["org.springframework", "com.ruoyi"]
#: 定时任务白名单配置（仅允许访问的包名，如其他需要可以自行添加）
JOB_WHITELIST_STR: Final[List[str]] = ["com.ruoyi.quartz.task"]
#: 定时任务违规的字符
JOB_ERROR_STR: Final[List[str]] = [
    "java.net.URL",
    "javax.naming.InitialContext",
    "org.yaml.snakeyaml",
    "org.springframework",
    "org.apache",
    "com.ruoyi.common.utils.file",
    "com.ruoyi.common.config",
    "com.ruoyi.generator",
]

# --------------------------------------------------------------------------- 流程

#: 流程结果-委托
FLOW_RESULT_ENTRUST_KEY: Final[str] = "entrust"
#: 流程结果内容前缀-委托
FLOW_RESULT_CONTEXT_PREFIX: Final[str] = "委托"
#: 流程结果内容后缀-委托
FLOW_RESULT_CONTEXT_SUFFIX: Final[str] = "办理"
#: 流程委托
FLOW_ENTRUST_NAME: Final[str] = "委托"
#: 忽略流程中的 tenant_id 查询条件
FLOW_IGNORE_TENANT_ID: Final[str] = "ignore"

# --------------------------------------------------------------------------- Redis key 前缀

#: 参数管理 cache key
SYS_CONFIG_KEY: Final[str] = "sys_config:"
#: 字典管理 cache key
SYS_DICT_KEY: Final[str] = "sys_dict:"
#: 登录用户 redis key
LOGIN_TOKEN_KEY: Final[str] = "login_tokens:"
#: 验证码 redis key
CAPTCHA_CODE_KEY: Final[str] = "captcha_codes:"

#: 采购经理角色key
PROCUREMENT_MANAGER_ROLE_KEY: Final[str] = "cgjl_manager"

# --------------------------------------------------------------------------- 其他

#: 字段主键名称
COLUMN_PRIMARY_KEY: Final[str] = "id"
#: 字符串类型键
STRING_CLASS_KEY: Final[str] = "String"
#: 生成代码-字典列表键后缀
GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX: Final[str] = "DictList"
#: 字符-逗号
CHAR_COMMA: Final[str] = ","
#: 空字符
CHAR_BLANK: Final[str] = ""

#: 部门领导
dept_manager_role: Final[str] = "dept_manager"
#: 科室值班人
dept_duty_emp_role: Final[str] = "dept_duty_emp"

#: 重点车俩列表
car_list: Final[str] = "car_list"
#: 重点车俩列表：简称
car_list_jc: Final[str] = "car_list_jc"

#: 省界称重
BORDER_WEIGHING_CAPTURE: Final[str] = "BorderWeighingCapture"
#: 门架抓拍
GANTRY_CAPTURE: Final[str] = "GantryCapture"
#: 省界抓拍
PROV_CAPTURE: Final[str] = "ProvCapture"
#: 服务区抓拍
SERVICE_AREA_CAPTURE: Final[str] = "ServiceAreaCapture"
#: 收费站抓拍
STATION_CAPTURE: Final[str] = "StationCapture"

FeeRecord: Final[str] = "FeeRecord"
FeeStationEnter: Final[str] = "FeeStationEnter"
FeeStationExit: Final[str] = "FeeStationExit"

#: 白名单
white_car_list: Final[str] = "white_car_list"

CAR_WARNING_RULE: Final[str] = "car_warning_rule:"

#: 预警redos
car_warning_list: Final[str] = "car_warning_list"

#: 路线经纬度
lxbh_jdwd: Final[str] = "lxbh_jdwd:"

#: 收费站ip redis
station_ip: Final[str] = "station_ip"

#: 门架ip redis
gantry_ip: Final[str] = "gantry_ip"

#: 可疑车辆
car_uspicious: Final[str] = "car_uspicious"

#: 车辆历史轨迹
car_history_trail: Final[str] = "car_history_trail:"

#: 车辆当前轨迹
car_curent_trail: Final[str] = "car_curent_trail:"

#: 车辆路线规划
car_lxgh: Final[str] = "car_lxgh:"

SECTION_LIST: Final[str] = "section_list"

#: 门架对象redis
gantry_list: Final[str] = "gantry_list"

#: 门架对象redis 数据
gantry_list_data: Final[str] = "gantry_list_data:"

#: 全部路段
section_all: Final[str] = "all"

#: 重点车俩列表
CAR_WARNING_CONFIG_LIST: Final[str] = "car_warning_config_list"
