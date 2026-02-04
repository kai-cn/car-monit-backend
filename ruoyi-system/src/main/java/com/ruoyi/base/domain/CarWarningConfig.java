package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;

/**
 * 服务区判定规则对象 car_warning_config
 *
 * @author ruoyi
 * @date 2026-01-27
 */
@Data
@TableName("car_warning_config")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarWarningConfig  implements Custom {

    private static final long serialVersionUID = 1L;

    /**
     * 主键
     */
    @TableId(value = "id", type = IdType.ASSIGN_UUID)
    private String id;


    /** 进入门架编号（分离） */
    @Excel(name = "进入门架编号", readConverterExp = "分=离")
    private String gantryCodeIn;

    /** 进入门架名称 */
    @Excel(name = "进入门架名称")
    private String gantryNameIn;

    /** 出去门架编号（分离） */
    @Excel(name = "出去门架编号", readConverterExp = "分=离")
    private String gantryCodeOut;

    /** 出去门架名称 */
    @Excel(name = "出去门架名称")
    private String gantryNameOut;

    /** 判定时间间隔（分钟） */
    @Excel(name = "判定时间间隔", readConverterExp = "分=钟")
    private Long timeSpan;

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


    /** 桩号 */
    @Excel(name = "备注")
    private String remark;


}
