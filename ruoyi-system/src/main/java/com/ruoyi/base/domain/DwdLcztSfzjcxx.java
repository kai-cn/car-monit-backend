package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 收费站基础信息对象 dwd_lczt_sfzjcxx
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("dwd_lczt_sfzjcxx")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class DwdLcztSfzjcxx implements Custom {

    /** 代理主键 */
    private String agentPk;

    /** 源系统主键 */
    @Excel(name = "源系统主键")
    private String yxtzj;

    /** 收费站代码 */
    @Excel(name = "收费站代码")
    private String sfzdm;

    /** 收费站名称 */
    @Excel(name = "收费站名称")
    private String sfzmc;

    /** 经度 */
    @Excel(name = "经度")
    private String jd;

    /** 纬度 */
    @Excel(name = "纬度")
    private String wd;

    /** 所属路线编号 */
    @Excel(name = "所属路线编号")
    private String sslxbh;

    /** 所属路线名称 */
    @Excel(name = "所属路线名称")
    private String sslxmc;

    /** 所属路段编号 */
    @Excel(name = "所属路段编号")
    private String ssldbh;

    /** 所属路段名称 */
    @Excel(name = "所属路段名称")
    private String ssldmc;

    /** 所处桩号(K格式) */
    @Excel(name = "所处桩号(K格式)")
    private String sczhK;

    /** 所处桩号(数值格式) */
    @Excel(name = "所处桩号(数值格式)")
    private String sczhN;

    /** 所属管理中心编码 */
    @Excel(name = "所属管理中心编码")
    private String ssglzxbm;

    /** 所属管理中心名称 */
    @Excel(name = "所属管理中心名称")
    private String ssglzxmc;

    /** 来源系统 */
    @Excel(name = "来源系统")
    private String lyxt;

    /** 加载日期 */
    @Excel(name = "加载日期")
    private String loadTime;

    /** 全字段MD5 */
    @Excel(name = "全字段MD5")
    private String allColPk;


}
