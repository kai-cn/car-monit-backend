package com.ruoyi.base.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntityNew;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

import java.util.Date;

/**
 * 机构信息对象 base_org_info
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Data
@TableName("base_org_info")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BaseOrgInfo extends BasePlusEntityNew implements Custom {

    /** 主键 */
    private String bigId;

    /** 机构代码 */
    @Excel(name = "机构代码")
    private String orgCode;

    /** 机构名称 */
    @Excel(name = "机构名称")
    private String orgName;

    /** 机构简称 */
    @Excel(name = "机构简称")
    private String orgShortName;

    /** 上级机构ID */
    @Excel(name = "上级机构ID")
    private String orgParentId;

    /** 层级代码 */
    @Excel(name = "层级代码")
    private String orgLevelCode;

    /** 是否虚机构 1：虚机构，0：非需机构 */
    @Excel(name = "是否虚机构 1：虚机构，0：非需机构")
    private String orgIsVirtual;

    /** 是否是养护类（1：是，0否） */
    @Excel(name = "是否是养护类", readConverterExp = "1=：是，0否")
    private String orgMaintenance;

    /** 机构顺序 */
    @Excel(name = "机构顺序")
    private Long orgSequence;

    /** 是否管理单位，主要指是否是路段管理单位(1：是,0：否) */
    @Excel(name = "是否管理单位，主要指是否是路段管理单位(1：是,0：否)")
    private String orgIsManager;

    /** 是否删除 1：是 0：否 */
    @Excel(name = "是否删除 1：是 0：否")
    private String orgIsDeleted;

    /** 机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "机构分类： 01集团 02公司 03管理中心 10部门 11所 12服务区 13养护区 14站 15项目办 16信息中心 17项目部  99其它", width = 30, dateFormat = "yyyy-MM-dd")
    private Date orgCategory;

    /** 是否授权机构 1：是 0：否 */
    @Excel(name = "是否授权机构 1：是 0：否")
    private String orgIsAuthorized;

    /** 机构地址 */
    @Excel(name = "机构地址")
    private String orgAddress;

    /** 是自营养护单位 */
    @Excel(name = "是自营养护单位")
    private String orgIsYhAutarky;

    /** 加载时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "加载时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date loadTime;

    /** 分类分级 */
    @Excel(name = "分类分级")
    private Integer gradeLevel;

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
