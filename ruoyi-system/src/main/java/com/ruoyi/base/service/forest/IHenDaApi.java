package com.ruoyi.base.service.forest;

import com.alibaba.fastjson2.JSONObject;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Headers;
import com.dtflys.forest.annotation.Query;

/**
 * 恒达接口
 * @author Qiuchen
 * 2021年9月30日
 */
public interface IHenDaApi {

	// TODO 缺少恒达访问地址
	/**
	 * "&appid=" + appid + "&nonce=" + nonce + "&signature=" + signature + "&timestamp=" + timestamp;
	 * 桩号转经纬度
	 * @param params 参数
	 * @param appid 参数
	 * @param nonce 参数
	 * @param signature 参数
	 * @param timestamp 参数
	 * @return JSONObject
	 */
	@Headers({ "Connection:close"})
	@Get(url = "${hendaUrl}/getLonLatByPos", connectTimeout = 30000)
	public JSONObject getLonLatByPos(@Query("params") String params, @Query("appid") String appid, @Query("nonce") String nonce,
								@Query("signature") String signature, @Query("timestamp") String timestamp);
}
