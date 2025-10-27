package com.ruoyi.base.util;

import com.alibaba.fastjson2.JSONArray;
import com.alibaba.fastjson2.JSONObject;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;
import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.LinkedHashMap;

@Component
public class LonLatPathsUtils {
    private static final String key = "UVUBZ-6AY3V-FEGP2-UJSJP-SBJAJ-UTBT6";
    private static final String secret = "M9yNPgh8FLp33A0plztTK5sehD6gMqny";
    private static final String url = "/ws/direction/v1/driving/";

    @Value("${tx-service-url}")
    private String txServiceUrl;

    @Resource
    private RestTemplate restTemplate;

    /**
     * 计算经纬度路径点
     *
     * @param curLon  当前节点经度
     * @param curLat  当前节点纬度
     * @param nextLon 下个节点经度
     * @param nextLat 下个节点纬度
     * @param heading 初始轨迹方向（0-360，正北为0）
     * @return 第一个元素：需要存储的经纬度集合字符串，第二个元素：距离（单位米）
     */
    public final String calcLonAndLatPaths(String curLon, String curLat, String nextLon, String nextLat, String heading, String waypoints) {
        try {
            //转腾讯坐标系
            double[] cur = GpsUtil.gps84_To_Gcj02(Double.parseDouble(curLat), Double.parseDouble(curLon));
            double[] next = GpsUtil.gps84_To_Gcj02(Double.parseDouble(nextLat), Double.parseDouble(nextLon));

            String from = BigDecimal.valueOf(cur[0]).setScale(6, RoundingMode.HALF_UP).doubleValue() +
                    "," +
                    BigDecimal.valueOf(cur[1]).setScale(6, RoundingMode.HALF_UP).doubleValue();
            String to = BigDecimal.valueOf(next[0]).setScale(6, RoundingMode.HALF_UP).doubleValue() +
                    "," +
                    BigDecimal.valueOf(next[1]).setScale(6, RoundingMode.HALF_UP).doubleValue();

            JSONObject result;
            // 请求腾讯API
            result = getLngLat(from, to, heading, waypoints, key, sig(from, to, heading, waypoints));

            int status = result.getIntValue("status");
            if (status != 0) {
                System.err.println(result.getString("message"));
                return null;
            }

            //获取第一个路线
            JSONObject jsonObject = result.getJSONObject("result").getJSONArray("routes").getJSONObject(0);

            //获取方案总距离
            int distance = jsonObject.getIntValue("distance");

            // 提取数据并格式化
            JSONArray jsonArray = jsonObject.getJSONArray("polyline");
            double[] arr = new double[jsonArray.size()];
            arr[0] = jsonArray.getDoubleValue(0);
            arr[1] = jsonArray.getDoubleValue(1);
            for (int i = 2; i < arr.length; i++) {
                arr[i] = arr[i - 2] + jsonArray.getDouble(i) / 1000000;
            }

            JSONArray rtn = new JSONArray();
            // 转换坐标系
            for (int i = 0; i < arr.length; i += 2) {
                double[] gps = GpsUtil.gcj02_To_Gps84(arr[i], arr[i + 1]);
                // 保留后6位
                gps[0] = BigDecimal.valueOf(gps[0]).setScale(6, BigDecimal.ROUND_HALF_UP).doubleValue();
                gps[1] = BigDecimal.valueOf(gps[1]).setScale(6, BigDecimal.ROUND_HALF_UP).doubleValue();
                rtn.add(gps);
            }
            return rtn.toString();
        } catch (Exception e) {
            return null;
        }
    }

    private JSONObject getLngLat(String from, String to, String heading, String waypoints, String key, String sig) {
        StringBuilder sb = new StringBuilder(txServiceUrl);
        sb.append(url).append("?").append("from=").append(from).append("&to=").append(to);
        if(StringUtils.isNotBlank(heading)) {
            sb.append("&heading=").append(heading);
        }
        if(StringUtils.isNotBlank(waypoints)) {
            sb.append("&waypoints=").append(waypoints);
        }
        sb.append("&key=").append(key).append("&sig=").append(sig);
        return restTemplate.getForObject(sb.toString(), JSONObject.class);
    }

    protected final String urlEncode(String s) {
        try {
            return URLEncoder.encode(s, "utf-8");
        } catch (UnsupportedEncodingException e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * 生成签名
     * @param from
     * @param to
     * @param heading
     * @param waypoints
     * @return
     */
    private String sig(String from, String to, String heading, String waypoints) {
        LinkedHashMap<String, String> param = new LinkedHashMap<>(3);
        param.put("from", from);
        param.put("to", to);
        if(StringUtils.isNotBlank(heading)) {
            param.put("heading", heading);
        }
        if(StringUtils.isNotBlank(waypoints)) {
            param.put("waypoints", waypoints);
        }
        param.put("key", key);

        String[] array = param.keySet().toArray(new String[0]);
        Arrays.sort(array);
        StringBuilder sb = new StringBuilder();
        sb.append(url).append("?");
        for (int i = 0; i < array.length; i++) {
            String str = array[i];
            if (!param.get(array[i]).trim().isEmpty()) {
                sb.append(str).append("=").append(param.get(str).trim());
            }
            if (i < array.length - 1) {
                sb.append("&");
            }
        }
        sb.append(secret);
        try {
            return MD5(sb.toString());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    /**
     * 加密签名
     * @param param
     * @return
     * @throws Exception
     */
    private String MD5(String param) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] array = md.digest(param.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        for (byte item : array) {
            sb.append(Integer.toHexString((item & 0xFF) | 0x100), 1, 3);
        }
        return sb.toString().toLowerCase();
    }
}
