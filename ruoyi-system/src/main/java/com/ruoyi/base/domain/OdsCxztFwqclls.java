package com.ruoyi.base.domain;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.Custom;

/**
 * 服务区车辆流水对象 ods_cxzt_fwqclls
 *
 * @author ruoyi
 * @date 2025-10-20
 */
@Data
@TableName("ods_cxzt_fwqclls")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsCxztFwqclls implements Custom {

    /** $column.columnComment */
    @Excel(name = "${comment}", readConverterExp = "$column.readConverterExp()")
    private Long bigId;

    /** $column.columnComment */
    @Excel(name = "${comment}", readConverterExp = "$column.readConverterExp()")
    private String datauuid;

    /** 抓拍照片url */
    @Excel(name = "抓拍照片url")
    private String targetpicurl;

    /** 车辆品牌 */
    @Excel(name = "车辆品牌")
    private String vehiclebrand;

    /** 车牌照片 */
    @Excel(name = "车牌照片")
    private String platepicurl;

    /** 车类型 */
    @Excel(name = "车类型")
    private String rollvehiclestype;

    /** 车牌 */
    @Excel(name = "车牌")
    private String plateno;

    /** 方向名称 */
    @Excel(name = "方向名称")
    private String directionname;

    /** 车牌类型 */
    @Excel(name = "车牌类型")
    private String platetype;

    /** 是否危化品车 */
    @Excel(name = "是否危化品车")
    private String dangmark;

    /** 通过时间（分区字段） */
    @Excel(name = "通过时间", readConverterExp = "分=区字段")
    private Date crosstime;

    /** 坐标 */
    @Excel(name = "坐标")
    private String axles;

    /** 设备名称 */
    @Excel(name = "设备名称")
    private String devicename;

    /** IP地址 */
    @Excel(name = "IP地址")
    private String ipaddress;

    /** 服务区名称 */
    @Excel(name = "服务区名称")
    private String servicename;

    /** 车辆类型 */
    @Excel(name = "车辆类型")
    private String vehicletype;

    /** 加载时间 */
    @Excel(name = "加载时间")
    private String loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private String gradeLevel;


}
