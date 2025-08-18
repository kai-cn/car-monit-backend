package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 预警规则对象 car_warning_rule
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_warning_rule")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarWarningRule extends BasePlusEntity implements Custom {

    /** 规则名称 */
    @Excel(name = "规则名称")
    private String ruleName;

    /** 预警范围id(包含的路段范围) */
    @Excel(name = "预警范围id(包含的路段范围)")
    private String noticeRangeId;

    /** 预警范围(包含的路段范围) */
    @Excel(name = "预警范围(包含的路段范围)")
    private String noticeRangeAnme;

    /** 通知 */
    @Excel(name = "通知")
    private String notice;

    /** 通知方式 */
    @Excel(name = "通知方式")
    private String noticeType;

    /** 通知人员id */
    @Excel(name = "通知人员id")
    private String noticeUserId;

    /** 通知人员 */
    @Excel(name = "通知人员")
    private String noticeUserName;

    /** 所属站/所 */
    @Excel(name = "所属站/所")
    private String orgId;

    /** 所属站/所 */
    @Excel(name = "所属站/所")
    private String orgName;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;

    /** 备注 */
    @Excel(name = "备注")
    private String remark;

}
