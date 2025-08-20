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
 * 拆分流水对象 car_split_record
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_split_record")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarSplitRecord extends BasePlusEntity implements Custom {

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

    /** 通信标识（1人工2ETC） */
    @Excel(name = "通信标识", readConverterExp = "1=人工2ETC")
    private String passType;

    /** 入口站id */
    @Excel(name = "入口站id")
    private String inStationId;

    /** 入口站 */
    @Excel(name = "入口站")
    private String inStation;

    /** 入口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "入口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date inTime;

    /** 出口站id */
    @Excel(name = "出口站id")
    private String outStationId;

    /** 出口站 */
    @Excel(name = "出口站")
    private String outStation;

    /** 出口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "出口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date outTime;

    /** 拆分金额 */
    @Excel(name = "拆分金额")
    private BigDecimal amount;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;

    // 时间查询
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;


}
