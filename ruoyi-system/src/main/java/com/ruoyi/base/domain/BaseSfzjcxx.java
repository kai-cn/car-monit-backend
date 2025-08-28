package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * 收费站基础信息位置对象 base_sfzjcxx
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_sfzjcxx")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseSfzjcxx extends BasePlusEntityNew implements Custom {

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

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 备注 */
    @Excel(name = "备注")
    private String remark2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;


}
