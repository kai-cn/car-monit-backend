package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/11:03
 * @Description:
 */

@Data
public class SegmentRoutes {
    private String startNodeId;
    private String endNodeId;
    private String startTitle;
    private String endTitle;
    private List<List<Double>> routePoints;
}
