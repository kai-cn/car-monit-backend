package com.ruoyi.flow.domain;

import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;

/**
 * 审核历史记录对象 flow_list
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public class FlowList extends BaseUuidEntity
{
    /** 单据OID */
    @Excel(name = "单据OID")
    private String billOid;

    /** 流程类型 */
    @Excel(name = "流程类型")
    private String bussType;

    /** 任务ID */
    @Excel(name = "任务ID")
    private String taskId;

    /** 流程实例ID */
    @Excel(name = "流程实例ID")
    private String flowRuid;

    /** 当前节点OID(流程节点OID) */
    @Excel(name = "当前节点OID(流程节点OID)")
    private String currentOid;

    /** 审核人 */
    @Excel(name = "审核人")
    private String shUser;

    /** 审核结论KEY（T同意F拒绝R退回S提交） */
    @Excel(name = "审核结论KEY", readConverterExp = "T=同意F拒绝R退回S提交")
    private String shKey;

    /** 审核结论（T同意F拒绝R退回S提交） */
    @Excel(name = "审核结论", readConverterExp = "T=同意F拒绝R退回S提交")
    private String shValue;

    /** 内容 */
    @Excel(name = "内容")
    private String shContext;

    /** 备用字段1 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 备用字段3 */
    @Excel(name = "备用字段3")
    private String backCol3;

    public String getBillOid() {
        return billOid;
    }

    public void setBillOid(String billOid) {
        this.billOid = billOid;
    }

    public String getBussType() {
        return bussType;
    }

    public void setBussType(String bussType) {
        this.bussType = bussType;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getFlowRuid() {
        return flowRuid;
    }

    public void setFlowRuid(String flowRuid) {
        this.flowRuid = flowRuid;
    }

    public String getCurrentOid() {
        return currentOid;
    }

    public void setCurrentOid(String currentOid) {
        this.currentOid = currentOid;
    }

    public String getShUser() {
        return shUser;
    }

    public void setShUser(String shUser) {
        this.shUser = shUser;
    }

    public String getShKey() {
        return shKey;
    }

    public void setShKey(String shKey) {
        this.shKey = shKey;
    }

    public String getShValue() {
        return shValue;
    }

    public void setShValue(String shValue) {
        this.shValue = shValue;
    }

    public String getShContext() {
        return shContext;
    }

    public void setShContext(String shContext) {
        this.shContext = shContext;
    }

    public String getBackCol1() {
        return backCol1;
    }

    public void setBackCol1(String backCol1) {
        this.backCol1 = backCol1;
    }

    public String getBackCol2() {
        return backCol2;
    }

    public void setBackCol2(String backCol2) {
        this.backCol2 = backCol2;
    }

    public String getBackCol3() {
        return backCol3;
    }

    public void setBackCol3(String backCol3) {
        this.backCol3 = backCol3;
    }
}
