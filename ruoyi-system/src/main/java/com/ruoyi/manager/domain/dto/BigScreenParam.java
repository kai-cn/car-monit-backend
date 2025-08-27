package com.ruoyi.manager.domain.dto;

import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import javax.validation.constraints.NotNull;
import java.util.Date;

@Data
public class BigScreenParam {

    /**
     * 开始时间
     */
    @NotNull(message = "开始时间不能为空")
    @DateTimeFormat(pattern = "yyyy-MM")
    private Date startTime;

    /**
     * 结束时间
     */
    @NotNull(message = "结束时间不能为空")
    @DateTimeFormat(pattern = "yyyy-MM")
    private Date endTime;

    /**
     * 地域code
     */
    private String code;

    /**
     * 0 流入 1流出
     */
    private Integer orderType;

    /**
     * type 1 订单  2 企业
     */
    private Integer type;

    /**
     * 编号
     */
    private String orderNum;

    private String id;
}
