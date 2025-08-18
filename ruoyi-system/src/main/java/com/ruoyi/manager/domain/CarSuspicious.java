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
 * 可疑车辆对象 car_suspicious
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_suspicious")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarSuspicious extends BasePlusEntity implements Custom {

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

    /** 入口站id */
    @Excel(name = "入口站id")
    private String inStationId;

    /** 入口站 */
    @Excel(name = "入口站")
    private String inStation;

    /** 通行时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "通行时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date inTime;

    /** 门架id */
    @Excel(name = "门架id")
    private String gantryStationId;

    /** 门架名称 */
    @Excel(name = "门架名称")
    private String gantrytStation;

    /** 经过时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "经过时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date gantryTime;

    /** 图片(附件ids) */
    @Excel(name = "图片(附件ids)")
    private String fileIds;

    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @Excel(name = "逃费类型", readConverterExp = "字=典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;

    /** 逃费类型名称 */
    @Excel(name = "逃费类型名称")
    private String escapedTypeName;

    /** 是否为可疑车辆 */
    @Excel(name = "是否为可疑车辆")
    private String isExcept;

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
