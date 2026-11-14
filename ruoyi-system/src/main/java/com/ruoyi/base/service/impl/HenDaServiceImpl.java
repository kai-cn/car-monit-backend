package com.ruoyi.base.service.impl;

import com.alibaba.fastjson2.JSONObject;
import tools.jackson.databind.ObjectMapper;
import com.ruoyi.base.service.IHenDaService;
import com.ruoyi.base.service.forest.IHenDaApi;
import com.ruoyi.base.util.EncryptUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

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
@Service
public class HenDaServiceImpl implements IHenDaService {

    @Autowired
    private IHenDaApi henDaApi;

    @Value("${hengda.appid}")
    private String appid;

    @Value("${hengda.secret}")
    private String secretKey;

    @Override
    public JSONObject getPileToLonLat(String roadCode, String pile, String direction) {
        try {
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
            String mapStr = URLEncoder.encode(mapper.writeValueAsString(map), "utf8");

            JSONObject lonLatByPos = henDaApi.getLonLatByPos(mapStr, appid, nonce, signature, timestamp);
            JSONObject jsonObject = lonLatByPos.getJSONObject("data");

            JSONObject rtn = new JSONObject();
            rtn.put("longitude", jsonObject.getString("x"));
            rtn.put("latitude", jsonObject.getString("y"));
            return rtn;
        }catch (Exception e){
            // 防止线程中断 如果报错就跳过这个经纬度
            return null;
        }
    }
}
