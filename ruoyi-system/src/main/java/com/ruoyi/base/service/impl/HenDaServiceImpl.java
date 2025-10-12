package com.ruoyi.base.service.impl;

import com.alibaba.fastjson2.JSONObject;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruoyi.base.service.IHenDaService;
import com.ruoyi.base.service.forest.IHenDaApi;
import com.ruoyi.base.util.EncryptUtils;
import org.springframework.beans.factory.annotation.Value;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Map;

/**
 * HenDaServiceImpl Description
 *
 * @author Alec
 * @date 2025-10-12 13:12
 */
public class HenDaServiceImpl implements IHenDaService {

    private IHenDaApi henDaApi;

    /*
     * TODO 缺少恒达appid 、secretKey
     */
    @Value("${henda.appid}")
    private String appid;

    @Value("${henda.secretKey}")
    private String secretKey;

    @Override
    public JSONObject getPileToLonLat(String roadCode, String pile, String direction) {
        Map<String, String> map = new HashMap<>(3);
        map.put("layerName", "rdlinelong");
        map.put("filter", "lxbh='" + roadCode + "'  and gxfx = '" + direction + "'");
        map.put("m", pile);

        Calendar calendar = Calendar.getInstance();
        SimpleDateFormat format = new SimpleDateFormat("yyyyMMddHHmmss");
        String timestamp = format.format(new java.util.Date());

        //随机字符串
        String nonce = String.valueOf(calendar.getTimeInMillis());

        String signature = EncryptUtils.getCiphertext(appid, secretKey, nonce, timestamp);
        ObjectMapper mapper = new ObjectMapper();
        String mapStr = "";
        try {
            mapStr = URLEncoder.encode(mapper.writeValueAsString(map), "utf8");
        } catch (UnsupportedEncodingException | JsonProcessingException e) {
            throw new RuntimeException(e);
        }
        JSONObject lonLatByPos = henDaApi.getLonLatByPos(mapStr, appid, nonce, signature, timestamp);
        JSONObject jsonObject = lonLatByPos.getJSONObject("data");

        JSONObject rtn = new JSONObject();
        rtn.put("longitude", jsonObject.getString("x"));
        rtn.put("latitude", jsonObject.getString("y"));
        return rtn;
    }
}
