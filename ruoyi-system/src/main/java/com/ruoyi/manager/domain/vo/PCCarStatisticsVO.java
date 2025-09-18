package com.ruoyi.manager.domain.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/14:29
 * @Description:
 */
@Data
public class PCCarStatisticsVO {

    /**
     * 录入单位
     */
    private String orgName;

    /**
     * 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
     */
    private Integer escapedType10Num = 0;

    private BigDecimal escapedType10Amount = BigDecimal.ZERO;

    private Integer escapedType20Num = 0;

    private BigDecimal escapedType20Amount = BigDecimal.ZERO;

    private Integer escapedType30Num = 0;

    private BigDecimal escapedType30Amount = BigDecimal.ZERO;

    private Integer escapedType40Num = 0;

    private BigDecimal escapedType40Amount = BigDecimal.ZERO;

    private Integer escapedType50Num = 0;

    private BigDecimal escapedType50Amount = BigDecimal.ZERO;

    private Integer totalNum = 0;

    private BigDecimal totalAmount = BigDecimal.ZERO;

    private List<PCCarStatisticsDetailVO> detailVOList;
}
