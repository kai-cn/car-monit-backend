package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * 省界设备ip对象 ods_szdn_gantry_ip
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Data
@TableName("ods_szdn_gantry_ip")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class OdsSzdnGantryIp implements Custom {

    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.ASSIGN_UUID)
    private Long id;

    /**
     * 门架编号
     */
    @Excel(name = "门架编号")
    private String gantryCode;

    /**
     * 门架名称
     */
    @Excel(name = "门架名称")
    private String gantryName;

    /**
     * 机构编码
     */
    @Excel(name = "机构编码")
    private String orgCode;

    /**
     * 设备ip
     */
    @Excel(name = "设备ip")
    private String ip;

    private String brand;

    /**
     * 类型1是省界门架
     */
    @Excel(name = "类型1是省界门架")
    private String type;


}
