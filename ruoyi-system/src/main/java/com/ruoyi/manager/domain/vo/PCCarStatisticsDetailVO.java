package com.ruoyi.manager.domain.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.math.BigDecimal;
import java.sql.Timestamp;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/14:29
 * @Description:
 */
@Data
public class  PCCarStatisticsDetailVO {

    private String plateColor;

    /** 车牌号 */
    private String carNo;

    /** 车型 */
    private String carType;

    /**
     * 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
     */
    private String escapedType;

    /**
     * 车辆数量
     */
//    private Integer number = 0;

    /**
     * 逃费金额
     */
    private BigDecimal escapedAmount = BigDecimal.ZERO;

    /** 录入单位 */
    private String orgName;

    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp createTime;
}
