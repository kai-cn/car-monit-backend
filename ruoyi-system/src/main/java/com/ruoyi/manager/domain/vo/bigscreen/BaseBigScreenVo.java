package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

@Data
public class BaseBigScreenVo {

    /**
     * 时间 年月  yyyyMM
     */
    private String dateTime;

    /**
     * 地域 code (区县 code)
     *
     */
    private Integer code;

    /**
     * 地域 code (城市 code)
     */
    private Integer cityCode;

    /**
     * 地域 code (省 code)
     */
    private Integer provinceCode;
}
