package com.ruoyi.manager.domain.vo.bigscreen.center;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OrderAndEnterpriseVo {

    /**
     * 年月  202508
     */
    private String dateTime;

    /**
     * 城市代码
     */
    private Integer cityCode;

    /**
     * 省份代码
     */
    private Integer provinceCode;

    private String name;

    private String[] coord;

    private Integer value;

    /**
     * 地区代码
     */
    private Integer areaCode;
}
