package com.ruoyi.manager.domain.vo;

import com.baomidou.mybatisplus.annotation.TableField;
import lombok.Data;

@Data
public class CarConfimFreeQueryRo {

    private String orgId;
    /**
     * 录入单位id
     */
    private String carNo;
    private String orgName;
    /**
     * 逃费类型
     */
    private String escapedType;
    // 时间查询 :入口时间
    @TableField(exist = false)
    private String applyTime1;
    @TableField(exist = false)
    private String applyTime2;

}
