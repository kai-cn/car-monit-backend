package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("t_waybill_cargo")
public class TWaybillCargo {
    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private String id;

    /** 货物名称 */
    private String cargoName;

    /** 货物规格 */
    private String cargoSpec;

    /** 重量数值 */
    private BigDecimal weight;

    /** 重量单位 1-件 2-吨 3-箱 */
    private Integer weightUnit;

    /** 运单表 id */
    private String waybillId;
}
