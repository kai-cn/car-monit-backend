package com.ruoyi.flow.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;
import lombok.Data;

import java.util.List;

/**
 * 系统内部消息对象 flow_message_info
 *
 * @author ruoyi
 * @date 2021-05-07
 */
@Data
public class FlowMessageInfo extends BaseUuidEntity {

    /**
     * 消息编号
     *  格式 => 时间戳+userId
     */
    private String messageNo;

    /**
     * 单据OID
     */
    @Excel(name = "单据OID")
    private String billOid;

    /**
     * 业务类型-字典
     */
    @Excel(name = "业务类型-字典")
    private String bussType;

    /**
     * 流程实例ID
     */
    @Excel(name = "流程实例ID")
    private String flowRuid;

    /**
     * 标题
     */
    @Excel(name = "标题")
    private String msgTitle;

    /**
     * 内容
     */
    @Excel(name = "内容")
    private String msgContext;

    /**
     * 消息类型(1:通知业务，2:办理业务)
     */
    @Excel(name = "消息类型(1:通知业务，2:办理业务)")
    private String msgType;

    /**
     * 处理的URL
     */
    @Excel(name = "处理的URL")
    private String msgUrl;

    /**
     * 批次OID
     */
    @Excel(name = "批次OID")
    private String pcOid;

    /**
     * 申请人
     */
    @Excel(name = "申请人")
    private String applyName;

    /**
     * 备用字段1
     */
    @Excel(name = "备用字段1")
    private String backCol1;

    /**
     * 备用字段2
     */
    @Excel(name = "备用字段2")
    private String backCol2;

    /**
     * 备用字段3
     */
    @Excel(name = "备用字段3")
    private String backCol3;

    /**
     * 处理对象ID
     */
    private Long userId;

    /**
     * 消息状态
     */
    private String msgStatus;

    /**
     * 当前状态
     */
    private String flowStatus;

    /**
     * 当前处理人
     */
    private String curEmpNames;

    /** 消息 */
    private List<FlowMessageDispose> disposeList;

}
