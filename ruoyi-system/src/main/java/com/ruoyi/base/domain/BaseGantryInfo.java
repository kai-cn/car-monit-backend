package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * 门架信息对象 base_gantry_info
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_gantry_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseGantryInfo extends BasePlusEntityNew implements Custom {

    /** 门架编号（分离） */
    @Excel(name = "门架编号", readConverterExp = "分=离")
    private String gantryCode;

    /** 门架名称 */
    @Excel(name = "门架名称")
    private String gantryName;

    /** 所属路线编码 */
    @Excel(name = "所属路线编码")
    private String roadCode;

    /** 所属路段编码 */
    @Excel(name = "所属路段编码")
    private String sectionCode;

    /** 所属收费站编码 */
    @Excel(name = "所属收费站编码")
    private String tollCode;

    /** 所属管理中心机构编码 */
    @Excel(name = "所属管理中心机构编码")
    private String orgCode;

    /** 门架二进制编号 */
    @Excel(name = "门架二进制编号")
    private String hexCode;

    /** 方向（0: 上行，1: 下行） */
    @Excel(name = "方向", readConverterExp = "0=:,上=行，1:,下=行")
    private String direction;

    /** 桩号 */
    @Excel(name = "桩号")
    private String pileNo;

    /** 经度 */
    @Excel(name = "经度")
    private String lon;

    /** 纬度 */
    @Excel(name = "纬度")
    private String lat;

    /** 是否虚门架（0：否，1：是） */
    @Excel(name = "是否虚门架", readConverterExp = "0=：否，1：是")
    private String isVirtual;

    /** 里程 */
    @Excel(name = "里程")
    private String mileage;

    /** 边界门架类型（0：边界入口门架，1：边界出口门架） */
    @Excel(name = "边界门架类型", readConverterExp = "0=：边界入口门架，1：边界出口门架")
    private String boundaryGantryType;

    /** 门架类型（0：收费门架，1：交调门架） */
    @Excel(name = "门架类型", readConverterExp = "0=：收费门架，1：交调门架")
    private String gantryType;

    /** 城市编码 */
    @Excel(name = "城市编码")
    private String cityCode;

    /** 行政区名称 */
    @Excel(name = "行政区名称")
    private String districtName;

    /** 是否属于集团，0：否；1：是 */
    @Excel(name = "是否属于集团，0：否；1：是")
    private String belongGroup;

    /** 门架编号 */
    @Excel(name = "门架编号")
    private String gantryCodeMerge;

    /** 门架别名 */
    @Excel(name = "门架别名")
    private String gantryNameAlias;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 备注 */
    @Excel(name = "备注")
    private String remark2;

    /** 状态（0正常1停用） */
    @Excel(name = "状态", readConverterExp = "0=正常1停用")
    private String status;

    /** 备注 */
    @Excel(name = "备注")
    private String remark;

}
