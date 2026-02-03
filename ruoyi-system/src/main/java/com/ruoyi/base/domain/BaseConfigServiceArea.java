package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 服务区对象 base_config_service_area
 *
 * @author ruoyi
 * @date 2026-02-02
 */
@Data
@TableName("base_config_service_area")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseConfigServiceArea extends BasePlusEntity implements Custom {

    /** 判定进入的服务区编码 */
    @Excel(name = "判定进入的服务区编码")
    private String fwqbm;

    /** 判定进入的服务区名称 */
    @Excel(name = "判定进入的服务区名称")
    private String fwqmc;

    /** 经度 */
    @Excel(name = "经度")
    private String lon;

    /** 维度 */
    @Excel(name = "维度")
    private String lat;

    /** 路线编码 */
    @Excel(name = "路线编码")
    private String roadCode;

    /** 路段编码 */
    @Excel(name = "路段编码")
    private String sectionCode;

    /** 桩号 */
    @Excel(name = "桩号")
    private String pileNo;


}
