package com.ruoyi.manager.domain.vo.bigscreen;

import com.baomidou.mybatisplus.annotation.TableField;
import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/15:45
 * @Description:
 */

@Data
public class IncomeStatisticParam {
    String orgCode;
    String queryDateType;
    String year;
    String month;
    String startDate;
}
