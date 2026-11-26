package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

@Data
public class CarParaVO {

    /**
     * 车俩列表
     */
    private List<CarVO> carlist;

    //车牌号
    private String carNo;

    // 时间查询
    private String applyTime1;

    private String applyTime2;

    /**
     * 车俩编号数组
     */
    private List<String> carNoList;

    // 当前页面
    private Integer pageNum;

    // 分页大小
    private Integer pageSize;



    // 起始界面
    private Integer startNum;

    // 最后的界面
    private Integer endNum;


    // 起始天数
    private Integer starTime;

    // 最后的天数
    private Integer endTime;


    // 标识位
    private String flag;



}
