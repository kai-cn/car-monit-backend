package com.ruoyi.manager.domain.vo.bigscreen.center;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class TrackPoint {

    private BigDecimal latitude;  // 纬度
    private BigDecimal longitude; // 经度
}
