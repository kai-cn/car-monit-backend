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
 * 门架抓拍流水对象 ods_rt_szdn_snapshot_flow_addcode
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Data
@TableName("ods_rt_szdn_snapshot_flow_addcode")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsRtSzdnSnapshotFlowAddcode implements Custom {

    /** 主键 */
    private String bigId;

    /** 数据类型 */
    @Excel(name = "数据类型")
    private String datasource;

    /** 设备类型 */
    @Excel(name = "设备类型")
    private String cameratype;

    /** 设备编号 */
    @Excel(name = "设备编号")
    private String deviceid;

    /** 门架编号（分离） */
    @Excel(name = "门架编号", readConverterExp = "分=离")
    private String gantrycode;

    /** 门架名称 */
    @Excel(name = "门架名称")
    private String gantryname;

    /** 所属路线编码 */
    @Excel(name = "所属路线编码")
    private String roadcode;

    /** 所属路线名称 */
    @Excel(name = "所属路线名称")
    private String roadname;

    /** 所属路段编码 */
    @Excel(name = "所属路段编码")
    private String sectioncode;

    /** 所属路段名称 */
    @Excel(name = "所属路段名称")
    private String sectionname;

    /** 所属收费站编码 */
    @Excel(name = "所属收费站编码")
    private String tollcode;

    /** 所属收费站名称 */
    @Excel(name = "所属收费站名称")
    private String tollname;

    /** 所属管理中心机构编码 */
    @Excel(name = "所属管理中心机构编码")
    private String orgcode;

    /** 所属管理中心机构名称 */
    @Excel(name = "所属管理中心机构名称")
    private String orgname;

    /** 方向（0: 上行，1: 下行） */
    @Excel(name = "方向", readConverterExp = "0=:,上=行，1:,下=行")
    private Integer direction;

    /** 门架二进制编号 */
    @Excel(name = "门架二进制编号")
    private String hexcode;

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
    private String deviceip;

    /** 站点ID */
    @Excel(name = "站点ID")
    private Long siteid;

    /** 车道编号 */
    @Excel(name = "车道编号")
    private Integer laneid;

    /** 抓拍时间Unix格式 */
    @Excel(name = "抓拍时间Unix格式")
    private Long snapshottimeunix;

    /** $column.columnComment */
    @Excel(name = "${comment}", readConverterExp = "$column.readConverterExp()")
    private Date snapshottime;

    /** 接收时间Unix格式 */
    @Excel(name = "接收时间Unix格式")
    private Long receivedtimeunix;

    /** 接收时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receivedtime;

    /** 车牌号 */
    @Excel(name = "车牌号")
    private String platenumber;

    /** 车牌颜色 */
    @Excel(name = "车牌颜色")
    private String platecolor;

    /** 车牌颜色编码 */
    @Excel(name = "车牌颜色编码")
    private Integer platecolorcode;

    /** 车牌类型 */
    @Excel(name = "车牌类型")
    private String platetype;

    /** 车牌类型编码 */
    @Excel(name = "车牌类型编码")
    private Integer platetypecode;

    /** 车牌置信度 */
    @Excel(name = "车牌置信度")
    private Integer plateconfidence;

    /** 车辆品牌 */
    @Excel(name = "车辆品牌")
    private String carbrand;

    /** 车辆颜色 */
    @Excel(name = "车辆颜色")
    private String carcolor;

    /** 车辆颜色编码 */
    @Excel(name = "车辆颜色编码")
    private Integer carcolorcode;

    /** 车辆类型 */
    @Excel(name = "车辆类型")
    private String cartype;

    /** 车辆类型编码 */
    @Excel(name = "车辆类型编码")
    private Integer cartypecode;

    /** 行驶方向 */
    @Excel(name = "行驶方向")
    private String cardirection;

    /** 图片路径 */
    @Excel(name = "图片路径")
    private String snappicturepath;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadtime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private Integer gradelevel;


}
