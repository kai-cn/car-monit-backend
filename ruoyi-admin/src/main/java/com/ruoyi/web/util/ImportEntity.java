package com.ruoyi.web.util;


/**
 * 内容摘要:导出公用BO 
 * 完成日期：2020-12-17
 * 编码作者：
 */
public class ImportEntity implements java.io.Serializable
{
	public ImportEntity() {

	}

	public ImportEntity(String colName,String colProp,String valadRes) {
		this.colName = colName;
		this.colProp = colProp;
		this.valadRes = valadRes;
	}

    private static final long serialVersionUID = 3286015940978442733L;

    private String colName; // 表头

    private String colProp; // 列

	/**
	 * 校验规则 1 必填  2 数字  3 整数   4 日期   5 身份证 6 年月
	 * 7 => 数值类型(包含整数 小数)
	 */
    private String valadRes;

	public String getColName() {
		return colName;
	}

	public void setColName(String colName) {
		this.colName = colName;
	}

	public String getColProp() {
		return colProp;
	}

	public void setColProp(String colProp) {
		this.colProp = colProp;
	}

	public String getValadRes() {
		return valadRes;
	}

	public void setValadRes(String valadRes) {
		this.valadRes = valadRes;
	}
}
