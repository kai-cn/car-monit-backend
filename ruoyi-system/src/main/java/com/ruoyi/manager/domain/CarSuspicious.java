package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import io.swagger.annotations.ApiModel;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.util.Date;

/**
 * 可疑车辆对象 car_suspicious
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_suspicious")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
@ApiModel("可疑车辆")
public class CarSuspicious extends BasePlusEntityNew implements Custom {

    /** 车牌颜色（字典：1白色2黑色） */
    @Excel(name = "车牌颜色", readConverterExp = "字=典：1白色2黑色")
    private String plateColor;

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
    @Excel(name = "通行时间", width = 30, dateFormat = "yyyy-MM-dd")
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

    /** 终止门架id */
    @Excel(name = "终止门架id")
    private String outGantryStationId;

    /** 终止门架名称 */
    @Excel(name = "终止门架名称")
    private String outGantrytStation;

    /** 终止经过时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @Excel(name = "终止经过时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date outGantryTime;

    /** 终止图片(附件ids) */
    @Excel(name = "终止图片(附件ids)")
    private String outFileIds;

    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    /** 逃费类型名称 */
    @Excel(name = "逃费类型名称")
    private String escapedTypeName;

    /** 异常通行门架次数 */
    @Excel(name = "异常通行门架次数")
    private Long escapedNum;

    /** 是否为可疑车辆 */
    @Excel(name = "是否为可疑车辆")
    private String isExcept;

    /** 核实状态（0未核实1已核实） */
    @Excel(name = "核实状态", readConverterExp = "0=未核实1已核实")
    private String checkStatus;

    /** 管理中心id */
    @Excel(name = "管理中心id")
    private String orgId;

    /** 管理中心名称 */
    @Excel(name = "管理中心名称")
    private String orgName;

    /** 是否在白名单（0否1是） */
    @Excel(name = "是否在白名单", readConverterExp = "0=否1是")
    private String isWhite;

    /** 白名单原因 */
    @Excel(name = "白名单原因")
    private String whiteRemark;

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

    /** 行驶轨迹josn */
    @Excel(name = "行驶轨迹josn")
    private String trackJosn;

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


    // 车牌号查询
    @TableField(exist = false)
    private String carNoQuery;

    // 时间查询
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;

    // 查询时间
    @TableField(exist = false)
    private String createTimeStr;

    /**
     * 车辆信息
     */
    @TableField(exist = false)
    private CarInfo carInfo;

    /**
     * 车辆核实信息
     */
    @TableField(exist = false)
    private CarSuspiciousCheck carSuspiciousCheck;

}
