package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/15:45
 * @Description:
 */

@Data
public class IncomeStatisticParam {
    private String orgCode;
    private String queryDateType;//suo查询所，zhan查询站
    private String year;
    private String month;
    private String startDate;
    // 时间查询
    private String applyTime1;
    private String applyTime2;
    private String orgId;
    private String escapedType;


}
