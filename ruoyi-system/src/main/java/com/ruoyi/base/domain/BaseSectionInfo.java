package com.ruoyi.base.domain;

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
 * 路段信息对象 base_section_info
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_section_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseSectionInfo extends BasePlusEntity implements Custom {

    /** 路线编码 */
    @Excel(name = "路线编码")
    private String roadCode;

    /** 路线名称 */
    @Excel(name = "路线名称")
    private String roadName;

    /** 路段编码 */
    @Excel(name = "路段编码")
    private String sectionCode;

    /** 路段名称 */
    @Excel(name = "路段名称")
    private String sectionName;

    /** 起点桩号 */
    @Excel(name = "起点桩号")
    private Long startPileNo;

    /** 终点桩号 */
    @Excel(name = "终点桩号")
    private Long endPileNo;

    /** 机构代码 */
    @Excel(name = "机构代码")
    private String orgCode;

    /** 机构名称 */
    @Excel(name = "机构名称")
    private String orgName;

    /** 层级代码 */
    @Excel(name = "层级代码")
    private String orgLevelCode;

    /** 机构分类 */
    @Excel(name = "机构分类")
    private String orgCategory;

    /** 里程 */
    @Excel(name = "里程")
    private Long mileage;

    /** 通车日期 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "通车日期", width = 30, dateFormat = "yyyy-MM-dd")
    private Date openDate;

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
