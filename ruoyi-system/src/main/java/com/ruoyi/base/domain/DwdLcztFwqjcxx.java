package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

import java.util.List;

/**
 * 服务区基础信息对象 dwd_lczt_fwqjcxx
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("dwd_lczt_fwqjcxx")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class DwdLcztFwqjcxx implements Custom {

    /** 代理主键 */
    @TableId(value = "agent_pk", type = IdType.INPUT)
    private String agentPk;

    /** 源系统主键 */
    @Excel(name = "源系统主键")
    private String yxtzj;

    /** 服务区编码 */
    @Excel(name = "服务区编码")
    private String fwqbm;

    /** 服务区名称 */
    @Excel(name = "服务区名称")
    private String fwqmc;

    /** 纬度 */
    @Excel(name = "纬度")
    private String wd;

    /** 方向名称 */
    @Excel(name = "方向名称")
    private String fxmc;

    /** 方向代码 */
    @Excel(name = "方向代码")
    private String fxdm;

    /** 经度 */
    @Excel(name = "经度")
    private String jd;

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
    private String sczhkgs;

    /** 所处桩号(数值格式) */
    @Excel(name = "所处桩号(数值格式)")
    private String sczhszgs;

    /** 所属管理中心编码 */
    @Excel(name = "所属管理中心编码")
    private String ssglzxbm;

    /** 所属管理中心名称 */
    @Excel(name = "所属管理中心名称")
    private String ssglzxmc;

    /** 行政区划名称 */
    @Excel(name = "行政区划名称")
    private String xzqhmc;

    /** 营业日期 */
    @Excel(name = "营业日期")
    private String yyrq;

    /** 车位数 */
    @Excel(name = "车位数")
    private String cws;

    /** 是否设置了卡口 */
    @Excel(name = "是否设置了卡口")
    private String sfszlkk;

    /** 充电桩数 */
    @Excel(name = "充电桩数")
    private String cdzs;

    /** 是否餐饮服务 */
    @Excel(name = "是否餐饮服务")
    private String sfcyfw;

    /** 是否提供住宿服务 */
    @Excel(name = "是否提供住宿服务")
    private String sftgzsfw;

    /** 是否提供汽修服务 */
    @Excel(name = "是否提供汽修服务")
    private String sftgqxfw;

    /** 是否提供超市服务 */
    @Excel(name = "是否提供超市服务")
    private String sftgcsfw;

    /** 是否提供加油服务 */
    @Excel(name = "是否提供加油服务")
    private String sftgjyfw;

    /** 面积(平方米) */
    @Excel(name = "面积(平方米)")
    private String mj;

    /** 是否提供厕所服务 */
    @Excel(name = "是否提供厕所服务")
    private String sftgcshfw;

    /** 行政区划代码 */
    @Excel(name = "行政区划代码")
    private String xzqhdm;

    /** 使用年限 */
    @Excel(name = "使用年限")
    private String synx;

    /** 来源系统 */
    @Excel(name = "来源系统")
    private String lyxt;

    /** 加载日期 */
    @Excel(name = "加载日期")
    private String loadTime;

    /** 全字段MD5 */
    @Excel(name = "全字段MD5")
    private String allColPk;


    /**
     * 路线数组
     */
    @TableField(exist = false)
    List<String> sectionCodeList;


}
