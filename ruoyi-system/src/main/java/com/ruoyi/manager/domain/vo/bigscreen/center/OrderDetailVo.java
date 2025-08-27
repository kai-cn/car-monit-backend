package com.ruoyi.manager.domain.vo.bigscreen.center;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.ruoyi.manager.domain.TWaybill;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

@Data
public class OrderDetailVo {

    /**
     * id
     */
    private String id;
    /**
     * 订单名称
     */
    private String goodsName;

    /**
     * 订单编号
     */
    private String orderNum;

    /**
     * 发货人
     */
    private String deliverUser; // 发货人

    /**
     * 下单时间 YYYY-MM-dd
     */
    @JsonFormat(pattern = "yyyy-MM-dd",  timezone = "GMT+8")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private Date createTime;

    /**
     * 货物规格
     */
    private String goodsSpec;;

    /**
     * 单位 1-(件) 2-吨 3-箱
     */
    private Integer deliverType;

    /**
     * 数量
     */
    private BigDecimal nums;

    /**
     * 发货地址
     */
    private String deliveryAddress;

    /**
     * 收货地址
     */
    private String shippingAddress;

    /**
     * 运输单
     */
    private List<TransitOrderDetailVo> transitOrder;

    private List<TWaybill> waybillList;
}
