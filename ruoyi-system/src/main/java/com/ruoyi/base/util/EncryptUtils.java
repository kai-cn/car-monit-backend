package com.ruoyi.base.util;

import org.apache.commons.lang3.RandomStringUtils;
import org.apache.commons.lang3.time.DateFormatUtils;
import org.springframework.util.DigestUtils;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.Collectors;

/**
 * @author ma
 */
public class EncryptUtils {

	/**
	 * 	构建加密验证密文 只实现《20200531-江西省高速集团养护管理系统建设（一期）项目集成规范（征求意见稿）》中7.2.2
	 * POST（application/json）的加密方式 因为跟规范制定方交流过，对方建议我们都使用POST
	 */
	private static String createSignature(Map<String, String> headerMap, String secretKey, String jsonStr) {
		/*
		 * （1）将appID、timeStamp、nonce、secretKey按字典排序后并用&拼接，得到字符串publicStr；
		 * （2）去除json字符串进行压缩（即去掉换行，空格信息）得到字符串jsonStr；
		 * （3）将第一步得到的字符串和第二步得到的字符串用&拼接；
		 * （4）对最终的字符串使用md5加密算法。
		 *
		 * 	appID String 是 应用对应唯一编码
		 *  signature String 是 签名，生成方式见附录二
		 *  nonce String 是 签名唯一随机串。用于防止网络重放攻击，建议每一次请求都使用不同的随机字符串（生成方式见附录二）
		 *  timestamp String 是
		 *  请求的时间戳。按照ISO8601标准表示，并需要使用UTC时间，格式为yyyyMMddHHmmss。示例：20180101200000 表示北京时间
		 */
		List<String> list = Arrays.asList(headerMap.get("appid").replace("[", "").replace("]", ""),
				headerMap.get("timestamp").replace("[", "").replace("]", ""),
				headerMap.get("nonce").replace("[", "").replace("]", ""), secretKey);
		Collections.sort(list);
		StringBuilder publicStr = new StringBuilder();
		for (String str : list) {
			if (publicStr.toString().isEmpty()) {
				publicStr.append(str);
			} else {
				publicStr.append(publicStr).append("&").append(str);
			}
		}
		// 删除String中的换行和空格
		jsonStr = jsonStr.replace("\n", "");
		jsonStr = jsonStr.replace(" ", "");
		String strAdd = publicStr + "&" + jsonStr;
        return DigestUtils.md5DigestAsHex(strAdd.getBytes(StandardCharsets.UTF_8));
	}

	/**
	 * hik加密
	 * @param headerMap head
	 * @param secretKey secretKey
	 * @param jsonStr json
	 * @return str
	 */
	public static String createSignatures(Map<String, String> headerMap, String secretKey, String jsonStr) {
		List<String> list = Arrays.asList(headerMap.get("appID").replace("[", "").replace("]", ""),
				headerMap.get("timestamp").replace("[", "").replace("]", ""),
				headerMap.get("nonce").replace("[", "").replace("]", ""), secretKey);

		String publicStr = list.stream().sorted(String::compareTo).collect(Collectors.joining("&"));
		// 删除String中的换行和空格
		jsonStr = jsonStr.replace("\n", "").replace(" ", "");
		String strAdd = publicStr + "&" + jsonStr;
		return DigestUtils.md5DigestAsHex(strAdd.getBytes(StandardCharsets.UTF_8));
	}
	
	public static String getCiphertext(String appid, String secretKey, String nonce, String timestamp) {
		Map<String, String> headers = new HashMap<>(3);
	    headers.put("appid", appid);
	    headers.put("nonce", nonce);
	    headers.put("timestamp", timestamp);
	    return EncryptUtils.createSignature(headers, secretKey, nonce);
	}

	public static TreeMap<String, String> getSignHeader() {
		TreeMap<String, String> header = new TreeMap<>();
		header.put("appID", "APL");
		header.put("nonce", RandomStringUtils.randomAlphabetic(12));
		header.put("timestamp", DateFormatUtils.format(new Date(), "yyyyMMddHHmmss"));
		header.put("secretKey", "45d6a321-fcba-4d38-9595-c04ffe90a6c6");
		return header;
	}
}
