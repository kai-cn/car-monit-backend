package com.ruoyi.system.domain.vo;

import lombok.Data;

import java.util.Date;

/**
 *  描述:向第三方电子签章系统传参使用
 *
**/
@Data
public class SealParmras {

    /**用户的数字签名**/
    private String usercert = null;

    /**文档唯一编号**/
    private String documentNo = null;

    /**印章图片，Base64编码格式**/
    private String pictureByBase64 = null;

    /**签章策略ID**/
    private String sealStrategyId = null;

    /**Base64编码后的PDF文件数据**/
    private String pdfByBase64 = null;

    /**
     签章位置说明，支持后台配置规则定位、位置定位和关键字两种方式，只能选择一种，如果选择则对应的配置需要必填
     auto:基于后台配置的位置规则
     position：基于位置盖章
     keyword：基于关键字盖章
     **/
    private String type = null;

    /**PDF中印章显示大小的宽度**/
    private int sealPDFWidth = 150;

    /**PDF中印章显示大小的高度**/
    private int sealPDFHeight = 150;

    /**是否骑缝盖章 是:true  否:false **/
    private boolean perforation = false;

    /**是否多页签章。（图章在pdf每一页的同一位置）是:true 否:false **/
    private boolean perpagevisible = false;

    /**关键字位置文字**/
    private String key = null;

    /**盖章处的页码**/
    private int pageNum = 1;

    private Date time = null;

    private int positionX = 0;

    private int positionY = 0;



}
