package com.ruoyi.web.util;


import com.alibaba.fastjson2.JSONObject;

import java.util.HashMap;
import java.util.List;
import java.util.Map;


/**
 * 内容摘要:导出公用
 * 完成日期：2020-12-17
 * 编码作者：
 */
public class ImportUtil {

	// 2小数或整数
	public static final String xiaoshu = "^(-?\\d+)(\\.\\d+)?$";

	//  3 整数
	public static final String znumber = "^[0-9]*$";

	// 4 日期
	public static final String eLtime2 = "[0-9]{4}-[0-9]{2}-[0-9]{2}";

	// 5 身份证
	public static final String idCard = "^[1-9]\\d{5}[1-9]\\d{3}((0\\d)|(1[0-2]))(([0|1|2]\\d)|3[0-1])\\d{3}([0-9]|X|x)$";

	//  6 年月
	public static final String elTimeYM = "^\\d{4}(\\-|\\/|\\.)\\d{1,2}$";


	//  8 年月
	public static final String dateTimeRegex= "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$";

	/**
	 * 校验是否是数值类型的正则表达式
	 * 7 => 数值类型
	 */
	public static final String VERIFY_NUMBER_TYPE = "^(\\-|\\+)?\\d+(\\.\\d+)?$";

	public static Object importExcel(
			List<ImportErrorEntity> errorList,
			List<ImportEntity> boList,
			int index,
			String[] exceVals,
			Class<? extends Object> cl) {
		ImportSysUtil importUtil = new ImportSysUtil();
		Map<String, String> objMap = new HashMap<String, String>();
		for (int i = 0; i < boList.size(); i++) {
			String value = isNull(exceVals[i]);
			ImportEntity bo = boList.get(i);
			objMap.put(bo.getColProp(), value);   // 拼装map
			if (!CommonUtil.isNull(bo.getValadRes()).equals("")) {
				String[] gzs = bo.getValadRes().split(",");
				for (int z = 0; z < gzs.length; z++) {
					if (gzs[z].equals("1")) {
						// 必填
						if (value.equals("")) {
							errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "不能为空"));
						}
					}
					if (!value.equals("")) {
						if (gzs[z].equals("2")) {
							if (!importUtil.validateValueRegex(value, xiaoshu)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "不是小数"));
							}
						} else if (gzs[z].equals("3")) {
							if (!importUtil.validateValueRegex(value, znumber)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "不是正整数"));
							}
						} else if (gzs[z].equals("4")) {
							if (!importUtil.validateValueRegex(value, eLtime2)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "日期格式（年-月-日）不正确"));
							}
						} else if (gzs[z].equals("5")) {
							if (!importUtil.validateValueRegex(value, idCard)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "身份证号码不正确"));
							}
						} else if (gzs[z].equals("6")) {
							if (!importUtil.validateValueRegex(value, elTimeYM)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "日期格式（年-月）不正确"));
							}
						} else if ("7".equals(gzs[z])) {
							if (!importUtil.validateValueRegex(value, VERIFY_NUMBER_TYPE)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "不是数值"));
							}
						}else if (gzs[z].equals("8")) {
							if (!importUtil.validateValueRegex(value, dateTimeRegex)) {
								errorList.add(importUtil.getErrorBO(index + 1, bo.getColName(), "日期格式（年月日时分秒）不正确"));
							}
						}
					}
				}
			}
		}

		Object rtnobj = null;
		if (errorList.size() == 0) {
			JSONObject jsonObject = new JSONObject(objMap);
			rtnobj = jsonObject.toJavaObject(cl);
			/*JSONObject jsonObject = (JSONObject) JSONObject(objMap);
			rtnobj = JSONObject.toJavaObject(jsonObject, cl);*/
		}
		return rtnobj;
	}


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


}
