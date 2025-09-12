package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 车俩白名单对象 car_white_info
 *
 * @author ruoyi
 * @date 2025-09-12
 */
@Data
@TableName("car_white_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarWhiteInfo extends BasePlusEntity implements Custom {

    /** 车牌颜色（字典：1白色2黑色） */
    @Excel(name = "车牌颜色", readConverterExp = "字=典：1白色2黑色")
    private String plateColor;

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

    /** 相关附件(附件ids) */
    @Excel(name = "相关附件(附件ids)")
    private String fileIds;

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
