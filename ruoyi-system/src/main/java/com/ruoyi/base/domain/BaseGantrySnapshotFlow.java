package com.ruoyi.base.domain;

import java.math.BigDecimal;
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
 * 门架抓拍流水对象 base_gantry_snapshot_flow
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_gantry_snapshot_flow")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseGantrySnapshotFlow extends BasePlusEntity implements Custom {

    /** 主键 */
    private String bigId;

    /** 数据类型 */
    @Excel(name = "数据类型")
    private String dataSource;

    /** 设备类型 */
    @Excel(name = "设备类型")
    private String cameraType;

    /** 设备编号 */
    @Excel(name = "设备编号")
    private String deviceId;

    /** 门架编号（分离） */
    @Excel(name = "门架编号", readConverterExp = "分=离")
    private String gantryCode;

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

    /** 所属收费站编码 */
    @Excel(name = "所属收费站编码")
    private String tollCode;

    /** 所属收费站名称 */
    @Excel(name = "所属收费站名称")
    private String tollName;

    /** 所属管理中心机构编码 */
    @Excel(name = "所属管理中心机构编码")
    private String orgCode;

    /** 所属管理中心机构名称 */
    @Excel(name = "所属管理中心机构名称")
    private String orgName;

    /** 门架二进制编号 */
    @Excel(name = "门架二进制编号")
    private String hexCode;

    /** 方向（0: 上行，1: 下行） */
    @Excel(name = "方向", readConverterExp = "0=:,上=行，1:,下=行")
    private Integer direction;

    /** 桩号 */
    @Excel(name = "桩号")
    private String pileno;

    /** 经度 */
    @Excel(name = "经度")
    private BigDecimal lon;

    /** 纬度 */
    @Excel(name = "纬度")
    private BigDecimal lat;

    /** 设备IP */
    @Excel(name = "设备IP")
    private String deviceIp;

    /** 站点ID */
    @Excel(name = "站点ID")
    private Long siteId;

    /** 车道编号 */
    @Excel(name = "车道编号")
    private Integer laneId;

    /** 抓拍时间Unix格式 */
    @Excel(name = "抓拍时间Unix格式")
    private Long snapshotTimeUnix;

    /** 抓拍时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "抓拍时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date snapshotTime;

    /** 接收时间Unix格式 */
    @Excel(name = "接收时间Unix格式")
    private Long receivedTimeUnix;

    /** 接收时间 */
    @Excel(name = "接收时间")
    private String receivedTime;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String plateNumber;

    /** 车牌颜色 */
    @Excel(name = "车牌颜色")
    private String plateColor;

    /** 车牌颜色编码 */
    @Excel(name = "车牌颜色编码")
    private Integer plateColorCode;

    /** 车牌类型 */
    @Excel(name = "车牌类型")
    private String plateType;

    /** 车牌类型编码 */
    @Excel(name = "车牌类型编码")
    private Integer plateTypeCode;

    /** 车牌置信度 */
    @Excel(name = "车牌置信度")
    private Integer plateConfidence;

    /** 车辆品牌 */
    @Excel(name = "车辆品牌")
    private String carBrand;

    /** 车辆颜色 */
    @Excel(name = "车辆颜色")
    private String carColor;

    /** 车辆颜色编码 */
    @Excel(name = "车辆颜色编码")
    private Integer carColorCode;

    /** 车辆类型 */
    @Excel(name = "车辆类型")
    private String carType;

    /** 车辆类型编码 */
    @Excel(name = "车辆类型编码")
    private Integer carTypeCode;

    /** 行驶方向 */
    @Excel(name = "行驶方向")
    private String carDirection;

    /** 图片路径 */
    @Excel(name = "图片路径")
    private String snapPicturePath;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private Integer gradeLevel;

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
