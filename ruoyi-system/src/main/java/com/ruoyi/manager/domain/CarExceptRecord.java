package com.ruoyi.manager.domain;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 异常车辆流水对象 car_except_record
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_except_record")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarExceptRecord extends BasePlusEntity implements Custom {


    /** 车辆id */
    @Excel(name = "车辆id")
    private String carId;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String carNo;

    /** 车型 */
    @Excel(name = "车型")
    private String carType;

    /** 车种 */
    @Excel(name = "车种")
    private String carVehicle;

    /** 轴数 */
    @Excel(name = "轴数")
    private Long carNum;

    /** 通行标识（1人工2ETC） */
    @Excel(name = "通行标识", readConverterExp = "1=人工2ETC")
    private String passType;

    /** 入口站id */
    @Excel(name = "入口站id")
    private String inStationId;

    /** 入口站 */
    @Excel(name = "入口站")
    private String inStation;

    /** 入口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "入口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date inTime;

    /** 出口站id */
    @Excel(name = "出口站id")
    private String outStationId;

    /** 出口站 */
    @Excel(name = "出口站")
    private String outStation;

    /** 出口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "出口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date outTime;

    /** 应缴金额 */
    @Excel(name = "应缴金额")
    private BigDecimal totalAmount;

    /** 收费金额 */
    @Excel(name = "收费金额")
    private BigDecimal chargeAmount;

    /** 差额 */
    @Excel(name = "差额")
    private BigDecimal difAmount;

    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    /** 备注 */
    @Excel(name = "备注")
    private String remark;


    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 状态（0未补交1全部补交） */
    @Excel(name = "状态", readConverterExp = "0=未补交1全部补交")
    private String status;

    // 时间查询 :入口时间
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;


    // 时间查询：出口时间
    @TableField(exist = false)
    private String applyTime3;

    @TableField(exist = false)
    private String applyTime4;

    // 查询时间
    @TableField(exist = false)
    private String createTimeStr;

    // 录入单位
    @TableField(exist = false)
    private String orgId;

    // 补缴状态 0未补缴
    @TableField(exist = false)
    private String supplementaryStatus = "0";

    /** 异常流水ids */
    @Excel(name = "异常流水ids")
    @TableField(exist = false)
    private String exceptIds;



}
