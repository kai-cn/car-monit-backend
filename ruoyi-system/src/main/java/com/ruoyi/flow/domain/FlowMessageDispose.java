package com.ruoyi.flow.domain;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;
import lombok.Data;

import java.util.Date;

/**
 * 系统消息处理人对象 flow_message_dispose
 *
 * @author ruoyi
 * @date 2021-05-07
 */

@Data
public class FlowMessageDispose extends BaseUuidEntity {

    /**
     * 消息外键
     */
    @Excel(name = "消息外键")
    private String mid;

    /**
     * 处理对象ID
     */
    @Excel(name = "处理对象ID")
    private String bussId;

    /**
     * 处理对象名称
     * 业务消息-处理人id
     */
    @Excel(name = "处理对象名称")
    private String bussName;

    /**
     * 消息状态（1：已办理，2：未办理）
     */
    @Excel(name = "消息状态", readConverterExp = "1=：已办理，2：未办理")
    private String msgStatus;

    /**
     * 处理时间
     */
    @JsonFormat(pattern = "flow_message_dispose")
    @Excel(name = "处理时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss")
    private Date hangTime;

    /**
     * 其他
     */
    @Excel(name = "其他")
    private String disposeOther;

}
