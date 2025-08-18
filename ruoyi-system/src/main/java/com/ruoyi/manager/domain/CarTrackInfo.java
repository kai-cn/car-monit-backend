package com.ruoyi.manager.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 车辆行驶轨迹对象 car_track_info
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_track_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarTrackInfo extends BasePlusEntity implements Custom {

    /** 车辆id */
    @Excel(name = "车辆id")
    private String carId;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String carNo;

    /** 经度 */
    @Excel(name = "经度")
    private String longitude;

    /** 维度 */
    @Excel(name = "维度")
    private String latitude;

    /** 设备类型 */
    @Excel(name = "设备类型")
    private String deviceType;

    /** 设备编号 */
    @Excel(name = "设备编号")
    private String deviceNo;

    /** 车道编号 */
    @Excel(name = "车道编号")
    private String laneNo;

    /** 抓拍时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "抓拍时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date snapTime;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receiveTime;

    /** 抓拍图片 */
    @Excel(name = "抓拍图片")
    private String snapPic;

    /** 管理中心路段id */
    @Excel(name = "管理中心路段id")
    private String roadSectionId;

    /** 管理中心路段名称 */
    @Excel(name = "管理中心路段名称")
    private String roadSectionName;

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
