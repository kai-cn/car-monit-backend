package com.ruoyi.manager.domain.vo.bigscreen.center;

import lombok.Data;

@Data
public class OrderAndEnterpriseInfoVo {

    /**
     *  时间  年月日 20250801
     */
    private String time;

    private String id;

    private String name;

    private String numberCode;

    private String[] coord;

    private Integer areaCode;

    /**
     * 0 流入 1流出
     */
    private Integer type;
}
