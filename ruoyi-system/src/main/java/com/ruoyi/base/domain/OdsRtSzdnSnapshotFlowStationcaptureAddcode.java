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
 * 收费站抓拍对象 ods_rt_szdn_snapshot_flow_stationcapture_addcode
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_rt_szdn_snapshot_flow_stationcapture_addcode")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsRtSzdnSnapshotFlowStationcaptureAddcode implements Custom {

    @TableId(value = "bigId", type = IdType.ASSIGN_UUID)
    private Long bigId;

    /**
     * 数据类型
     */
    @Excel(name = "数据类型")
    private String datasource;

    /**
     * 设备类型
     */
    @Excel(name = "设备类型")
    private String cameratype;

    /**
     * 设备编号
     */
    @Excel(name = "设备编号")
    private String deviceid;

    /**
     * 设备IP
     */
    @Excel(name = "设备IP")
    private String deviceip;

    /**
     * 收费站编码
     */
    @Excel(name = "收费站编码")
    private String tollcode;

    /**
     * 收费站名称
     */
    @Excel(name = "收费站名称")
    private String tollname;

    /**
     * 组织机构编码
     */
    @Excel(name = "组织机构编码")
    private Long orgcode;

    /**
     * 站点ID
     */
    @Excel(name = "站点ID")
    private Long siteid;

    /**
     * 车道编号
     */
    @Excel(name = "车道编号")
    private Integer laneid;

    /**
     * 抓拍时间Unix格式
     */
    @Excel(name = "抓拍时间Unix格式")
    private Long snapshottimeunix;

    /**
     * 抓拍时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "抓拍时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date snapshottime;

    /**
     * 接收时间Unix格式
     */
    @Excel(name = "接收时间Unix格式")
    private Long receivedtimeunix;

    /**
     * 接收时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "接收时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date receivedtime;

    /**
     * 车牌号
     */
    @Excel(name = "车牌号")
    private String platenumber;

    /**
     * 车牌颜色编码
     */
    @Excel(name = "车牌颜色编码")
    private Integer platecolorcode;

    /**
     * 车牌颜色
     */
    @Excel(name = "车牌颜色")
    private String platecolor;

    /** 车牌颜色名称（sys_dict_data plate_color 字典 label） */
    @Excel(name = "车牌颜色名称")
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorName;

    /** 字典标记：UNKNOWN=字典未命中，已回退原始码 */
    @com.baomidou.mybatisplus.annotation.TableField(exist = false)
    private String plateColorMark;

    /**
     * 车牌类型编码
     */
    @Excel(name = "车牌类型编码")
    private Integer platetypecode;

    /**
     * 车牌类型
     */
    @Excel(name = "车牌类型")
    private String platetype;

    /**
     * 车牌置信度
     */
    @Excel(name = "车牌置信度")
    private Integer plateconfidence;

    /**
     * 车辆品牌
     */
    @Excel(name = "车辆品牌")
    private String carbrand;

    /**
     * 车辆颜色编码
     */
    @Excel(name = "车辆颜色编码")
    private Integer carcolorcode;

    /**
     * 车辆颜色
     */
    @Excel(name = "车辆颜色")
    private String carcolor;

    /**
     * 车辆类型编码
     */
    @Excel(name = "车辆类型编码")
    private Integer cartypecode;

    /**
     * 车辆类型
     */
    @Excel(name = "车辆类型")
    private String cartype;

    /**
     * 行驶方向编码
     */
    @Excel(name = "行驶方向编码")
    private Integer cardirectioncode;

    /**
     * 行驶方向
     */
    @Excel(name = "行驶方向")
    private String cardirection;

    /**
     * 图片路径
     */
    @Excel(name = "图片路径")
    private String snappicturepath;

    /**
     * 加载时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadtime;

    /**
     * 分类分级
     */
    @Excel(name = "分类分级")
    private Integer gradelevel;

    private String datauuid;

    private String maindirection;

    private String maindirectionname;

    private String reserve3;


}
