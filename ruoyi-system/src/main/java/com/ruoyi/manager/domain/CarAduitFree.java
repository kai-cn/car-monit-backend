package com.ruoyi.manager.domain;

import java.math.BigDecimal;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 补缴处理对象 car_aduit_free
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Data
@TableName("car_aduit_free")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarAduitFree extends BasePlusEntity implements Custom {

    /** 确认补缴id */
    @Excel(name = "确认补缴id")
    private String confirmId;

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

    /** 处理单位id */
    @Excel(name = "处理单位id")
    private String orgId;

    /** 处理单位 */
    @Excel(name = "处理单位")
    private String orgName;

    /** 录入人员ids */
    @Excel(name = "处理人员ids")
    private String userIds;

    /** 处理人员 */
    @Excel(name = "处理人员")
    private String userNames;

    /** 拆分金额 */
    @Excel(name = "拆分金额")
    private BigDecimal amount;

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
