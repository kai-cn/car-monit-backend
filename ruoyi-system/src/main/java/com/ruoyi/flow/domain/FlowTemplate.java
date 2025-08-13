package com.ruoyi.flow.domain;

import lombok.Data;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;

/**
 * 流程节点对象 flow_template
 *
 * @author ruoyi
 * @date 2021-05-07
 */

@Data
public class FlowTemplate extends BaseUuidEntity {
    /**
     * 流程OID
     */
    @Excel(name = "流程OID")
    private String flowOid;

    /**
     * 当前流程类型(字典：1正常流程2会签流程)
     */
    @Excel(name = "当前流程类型(字典：1正常流程2会签流程)")
    private String flowType;

    /**
     * 节点顺序
     */
    @Excel(name = "节点顺序")
    private Integer nodeOrder;

    /**
     * 节点KEY
     */
    @Excel(name = "节点KEY")
    private String nodeKey;

    /**
     * 节点名称
     */
    @Excel(name = "节点名称")
    private String nodeName;

    /**
     * 下一节点OID(-1为当前为最后一个节点)
     */
    @Excel(name = "下一节点OID(-1为当前为最后一个节点)")
    private String nextNodeOid;

    /**
     * 上一节点OID(0为开始节点)
     */
    @Excel(name = "上一节点OID(0为开始节点)")
    private String previousNodeOid;

    /**
     * 驳回到第几步 0 是发起人
     */
    @Excel(name = "驳回到第几步 0 是发起人")
    private Integer returnNum;

    /**
     * 驳回节点OID
     */
    @Excel(name = "驳回节点OID")
    private String returnNodeOid;

    /**
     * 节点配置条件
     */
    @Excel(name = "节点配置条件")
    private String configCondtion;

    /**
     * 当前流程类型(字典：1人员2角色3其他)
     */
    @Excel(name = "当前流程类型(字典：1人员2角色3其他)")
    private String configType;

    /**
     * 节点配置id
     */
    @Excel(name = "节点配置id")
    private String configId;

    /**
     * 节点配置名称
     */
    @Excel(name = "节点配置名称")
    private String configName;

}
