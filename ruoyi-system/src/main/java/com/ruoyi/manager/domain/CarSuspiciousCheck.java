package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

import java.math.BigDecimal;

/**
 * 可疑车辆人工核实对象 car_suspicious_check
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_suspicious_check")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarSuspiciousCheck extends BasePlusEntity implements Custom {

    /**
     * 可疑车辆id
     */
    private String carSuspiciousId;

    /** 车辆id */
    @Excel(name = "车辆id")
    private String carId;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String carNo;

    /** 是否为可疑车辆 */
    @Excel(name = "是否为可疑车辆")
    private String suspicousFlag;

    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    /** 收费金额 */
    @Excel(name = "收费金额")
    private BigDecimal chargeAmount;

    /** 应缴金额 */
    @Excel(name = "应缴金额")
    private BigDecimal totalAmount;

    /** 差额 */
    @Excel(name = "差额")
    private BigDecimal difAmount;

    /** 附件 */
    @Excel(name = "附件")
    private String attachments;

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

    // 时间查询
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;

    // 查询时间
    @TableField(exist = false)
    private String createTimeStr;

}
