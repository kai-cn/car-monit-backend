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
 * 常用路线明细对象 car_route_detail
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_route_detail")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarRouteDetail extends BasePlusEntity implements Custom {

    /** 路线d */
    @Excel(name = "路线d")
    private String routeId;

    /** 车辆id */
    @Excel(name = "车辆id")
    private String carId;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String carNo;

    /** 数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍) */
    @Excel(name = "数据来源(1?架抓拍2收费站抓拍)3服务区抓拍)4省界抓拍)")
    private String dataSource;

    /** 来源名称 */
    @Excel(name = "来源名称")
    private String dataSourceName;

    /** 最后通行时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "最后通行时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date lastPassTime;

    /** 最后通行图片 */
    @Excel(name = "最后通行图片")
    private String lastPassPicture;

    /** 最后通行类型(1?架2收费拍)3服务区) */
    @Excel(name = "最后通行类型(1?架2收费拍)3服务区)")
    private String lastPassType;

    /** 最后通行地址 */
    @Excel(name = "最后通行地址")
    private String lastPassAddress;

    /** 最后通行经度 */
    @Excel(name = "最后通行经度")
    private String lastPassLongitude;

    /** 最后通行维度 */
    @Excel(name = "最后通行维度")
    private String lastPassLatitude;

    /** ⾏驶⽅向(1上行2下行3未知) */
    @Excel(name = "⾏驶⽅向(1上行2下行3未知)")
    private String lastPassCardirection;

    /** 管理中心路段id */
    @Excel(name = "管理中心路段id")
    private String roadSectionId;

    /** 管理中心路段名称 */
    @Excel(name = "管理中心路段名称")
    private String roadSectionName;

    /** 预计下一个通行时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
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

    /** 管理中心id */
    @Excel(name = "管理中心id")
    private String orgId;

    /** 管理中心名称 */
    @Excel(name = "管理中心名称")
    private String orgName;

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
