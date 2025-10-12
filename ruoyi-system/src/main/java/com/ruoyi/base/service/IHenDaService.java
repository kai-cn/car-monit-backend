package com.ruoyi.base.service;

import com.alibaba.fastjson2.JSONObject;

/**
 * IHenDaApi Description
 *
 * @author Alec
 * @date 2025-10-12 13:11
 */
public interface IHenDaService {

    /**
     * 桩号转经纬度
     * @param roadCode 道路编号
     * @param pile 桩号
     * @param direction 方向 UP("1", "上行"), DOWN("2", "下行")
     * @return JSONObject
     */
    public JSONObject getPileToLonLat(String roadCode, String pile, String direction);
}
