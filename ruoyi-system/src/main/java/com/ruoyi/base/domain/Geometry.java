package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.Custom;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.experimental.Accessors;

/**
 * 车辆信息对象 geometry
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@TableName("geometry")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class Geometry implements Custom {

    /** 主键 */
    @TableId(value = "id", type = IdType.INPUT)
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

    /** 桩号 */
    @TableField(exist = false)
    private String zhStr;


    public Geometry(String lxbh, String lxfx, Integer qdzh, Integer zdzh, String paths) {
        this.lxbh = lxbh;
        this.lxfx = lxfx;
        this.qdzh = qdzh;
        this.zdzh = zdzh;
        this.paths = paths;
    }
}
