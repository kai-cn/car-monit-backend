package com.ruoyi.base.service;

import java.util.List;

/**
 * @Author: zhukai
 * @Date: 2025/11/20/11:34
 * @Description:
 */
public interface IRoadPathService {

    String getShortestRoadPath(List<String> nodeIds);

}
