package com.ruoyi.common.constant;

/**
 * 缓存的key 常量
 *
 * @author ruoyi
 */
public class CacheConstants
{
    /**
     * 登录用户 redis key
     */
    public static final String LOGIN_TOKEN_KEY = "login_tokens:";

    /**
     * 验证码 redis key
     */
    public static final String CAPTCHA_CODE_KEY = "captcha_codes:";

    /**
     * 参数管理 cache key
     */
    public static final String SYS_CONFIG_KEY = "sys_config:";

    /**
     * 字典管理 cache key
     */
    public static final String SYS_DICT_KEY = "sys_dict:";

    /**
     * 防重提交 redis key
     */
    public static final String REPEAT_SUBMIT_KEY = "repeat_submit:";

    /**
     * 限流 redis key
     */
    public static final String RATE_LIMIT_KEY = "rate_limit:";

    /**
     * 登录账户密码错误次数 redis key
     */
    public static final String PWD_ERR_CNT_KEY = "pwd_err_cnt:";


    /*---------------------------------- 大屏 ---------------------------------------*/
    /**
     * 交易金额统计
     */
    public static final String AMOUNT_STATISTICS = "big_screen:amount_statistics:";

    /**
     * 今日订单
     */
    public static final String TODAY_ORDER = "big_screen:today_order:";

    /**
     * 货源企业排名
     */
    public static final String ENTERPRISES_RANK = "big_screen:enterprises_rank:";

    /**
     * 订单统计
     */
    public static final String CENTER_STATISTICS = "big_screen:center_statistics:";


    /**
     * 订单定位
     */
    public static final String ORDER_POSITION = "big_screen:order_position:";

    /**
     * 公司定位
     */
    public static final String ENTERPRISE_POSITION = "big_screen:enterprise_position:";


    /**
     * 订单信息
     */
    public static final String ORDER_INFO_POSITION = "big_screen:order_info_position:";

    /**
     * 企业信息
     */
    public static final String ENTERPRISE_INFO_POSITION = "big_screen:enterprise_info_position:";

    /**
     * 订单详情
     */
    public static final String ORDER_DETAIL = "big_screen:order_detail:";

    /**
     * 企业详情
     */
    public static final String ENTERPRISE_DETAIL = "big_screen:enterprise_detail:";


    /**
     * 货物类型统计
     */
    public static final String GOODS_TYPE_STATISTICS = "big_screen:goods_type_statistics:";

    /**
     * 运力统计
     */
    public static final String TRANSPORT_CAPACITY_STATISTICS = "big_screen:transport_capacity_statistics";

    /**
     * 热门航线
     */
    public static final String POPULAR_ROUTES = "big_screen:popular_routes:";

}
