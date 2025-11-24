package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/10:01
 * @Description:
 */

@Data
public class PathQueryRo {
    private List<String> nodeIds;
    private String pathType;
    private String includeCoordinates;
    private String queryMode;
    /*private int limit;
    private int page;
    private int pageSize;*/
}
