package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
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
 * 省界称重对象 ods_szdn_province_border_vehicle_weight_newstructure
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_szdn_province_border_vehicle_weight_newstructure")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsSzdnProvinceBorderVehicleWeightNewstructure implements Custom {

    /**
     * 数据来源
     */
    @Excel(name = "数据来源")
    private String dataSource;

    /**
     * 数据类型
     */
    @Excel(name = "数据类型")
    private String dataType;

    /**
     * 车牌号
     */
    @Excel(name = "车牌号")
    private String plateNo;

    /**
     * 站点ID
     */
    @Excel(name = "站点ID")
    private String siteId;

    /**
     * 设备地点
     */
    @Excel(name = "设备地点")
    private String location;

    /**
     * 车道号
     */
    @Excel(name = "车道号")
    private Long driveNo;

    /**
     * 车牌颜色索引
     */
    @Excel(name = "车牌颜色索引")
    private String plateColor;

    /**
     * 车牌颜色代码
     */
    @Excel(name = "车牌颜色代码")
    private String plateColorCode;

    /** 车牌颜色名称（sys_dict_data plate_color 字典 label） */
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorName;

    /** 字典标记：UNKNOWN=字典未命中，已回退原始码 */
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorMark;

    /**
     * 车牌类型索引
     */
    @Excel(name = "车牌类型索引")
    private String plateType;

    /**
     * 车牌类型代码
     */
    @Excel(name = "车牌类型代码")
    private String plateTypeCode;

    /**
     * 车辆颜色代号
     */
    @Excel(name = "车辆颜色代号")
    private String vehicleColor;

    /**
     * 车辆颜色代码
     */
    @Excel(name = "车辆颜色代码")
    private String vehicleColorCode;

    /**
     * 车辆类型代号
     */
    @Excel(name = "车辆类型代号")
    private String vehicleType;

    /**
     * 车辆类型代码
     */
    @Excel(name = "车辆类型代码")
    private String vehicleTypeCode;

    /**
     * 车辆速度（km/h）
     */
    @Excel(name = "车辆速度", readConverterExp = "k=m/h")
    private Long vehicleSpeed;

    /**
     * 是否超载
     */
    @Excel(name = "是否超载")
    private Long isOverweight;

    /**
     * 轴数
     */
    @Excel(name = "轴数")
    private Long axleNum;

    /**
     * 超重量（KG）
     */
    @Excel(name = "超重量", readConverterExp = "K=G")
    private Long overWeight;

    /**
     * 重量（KG）
     */
    @Excel(name = "重量", readConverterExp = "K=G")
    private Long vehicleWeight;

    /**
     * 车辆限重（KG）
     */
    @Excel(name = "车辆限重", readConverterExp = "K=G")
    private Long limitWeight;

    /**
     * 检测时间Unix格式
     */
    @Excel(name = "检测时间Unix格式")
    private Long checkTimeUnix;

    /**
     * 检测时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "检测时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date checkTime;

    /**
     * 轴型
     */
    @Excel(name = "轴型")
    private Long axleModel;

    /**
     * 超载率
     */
    @Excel(name = "超载率")
    private Long loadRate;

    /**
     * 轴型详细数据
     */
    @Excel(name = "轴型详细数据")
    private String axleArray;

    /**
     * 图片数组
     */
    @Excel(name = "图片数组")
    private String weighingImagesArry;

    /**
     * 加载时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /**
     * 分类分级
     */
    @Excel(name = "分类分级")
    private Long gradeLevel;

    /**
     * datauuid
     */
    @TableId(value = "datauuid", type = IdType.ASSIGN_UUID)
    @Excel(name = "datauuid")
    private String datauuid;

    private String reserve1;

    private String reserve2;

    private String reserve3;


}
