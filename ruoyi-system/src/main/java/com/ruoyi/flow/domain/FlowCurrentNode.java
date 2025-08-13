package com.ruoyi.flow.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;

/**
 * 流程_当前节点对象 flow_current_node
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public class FlowCurrentNode extends BaseUuidEntity
{
    /** 流程OID */
    @Excel(name = "流程OID")
    private String flowOid;

    /** 当前节点OID(流程节点OID) 流程模板(flow_template)oid */
    @Excel(name = "当前节点OID(流程节点OID)")
    private String currentOid;

    /** 节点顺序 */
    @Excel(name = "节点顺序")
    private Integer nodeOrder;

    /** 节点KEY */
    @Excel(name = "节点KEY")
    private String nodeKey;

    /** 节点名称 */
    @Excel(name = "节点名称")
    private String nodeName;

    /** 当前流程类型(字典：1人员2角色3其他) */
    @Excel(name = "当前流程类型(字典：1人员2角色3其他)")
    private String configType;

    /** 节点配置id */
    @Excel(name = "节点配置id")
    private String configId;

    /** 节点配置名称 */
    @Excel(name = "节点配置名称")
    private String configName;

    /** 单据OID */
    @Excel(name = "单据OID")
    private String billOid;

    /** 处理人ID */
    @Excel(name = "处理人ID")
    private String auitEmpOid;

    /** 处理人名称 */
    @Excel(name = "处理人名称")
    private String auitEmpName;

    /** 备用字段1 项目id */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2  委托之前的审核人id */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 备用字段3 委托之前的审核人名称 */
    @Excel(name = "备用字段3")
    private String backCol3;

    /**
     * 角色id
     */
    private String roleId;

    /**
     * 表名称
     */
    private String tableName;

    /**
     * 项目id
     */
    private String projectId;

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


    /** 审核结论（T同意F拒绝R退回S提交） 委托 entrust */
    private String shValue;

    /** 内容 */
    private String shContext;

    /**
     * 委托人id
     */
    private String entrustUserId;

    /**
     * 委托人名称
     */
    private String entrustUserName;


    /**
     * 角色key
      */
    private String roleKey;

    /**
     * 部门ID
     */
    private Long deptId;


    public String getRoleKey() {
        return roleKey;
    }

    public void setRoleKey(String roleKey) {
        this.roleKey = roleKey;
    }

    public Long getDeptId() {
        return deptId;
    }

    public void setDeptId(Long deptId) {
        this.deptId = deptId;
    }

    public String getEntrustUserId() {
        return entrustUserId;
    }

    public void setEntrustUserId(String entrustUserId) {
        this.entrustUserId = entrustUserId;
    }

    public String getEntrustUserName() {
        return entrustUserName;
    }

    public void setEntrustUserName(String entrustUserName) {
        this.entrustUserName = entrustUserName;
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

    public String getFlowOid() {
        return flowOid;
    }

    public void setFlowOid(String flowOid) {
        this.flowOid = flowOid;
    }

    public String getCurrentOid() {
        return currentOid;
    }

    public void setCurrentOid(String currentOid) {
        this.currentOid = currentOid;
    }

    public Integer getNodeOrder() {
        return nodeOrder;
    }

    public void setNodeOrder(Integer nodeOrder) {
        this.nodeOrder = nodeOrder;
    }

    public String getNodeKey() {
        return nodeKey;
    }

    public void setNodeKey(String nodeKey) {
        this.nodeKey = nodeKey;
    }

    public String getNodeName() {
        return nodeName;
    }

    public void setNodeName(String nodeName) {
        this.nodeName = nodeName;
    }

    public String getConfigType() {
        return configType;
    }

    public void setConfigType(String configType) {
        this.configType = configType;
    }

    public String getConfigId() {
        return configId;
    }

    public void setConfigId(String configId) {
        this.configId = configId;
    }

    public String getConfigName() {
        return configName;
    }

    public void setConfigName(String configName) {
        this.configName = configName;
    }

    public String getBillOid() {
        return billOid;
    }

    public void setBillOid(String billOid) {
        this.billOid = billOid;
    }

    public String getAuitEmpOid() {
        return auitEmpOid;
    }

    public void setAuitEmpOid(String auitEmpOid) {
        this.auitEmpOid = auitEmpOid;
    }

    public String getAuitEmpName() {
        return auitEmpName;
    }

    public void setAuitEmpName(String auitEmpName) {
        this.auitEmpName = auitEmpName;
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

    public String getRoleId() {
        return roleId;
    }

    public void setRoleId(String roleId) {
        this.roleId = roleId;
    }

    public String getTableName() {
        return tableName;
    }

    public void setTableName(String tableName) {
        this.tableName = tableName;
    }

    public String getProjectId() {
        return projectId;
    }

    public void setProjectId(String projectId) {
        this.projectId = projectId;
    }

    public String getFlowKey() {
        return flowKey;
    }

    public void setFlowKey(String flowKey) {
        this.flowKey = flowKey;
    }

    public String getFlowRuid() {
        return flowRuid;
    }

    public void setFlowRuid(String flowRuid) {
        this.flowRuid = flowRuid;
    }

    public String getFlowApplyOid() {
        return flowApplyOid;
    }

    public void setFlowApplyOid(String flowApplyOid) {
        this.flowApplyOid = flowApplyOid;
    }

    public String getFlowStatus() {
        return flowStatus;
    }

    public void setFlowStatus(String flowStatus) {
        this.flowStatus = flowStatus;
    }
}
