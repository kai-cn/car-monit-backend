package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 车辆信息对象 geometry
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@Data
@TableName("geometry")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class Geometry implements Custom {

    /** 主键 */
    private Integer id;

    /** 路线编号 */
    @Excel(name = "路线编号")
    private String lxbh;

    /** 路线方向 1上行 2下行*/
    @Excel(name = "路线方向")
    private String lxfx;

    /** 起点桩号 */
    @Excel(name = "起点桩号")
    private Integer qdzh;

    /** 终点桩号 */
    @Excel(name = "终点桩号")
    private Integer zdzh;

    /** 经纬度 */
    @Excel(name = "经纬度")
    private String paths;


}
