package com.ruoyi.base.service.impl;

import com.alibaba.fastjson2.JSONArray;
import com.alibaba.fastjson2.JSONObject;
import com.alibaba.fastjson2.TypeReference;
import com.ruoyi.base.domain.Path;
import com.ruoyi.base.domain.PathQueryRo;
import com.ruoyi.base.domain.ResData;
import com.ruoyi.base.service.IRoadPathService;
import com.ruoyi.base.service.forest.RoadPathApi;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;

/**
 * @Description: 
 * @author zhukai
 * @date 2025/11/20 17:38 
 * @Param: 
 * @return: 
 */
@Service
public class RoadPathImpl implements IRoadPathService {

    @Autowired
    private RoadPathApi roadPathApi;

    @Override
    public String getShortestRoadPath(List<String> nodeIds) {
        PathQueryRo ro = new PathQueryRo();
        ro.setNodeIds(nodeIds);
        ro.setPathType("SHORTEST");
        ro.setIncludeCoordinates("TRUE");
        try {
            JSONObject object = roadPathApi.getRoadPath(ro);
            if (object != null) {
                Boolean success = object.getBoolean("success");
                if (success != null && success) {
                    JSONObject data = object.getJSONObject("data");
                    if (data != null) {
                        JSONArray array = data.getJSONArray("data");
                        if (array != null) {
                            JSONArray rtn = new JSONArray();
                            for (Object o : array) {
                                JSONObject obj = (JSONObject) o;
                                ResData resData = obj.to(new TypeReference<ResData>() {
                                });
                                if(resData != null) {
                                    List<Path> pathList = resData.getPathResult().getPath();
                                    for (Path path : pathList) {
                                        double longitude = path.getLongitude();
                                        double latitude = path.getLatitude();
                                        // 保留后6位
                                        double[] gps = new double[2];
                                        gps[0] = longitude;
                                        gps[1] = latitude;
                                        gps[0] = BigDecimal.valueOf(gps[0]).setScale(6, RoundingMode.HALF_UP).doubleValue();
                                        gps[1] = BigDecimal.valueOf(gps[1]).setScale(6, RoundingMode.HALF_UP).doubleValue();
                                        rtn.add(gps);
                                    }
                                }
                            }
                            return rtn.toString();
                        }
                    }
                }
            }
        } catch (Exception e) {
            return null;
        }
        return null;
    }
}
