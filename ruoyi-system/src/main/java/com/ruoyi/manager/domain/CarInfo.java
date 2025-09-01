package com.ruoyi.manager.domain;

import java.math.BigDecimal;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 车辆信息对象 car_info
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarInfo extends BasePlusEntity implements Custom {

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

    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    /** 逃费类型名称 */
    @Excel(name = "逃费类型名称")
    private String escapedTypeName;

    /** 逃费金额（元） */
    @Excel(name = "逃费金额", readConverterExp = "元=")
    private BigDecimal escapedAmount;

    /** 逃费次数(反改) */
    @Excel(name = "逃费次数(反改)")
    private Long escapedNum;

    /** 累计追缴金额（元） */
    @Excel(name = "累计追缴金额", readConverterExp = "元=")
    private BigDecimal returnAmount;

    /** 是否在白名单（0否1是） */
    @Excel(name = "是否在白名单", readConverterExp = "0=否1是")
    private String isWhite;

    /** 白名单原因 */
    @Excel(name = "白名单原因")
    private String whiteRemark;

    /** 图片(附件ids) */
    @Excel(name = "图片(附件ids)")
    private String fileIds;

    /** 车辆品牌 */
    @Excel(name = "车辆品牌")
    private String brand;

    /** 车牌颜色（字典：1白色2黑色） */
    @Excel(name = "车牌颜色", readConverterExp = "字=典：1白色2黑色")
    private String plateColor;

    /** 车牌类型 */
    @Excel(name = "车牌类型")
    private String plateType;

    /** 车辆颜色（字典：1白色2黑色） */
    @Excel(name = "车辆颜色", readConverterExp = "字=典：1白色2黑色")
    private String carColor;

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

    /** 驾驶(1上行2下行3未知) */
    @Excel(name = "驾驶(1上行2下行3未知)")
    private String lastPassCardirection;

    /** 管理中心路段id */
    @Excel(name = "管理中心路段id")
    private String roadSectionId;

    /** 所属路段编码 */
    @Excel(name = "所属路段编码")
    private String sectionCode;

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

    /** 所属管理中心机构编码 */
    @Excel(name = "所属管理中心机构编码")
    private String orgCode;

    /** 管理中心名称 */
    @Excel(name = "管理中心名称")
    private String orgName;

    /** 门架编号（分离） */
    @Excel(name = "门架编号", readConverterExp = "分=离")
    private String gantryCode;

    /** 所属路线编码 */
    @Excel(name = "所属路线编码")
    private String roadCode;

    /** 所属路线名称 */
    @Excel(name = "所属路线名称")
    private String roadName;

    /** 所属收费站编码 */
    @Excel(name = "所属收费站编码")
    private String tollCode;

    /** 所属收费站名称 */
    @Excel(name = "所属收费站名称")
    private String tollName;

    /** 服务区编码 */
    @Excel(name = "服务区编码")
    private String fwqbm;

    /** 服务区名称 */
    @Excel(name = "服务区名称")
    private String fwqmc;

    /** 司机名称 */
    @Excel(name = "司机名称")
    private String linkName;

    /** 联系方式 */
    @Excel(name = "联系方式")
    private String linkPhone;

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

    // 时间查询
    @TableField(exist = false)
    private String applyTime1;

    @TableField(exist = false)
    private String applyTime2;

    // 车牌号查询
    @TableField(exist = false)
    private String carNoQuery;

    // 查询时间
    @TableField(exist = false)
    private String createTimeStr;


}
