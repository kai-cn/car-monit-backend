package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/10:35
 * @Description:
 */
@Data
public class TopTenVO {

    /**
     * 路线
     */
    private String roadCode;

    /**
     * 路段名称
     */
    private String sectionName;

    /**
     * 车辆数量
     */
    private Integer carNum;

    /**
     * 排名
     */
    private Integer rank;

    /**
     * 百分比
     */
    private String rate;
}
