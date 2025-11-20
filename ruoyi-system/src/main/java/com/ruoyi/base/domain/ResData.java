package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/11:36
 * @Description:
 */
@Data
public class ResData {
    private PathResult pathResult;
    private List<SegmentRoutes> segmentRoutes;
    private int pathIndex;
    private int nodeCount;
    private int totalPointCount;
    private double totalMileage;
}
