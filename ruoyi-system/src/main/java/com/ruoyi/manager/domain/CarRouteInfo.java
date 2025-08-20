package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 常用路线对象 car_route_info
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Data
@TableName("car_route_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarRouteInfo extends BasePlusEntity implements Custom {

    /** 车辆id */
    @Excel(name = "车辆id")
    private String carId;

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

    /** 起点通行地址 */
    @Excel(name = "起点通行地址")
    private String startAddress;

    /** 最后通行经度 */
    @Excel(name = "最后通行经度")
    private String startLongitude;

    /** 起点通行维度 */
    @Excel(name = "起点通行维度")
    private String startLatitude;

    /** 终点通行地址 */
    @Excel(name = "终点通行地址")
    private String endAddress;

    /** 终点通行经度 */
    @Excel(name = "终点通行经度")
    private String endLongitude;

    /** 终点通行维度 */
    @Excel(name = "终点通行维度")
    private String endLatitude;

    /** 路线明细JOSN */
    @Excel(name = "路线明细JOSN")
    private String routeDetail;

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

}
