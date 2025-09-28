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

    /** 行驶轨迹josn */
    @Excel(name = "行驶轨迹josn")
    private String trackJosn;

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




}
