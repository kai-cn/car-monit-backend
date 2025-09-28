package com.ruoyi.manager.domain.vo;

import com.baomidou.mybatisplus.annotation.TableField;
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

    // 当前页面
    private Integer pageNum;

    // 分页大小
    private Integer pageSize;



}
