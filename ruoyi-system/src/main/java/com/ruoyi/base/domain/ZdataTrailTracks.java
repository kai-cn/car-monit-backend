package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.math.BigDecimal;
import java.util.Date;

/**
 * 轨迹数据对象 zdata_trail_tracks
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("zdata_trail_tracks")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class ZdataTrailTracks implements Custom {

    /**
     * 唯一标识符（分布键，用于保证轨迹全局唯一）
     */
    @TableId(value = "uuid", type = IdType.ASSIGN_UUID)
    @Excel(name = "唯一标识符", readConverterExp = "分=布键，用于保证轨迹全局唯一")
    private String uuid;

    /**
     * 轨迹类型（如 0=不完整, 1=完整，后续可扩展更多状态码）
     */
    @Excel(name = "轨迹类型", readConverterExp = "如=,0==不完整,,1==完整，后续可扩展更多状态码")
    private Integer type;

    /**
     * 轨迹点数量（记录该轨迹包含多少个点）
     */
    @Excel(name = "轨迹点数量", readConverterExp = "记=录该轨迹包含多少个点")
    private Long pointCount;

    /**
     * 车牌唯一标识（可脱敏/加密存储，用于车辆关联）
     */
    @Excel(name = "车牌唯一标识", readConverterExp = "可=脱敏/加密存储，用于车辆关联")
    private String plateKey;

    /**
     * 进入时间（分区键，月度分区粒度）
     */
    @Excel(name = "进入时间", readConverterExp = "分=区键，月度分区粒度")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date enterTime;

    /**
     * 离开时间（轨迹结束时间）
     */
    @Excel(name = "离开时间", readConverterExp = "轨=迹结束时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date exitTime;

    /**
     * 轨迹点集合，推荐存 JSON 格式，包含坐标/时间/速度等信息
     */
    @Excel(name = "轨迹点集合，推荐存 JSON 格式，包含坐标/时间/速度等信息")
    private String trailPoints;

    /** 进入位置code */
    @Excel(name = "进入位置code")
    private String enterLocationcode;

    /** 离开位置code */
    @Excel(name = "离开位置code")
    private String exitLocationcode;

    /** 集合详情 */
    @Excel(name = "集合详情")
    private String trackJosn;

    /** 入口车轴数 */
    @Excel(name = "入口车轴数")
    private Integer enaxlecount;

    /** 入口车道编号 */
    @Excel(name = "入口车道编号")
    private String entolllaneid;

    /** 入口收费站编号 */
    @Excel(name = "入口收费站编号")
    private String entollstationid;

    /** 入口收费站名称 */
    @Excel(name = "入口收费站名称")
    private String entollstationname;

    /** 入口车型分类（收费车型） */
    @Excel(name = "入口车型分类", readConverterExp = "收=费车型")
    private String envehicleclass;

    /** 入口车辆编号 */
    @Excel(name = "入口车辆编号")
    private String envehicleid;

    /** 入口车辆类型代码 */
    @Excel(name = "入口车辆类型代码")
    private String envehicletype;

    /** 入口称重（kg） */
    @Excel(name = "入口称重", readConverterExp = "k=g")
    private BigDecimal enweight;

    /** 出口车道编号 */
    @Excel(name = "出口车道编号")
    private String extolllaneid;

    /** 出口收费站编号 */
    @Excel(name = "出口收费站编号")
    private String extollstationid;

    /** 出口收费站名称 */
    @Excel(name = "出口收费站名称")
    private String extollstationname;

    /** 出口车型分类 */
    @Excel(name = "出口车型分类")
    private String exvehicleclass;

    /** 出口车辆编号 */
    @Excel(name = "出口车辆编号")
    private String exvehicleid;

    /** 出口车辆类型代码 */
    @Excel(name = "出口车辆类型代码")
    private String exvehicletype;

    /** 出口称重（kg） */
    @Excel(name = "出口称重", readConverterExp = "k=g")
    private BigDecimal exweight;

    /** 入口收费站经度 */
    @Excel(name = "入口收费站经度")
    private String startLon;

    /** 入口收费站维度 */
    @Excel(name = "入口收费站维度")
    private String stratLat;

    /** 出口收费站经度 */
    @Excel(name = "出口收费站经度")
    private String endLon;

    /** 出口收费站维度 */
    @Excel(name = "出口收费站维度")
    private String endLat;


    // 入栈口
    @TableField(exist = false)
    private String firtStationCode;

    // 入栈口名称
    @TableField(exist = false)
    private String firtStationName;

    // 入栈口时间
    @TableField(exist = false)
    private String firtStationTime;


    /** 车牌颜色（字典：1白色2黑色） */
    @TableField(exist = false)
    private String plateColor;

    /** 车型 */
    @TableField(exist = false)
    private String carType;

    /** 车牌号 */
    @TableField(exist = false)
    private String carNo;

    /** 车种 */
    @TableField(exist = false)
    private String carVehicle;

    /** 轴数 */
    @TableField(exist = false)
    private Long carNum;

    /** 逃费类型 */
    @TableField(exist = false)
    private String escapedType;

    /** 通行标识 */
    @TableField(exist = false)
    private String passType;


    /** 逃费类型：原因 */
    @TableField(exist = false)
    private String escapedTypeRemark;

    /** 申请时间1 */
    @TableField(exist = false)
    private String applyTime1;

    /** 申请时间2 */
    @TableField(exist = false)
    private String applyTime2;

    /** 是否常用路线 */
    @TableField(exist = false)
    private String isCylx;

    /** 标识 */
    @TableField(exist = false)
    private String flag;


    /** 入口收费站经度 */
    @Excel(name = "入口收费站经度")
    @TableField(exist = false)
    private BigDecimal startLonDec;

    //** 入口收费站维度 *//*
    @Excel(name = "入口收费站维度")
    @TableField(exist = false)
    private BigDecimal stratLatDec;

    //** 出口收费站经度 *//*
    @Excel(name = "出口收费站经度")
    @TableField(exist = false)
    private BigDecimal endLonDec;

    //** 出口收费站维度 *//*
    @Excel(name = "出口收费站维度")
    @TableField(exist = false)
    private BigDecimal endLatDec;


}
