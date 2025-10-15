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
 * 车辆位置对象 zdata_location_dict
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Data
@TableName("zdata_location_dict")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class ZdataLocationDict  implements Custom {

    /** 主键 */
    private Long id;

    /** 类型 */
    @Excel(name = "类型")
    private String type;

    /** 收费站 */
    @Excel(name = "收费站")
    private String name;

    /** 轨迹表和实时轨迹code */
    @Excel(name = "轨迹表和实时轨迹code")
    private String rawCode;

    /** 收费站/门架code */
    @Excel(name = "收费站/门架code")
    private String standardCode;

    /** 路线编码 */
    @Excel(name = "路线编码")
    private String roadcode;

    /** 路线名称 */
    @Excel(name = "路线名称")
    private String roadname;

    /** 路段编码 */
    @Excel(name = "路段编码")
    private String sectioncode;

    /** 路段名称 */
    @Excel(name = "路段名称")
    private String sectionname;

    /** 收费站编码 */
    @Excel(name = "收费站编码")
    private String tollcode;

    /** 收费站名称 */
    @Excel(name = "收费站名称")
    private String tollname;

    /** 组织机构编码 */
    @Excel(name = "组织机构编码")
    private String orgcode;

    /** 组织机构名称 */
    @Excel(name = "组织机构名称")
    private String orgname;

    /** 创建时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "创建时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date createdAt;

    /** 修改时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "修改时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date updatedAt;


}
