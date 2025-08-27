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
 * 门架交易查询对象 gantry_trade_info
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("gantry_trade_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class GantryTradeInfo extends BasePlusEntity implements Custom {

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

    /** 入门架id */
    @Excel(name = "入门架id")
    private String inStationId;

    /** 入门架 */
    @Excel(name = "入门架")
    private String inStation;

    /** 入门时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "入门时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date inTime;

    /** 出口门架id */
    @Excel(name = "出口门架id")
    private String outStationId;

    /** 出口门架 */
    @Excel(name = "出口门架")
    private String outStation;

    /** 出口时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "出口时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date outTime;

    /** 交易类型（字典：1出口交易2逃费补缴） */
    @Excel(name = "交易类型", readConverterExp = "字=典：1出口交易2逃费补缴")
    private String chargeType;

    /** 收费金额 */
    @Excel(name = "收费金额")
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
