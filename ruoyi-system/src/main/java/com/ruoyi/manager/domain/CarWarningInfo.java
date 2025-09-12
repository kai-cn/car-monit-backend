package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 预警车辆对象 car_warning_info
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_warning_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarWarningInfo extends BasePlusEntityNew implements Custom {

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

    /** 门架id */
    @Excel(name = "门架id")
    private String gantryStationId;

    /** 门架名称 */
    @Excel(name = "门架名称")
    private String gantrytStation;

    /** 经过时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "经过时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date gantryTime;

    /** 图片(附件ids) */
    @Excel(name = "图片(附件ids)")
    private String fileIds;

    /** 预计下一个通行时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "预计下一个通行时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date nextPassTime;

    /** 预计下一个通行类型 */
    @Excel(name = "预计下一个通行类型")
    private String nextPassType;

    /** 预计下一个通行地址 */
    @Excel(name = "预计下一个通行地址")
    private String nextPassAddress;

    /** 预计下一个通行经度 */
    @Excel(name = "预计下一个通行经度")
    private String nextPassLongitude;

    /** 预计下一个通行维度 */
    @Excel(name = "预计下一个通行维度")
    private String nextPassLatitude;

    /** 所属路线编码 */
    @Excel(name = "所属路线编码")
    private String roadCode;

    /** 所属路线名称 */
    @Excel(name = "所属路线名称")
    private String roadName;

    /** 所属路段编码 */
    @Excel(name = "所属路段编码")
    private String sectionCode;

    /** 所属路段名称 */
    @Excel(name = "所属路段名称")
    private String sectionName;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;

    @TableField(exist = false)
    private String gantryTimeStr;

    // 时间查询
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;

    @TableField(exist = false)
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    @TableField(exist = false)
    @Excel(name = "逃费金额", readConverterExp = "元=")
    private BigDecimal escapedAmount;

}
