package com.ruoyi.web.util;


/**
 * 内容摘要:公用的错误类
 * 完成日期：2020-12-17
 * 编码作者：
 */
public class ImportErrorEntity implements java.io.Serializable
{

    private static final long serialVersionUID = 7631159408240383420L;

    private int rowNo; // 第几行
    
    private String colName;  // 列名
    
    private String message;  // 错误信息

    public int getRowNo() {
        return rowNo;
    }

    public void setRowNo(int rowNo) {
        this.rowNo = rowNo;
    }

    public String getColName() {
        return colName;
    }

    public void setColName(String colName) {
        this.colName = colName;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
