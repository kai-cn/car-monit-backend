package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/11:41
 * @Description:
 */

@Data
public class PathResult {
    private List<Path> path;
    private double totalMileage;
}
