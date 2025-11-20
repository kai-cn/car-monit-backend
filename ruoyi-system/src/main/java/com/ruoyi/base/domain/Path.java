package com.ruoyi.base.domain;

import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/10:59
 * @Description:
 */

@Data
public class Path {
    private String nodeId;
    private String label;
    private String title;
    private double longitude;
    private double latitude;
    private double afterMileage;
    private double frontMileage;
    private double mileage;
    private String orgName;
    private String section;
    private int direction;
}
