package com.ruoyi.web.util;

import com.ruoyi.common.utils.StringUtils;
import org.springframework.util.ClassUtils;
import org.springframework.web.util.HtmlUtils;

import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class CommonUtil {


	/**
	 * 对面默认为空 -- 空字符串
	 *
	 * @param names
	 * @return
	 */
	public static String isNull(Object names) {
		if (names == null) {
			return "";
		} else {
			return names.toString().trim();
		}
	}


	/**
	 * 对面默认为不为空 -- 空字符串
	 *
	 * @param str
	 * @return
	 */
	public static boolean isNotBlank(String str) {
		return  StringUtils.isNotBlank(str);
	}


	/**
	 * 对面默认为空 -- 空字符串
	 *
	 * @param str
	 * @return
	 */
	public static boolean isBlank(String str) {
		return  StringUtils.isBlank(str);
	}


	/*
	 * 判断是否为整数
	 * @param str 传入的字符串
	 * @return 是整数返回true,否则返回false
	 */
	public static boolean isInteger(String str) {
		Pattern pattern = Pattern.compile("^[-\\+]?[\\d]*$");
		return pattern.matcher(str).matches();
	}


	/*
	 * 判断是否为浮点数，包括double和float
	 * @param str 传入的字符串
	 * @return 是浮点数返回true,否则返回false
	 */
	public static boolean isDouble(String str) {
		Pattern pattern = Pattern.compile("^[-\\+]?[.\\d]*$");
		return pattern.matcher(str).matches();
	}

	//为空就返回一个零
	public static String returnZero(String str){
		if(isNull(str).equals("")){
			return "0";
		}else{
			return str.toString().trim();
		}
	}

	/**
	 * 判断是否是手机端
	 * @param requestHeader
	 * @return
	 */
	public static boolean isMobileDevice(String requestHeader)
	{
		String[] deviceArray = new String[] { "android", "mac os", "windows phone" };
		if (requestHeader == null)
		{
			return false;
		}
		requestHeader = requestHeader.toLowerCase();
		for (int i = 0; i < deviceArray.length; i++)
		{
			if (requestHeader.indexOf(deviceArray[i]) > 0)
			{
				return true;
			}
		}
		return false;
	}


	/**
	 * 判断是否为数字
	 *
	 * @param str
	 * @return
	 */
	public static boolean isNum(String str) {
		Pattern p = null; // 正则表达式
		Matcher m = null; // 操作的字符串
		p = Pattern.compile("^(-?\\d+)(\\.\\d+)?$");
		m = p.matcher(str);
		return m.matches();
	}


	/**
	 * 随机数
	 * @param place 定义随机数的位数
	 */
	public static String randomGen(int place) {
		String base = "qwertyuioplkjhgfdsazxcvbnmQAZWSXEDCRFVTGBYHNUJMIKLOP0123456789";
		StringBuffer sb = new StringBuffer();
		Random rd = new Random();
		for(int i=0;i<place;i++) {
			sb.append(base.charAt(rd.nextInt(base.length())));
		}
		return sb.toString();
	}


	/**
	 * 删除结尾为为,
	 * @param obj
	 * @return
	 */
	public static String deleteEnd(Object obj) {
		String str = isNull(obj);
		if (str.endsWith(",")) {
			str = str.substring(0, str.length() - 1);
		}
		return str;
	}

	// 截取长度
	public static String subStrLentg(Object obj, int len) {
		String str = isNull(obj);
		if (str.length() > len) {
			str = str.substring(0, len - 1);
		}
		return str;
	}


	/**
	 * 获取项目的跟目录 -绝对路径
	 *
	 * @return
	 */
	public static String getProjectUrl()
	{
		return  ClassUtils.getDefaultClassLoader().getResource("").getPath();
	}

	/**
	 * 获取HTML内的文本，不包含标签
	 *
	 * @param html HTML 代码
	 */
	public static String getInnerText(String html) {
		if (StringUtils.isNotBlank(html)) {
			//去掉 html 的标签
			String content = html.replaceAll("</?[^>]+>", "");
			// 将多个空格合并成一个空格
			content = content.replaceAll("(&nbsp;)+", "&nbsp;");
			// 反向转义字符
			content = HtmlUtils.htmlUnescape(content);
			return content.trim();
		}
		return "";
	}

	/**
	 * 对面默认为空 -- 空字符串
	 *
	 * @param names
	 * @return
	 */
	public static int isNullInteger(Integer names) {
		if (names == null) {
			return 0;
		} else {
			return names;
		}
	}

	/**
	 *  验证密码长度
	 *
	 * @param curPassword
	 * @return
	 */
	public static boolean checkPassword(String curPassword) {
		String passwordGz = "^(?![A-Za-z0-9]+$)(?![a-z0-9\\W]+$)(?![A-Za-z\\W]+$)(?![A-Z0-9\\W]+$)[a-zA-Z0-9\\W]{8,20}$";
		if(!curPassword.matches(passwordGz)){
			return true;
		}else{
			return false;
		}
	}


}
