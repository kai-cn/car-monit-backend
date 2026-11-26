package com.ruoyi.common.constant;

import java.util.Locale;
import io.jsonwebtoken.Claims;

/**
 * 通用常量信息
 *
 * @author ruoyi
 */
public class Constants
{
    /**
     * UTF-8 字符集
     */
    public static final String UTF8 = "UTF-8";

    /**
     * GBK 字符集
     */
    public static final String GBK = "GBK";

    /**
     * 系统语言
     */
    public static final Locale DEFAULT_LOCALE = Locale.SIMPLIFIED_CHINESE;

    /**
     * www主域
     */
    public static final String WWW = "www.";

    /**
     * http请求
     */
    public static final String HTTP = "http://";

    /**
     * https请求
     */
    public static final String HTTPS = "https://";

    /**
     * 通用成功标识
     */
    public static final String SUCCESS = "0";

    /**
     * 通用失败标识
     */
    public static final String FAIL = "1";

    /**
     * 登录成功
     */
    public static final String LOGIN_SUCCESS = "Success";

    /**
     * 注销
     */
    public static final String LOGOUT = "Logout";

    /**
     * 注册
     */
    public static final String REGISTER = "Register";

    /**
     * 登录失败
     */
    public static final String LOGIN_FAIL = "Error";

    /**
     * 所有权限标识
     */
    public static final String ALL_PERMISSION = "*:*:*";

    /**
     * 管理员角色权限标识
     */
    public static final String SUPER_ADMIN = "admin";

    /**
     * 角色权限分隔符
     */
    public static final String ROLE_DELIMETER = ",";

    /**
     * 权限标识分隔符
     */
    public static final String PERMISSION_DELIMETER = ",";

    /**
     * 验证码有效期（分钟）
     */
    public static final Integer CAPTCHA_EXPIRATION = 2;

    /**
     * 令牌
     */
    public static final String TOKEN = "token";

    /**
     * 令牌前缀
     */
    public static final String TOKEN_PREFIX = "Bearer ";

    /**
     * 令牌前缀
     */
    public static final String LOGIN_USER_KEY = "login_user_key";

    /**
     * 用户ID
     */
    public static final String JWT_USERID = "userid";

    /**
     * 用户名称
     */
    public static final String JWT_USERNAME = Claims.SUBJECT;

    /**
     * 用户头像
     */
    public static final String JWT_AVATAR = "avatar";

    /**
     * 创建时间
     */
    public static final String JWT_CREATED = "created";

    /**
     * 用户权限
     */
    public static final String JWT_AUTHORITIES = "authorities";

    /**
     * 资源映射路径 前缀
     */
    public static final String RESOURCE_PREFIX = "/profile";

    /**
     * RMI 远程方法调用
     */
    public static final String LOOKUP_RMI = "rmi:";

    /**
     * LDAP 远程方法调用
     */
    public static final String LOOKUP_LDAP = "ldap:";

    /**
     * LDAPS 远程方法调用
     */
    public static final String LOOKUP_LDAPS = "ldaps:";

    /**
     * 自动识别json对象白名单配置（仅允许解析的包名，范围越小越安全）
     */
    public static final String[] JSON_WHITELIST_STR = { "org.springframework", "com.ruoyi" };

    /**
     * 定时任务白名单配置（仅允许访问的包名，如其他需要可以自行添加）
     */
    public static final String[] JOB_WHITELIST_STR = { "com.ruoyi.quartz.task" };

    /**
     * 定时任务违规的字符
     */
    public static final String[] JOB_ERROR_STR = { "java.net.URL", "javax.naming.InitialContext", "org.yaml.snakeyaml",
            "org.springframework", "org.apache", "com.ruoyi.common.utils.file", "com.ruoyi.common.config", "com.ruoyi.generator" };

    /**
     * 流程结果-委托
     */
    public static final String FLOW_RESULT_ENTRUST_KEY = "entrust";

    /**
     * 流程结果内容前缀-委托
     */
    public static final String FLOW_RESULT_CONTEXT_PREFIX = "委托";

    /**
     * 流程结果内容后缀-委托
     */
    public static final String FLOW_RESULT_CONTEXT_SUFFIX = "办理";

    /**
     * 流程委托
     */
    public static final String FLOW_ENTRUST_NAME = "委托";

    /**
     * 忽略流程中的 tenant_id 查询条件
     */
    public static final String FLOW_IGNORE_TENANT_ID = "ignore";


    /**
     * 参数管理 cache key
     */
    public static final String SYS_CONFIG_KEY = "sys_config:";

    /**
     * 字典管理 cache key
     */
    public static final String SYS_DICT_KEY = "sys_dict:";


    /**
     * 登录用户 redis key
     */
    public static final String LOGIN_TOKEN_KEY = "login_tokens:";

    /**
     * 采购经理角色key
     */
    public static final String PROCUREMENT_MANAGER_ROLE_KEY = "cgjl_manager";


    /**
     * 验证码 redis key
     */
    public static final String CAPTCHA_CODE_KEY = "captcha_codes:";

    /**
     * 字段主键名称
     */
    public static final String COLUMN_PRIMARY_KEY = "id";


    /**
     * 字符串类型键
     */
    public static final String STRING_CLASS_KEY = "String";

    /**
     * 生成代码-字典列表键后缀
     */
    public static final String GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX = "DictList";


    /**
     * 字符-逗号
     */
    public static final String CHAR_COMMA = ",";


    /**
     * 空字符
     */
    public static final String CHAR_BLANK = "";


    /**
     * 部门领导
     */
    public static final String dept_manager_role = "dept_manager";

    /**
     * 科室值班人
     */
    public static final String dept_duty_emp_role = "dept_duty_emp";


    /**
     * 重点车俩列表
     */
    public static final String car_list = "car_list";

    /**
     * 重点车俩列表：简称
     */
    public static final String car_list_jc = "car_list_jc";

    /**
     * 重点车俩列表版本号（用于地图点位索引失效判断）
     */
    public static final String car_list_version = "car_list_version";



    public static final String BORDER_WEIGHING_CAPTURE = "BorderWeighingCapture";  // 省界称重
    public static final String GANTRY_CAPTURE = "GantryCapture";  // 门架抓拍
    public static final String PROV_CAPTURE = "ProvCapture"; // 省界抓拍
    public static final String SERVICE_AREA_CAPTURE = "ServiceAreaCapture"; // 服务区抓拍
    public static final String STATION_CAPTURE = "StationCapture";   // 收费站抓拍

    public static final String FeeRecord = "FeeRecord";
    public static final String FeeStationEnter = "FeeStationEnter";
    public static final String FeeStationExit = "FeeStationExit";


    /**
     * 白名单
     */
    public static final String white_car_list = "white_car_list";

    public static final String CAR_WARNING_RULE = "car_warning_rule:";


    /**
     * 预警redos
     */
    public static final String car_warning_list = "car_warning_list";


    /**
     * 路线经纬度
     */
    public static final String lxbh_jdwd = "lxbh_jdwd:";


    /**
     * 收费站ip redis
     */
    public static final String station_ip = "station_ip";


    /**g
     * 门架ip redis
     */
    public static final String gantry_ip = "gantry_ip";

    /**
     * 可疑车辆
     */
    public static final String car_uspicious = "car_uspicious";


    /**
     * 车辆历史轨迹
     */
    public static final String car_history_trail = "car_history_trail:";

    /**
     * 车辆历史轨迹“当前页”缓存（backend 私有）。
     *
     * <p>{@link #car_history_trail} 是 api 侧 TrackTask 只读消费的“全量历史”键，
     * backend 在线查询只拿到当前页，不能写入该键，否则会被 api 当成旧全量合并。</p>
     */
    public static final String car_history_trail_page = "car_history_trail_page:";


    /**
     * 车辆当前轨迹
     */
    public static final String car_curent_trail = "car_curent_trail:";


    /**
     * 车辆路线规划
     */
    public static final String car_lxgh = "car_lxgh:";


    public static final String SECTION_LIST = "section_list";

    /**
     * 门架对象redis
     */
    public static final String gantry_list = "gantry_list";

    /**
     * 门架对象redis 数据
     */
    public static final String gantry_list_data = "gantry_list_data:";


    /**
     * 全部路段
     */
    public static final String section_all = "all";


    /**
     * 重点车俩列表
     */
    public static final String CAR_WARNING_CONFIG_LIST = "car_warning_config_list";



}
