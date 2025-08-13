package com.ruoyi.manager.domain;

import java.math.BigDecimal;
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
 * 业务测试对象 buss_test
 *
 * @author ruoyi
 * @date 2024-09-06
 */
@Data
@TableName("buss_test")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class BussTest extends BasePlusEntity implements Custom {

    /** 业务名称 */
    @Excel(name = "业务名称")
    private String billName;

    /** 业务名称(字典：1业务2其他) */
    @Excel(name = "业务名称(字典：1业务2其他)")
    private String billType;

    /** 金额 */
    @Excel(name = "金额")
    private BigDecimal amount;

    /** 部门id */
    @Excel(name = "部门id")
    private Long deptId;

    /** 人员id */
    @Excel(name = "人员id")
    private Long userId;

    /** 申请时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "申请时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date applyTime;

    /** 时间时分秒 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "时间时分秒", width = 30, dateFormat = "yyyy-MM-dd")
    private Date applyTime2;

    /** 附件(逗号多个分割) */
    @Excel(name = "附件(逗号多个分割)")
    private String fileIds;

    /** 流程key */
    @Excel(name = "流程key")
    private String flowKey;

    /** 流程实例ID */
    @Excel(name = "流程实例ID")
    private String flowRuid;

    /** 流程申请ID */
    @Excel(name = "流程申请ID")
    private String flowApplyOid;

    /** 流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝) */
    @Excel(name = "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)")
    private String flowStatus;

    /** 审核时间 */
    @JsonFormat(pattern = "yyyy-MM-dd")
    @Excel(name = "审核时间", width = 30, dateFormat = "yyyy-MM-dd")
    private Date shTime;

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
