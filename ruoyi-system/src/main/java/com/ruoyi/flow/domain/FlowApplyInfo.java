package com.ruoyi.flow.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;

/**
 * 我的申请对象 flow_apply_info
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public class FlowApplyInfo extends BaseUuidEntity
{
    /** 单据OID */
    @Excel(name = "单据OID")
    private String billOid;

    /** 业务类型-字典 */
    @Excel(name = "业务类型-字典")
    private String bussType;

    /** 流程实例ID */
    @Excel(name = "流程实例ID")
    private String flowRuid;

    /** 标题 */
    @Excel(name = "标题")
    private String msgTitle;

    /** 内容 */
    @Excel(name = "内容")
    private String msgContext;

    /** 消息类型(1:通知业务，2:办理业务) */
    @Excel(name = "消息类型(1:通知业务，2:办理业务)")
    private String msgType;

    /** 处理的URL */
    @Excel(name = "处理的URL")
    private String msgUrl;

    /** 申请人 */
    @Excel(name = "申请人")
    private String applyName;

    /** 当前节点OID(流程节点OID) */
    @Excel(name = "当前节点OID(流程节点OID)")
    private String currentOid;

    /** 批次OID */
    @Excel(name = "批次OID")
    private String pcOid;

    /** 备用字段1 当前审批人名称 */
    @Excel(name = "备用字段1")
    private String backCol1;

    /** 备用字段2 */
    @Excel(name = "备用字段2")
    private String backCol2;

    /** 备用字段3 */
    @Excel(name = "备用字段3")
    private String backCol3;

    /** 流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝) */
    @Excel(name = "流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)")
    private String flowStatus;

    private String auitEmpName;

    /**
     * 流程委托数据, 里面保存的是json数组
     * @see EntrustInfo
     */
    private String entrustInfo;

    public String getEntrustInfo() {
        return entrustInfo;
    }

    public void setEntrustInfo(String entrustInfo) {
        this.entrustInfo = entrustInfo;
    }

    public String getAuitEmpName() {
        return auitEmpName;
    }

    public void setAuitEmpName(String auitEmpName) {
        this.auitEmpName = auitEmpName;
    }

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

    public String getFlowRuid() {
        return flowRuid;
    }

    public void setFlowRuid(String flowRuid) {
        this.flowRuid = flowRuid;
    }

    public String getMsgTitle() {
        return msgTitle;
    }

    public void setMsgTitle(String msgTitle) {
        this.msgTitle = msgTitle;
    }

    public String getMsgContext() {
        return msgContext;
    }

    public void setMsgContext(String msgContext) {
        this.msgContext = msgContext;
    }

    public String getMsgType() {
        return msgType;
    }

    public void setMsgType(String msgType) {
        this.msgType = msgType;
    }

    public String getMsgUrl() {
        return msgUrl;
    }

    public void setMsgUrl(String msgUrl) {
        this.msgUrl = msgUrl;
    }

    public String getApplyName() {
        return applyName;
    }

    public void setApplyName(String applyName) {
        this.applyName = applyName;
    }

    public String getCurrentOid() {
        return currentOid;
    }

    public void setCurrentOid(String currentOid) {
        this.currentOid = currentOid;
    }

    public String getPcOid() {
        return pcOid;
    }

    public void setPcOid(String pcOid) {
        this.pcOid = pcOid;
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

    public String getFlowStatus() {
        return flowStatus;
    }

    public void setFlowStatus(String flowStatus) {
        this.flowStatus = flowStatus;
    }
}
