package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("t_waybill")
public class TWaybill {
    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private String id;

    /** 运单编号 E-yyyymmdd+6位流水 */
    private String waybillNo;

    /** 运单类型 1-陆运单 2-水运单 */
    private Integer waybillType;

    /** 发货人姓名 */
    private String shipperName;

    /** 发货人联系方式 */
    private String shipperPhone;

    /** 备注 */
    private String remark;

    /** 订单id */
    private String orderId;

    /** 运输状态 1- 待运输 2- 开始运输 3-结束运输 */
    private String transportStatus;

    /** 预计到货日期 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date eta;

    /** 预计发货日期 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date etd;

    /** 货代公司名称 */
    @TableField("forwarder_name")
    private String forwarderName;

    @TableField("forwarder_id")
    /** 货代公司id */
    private String forwarderId;

    /** 承运公司名称 */
    private String carrierName;

    /** 承运公司id */
    @TableField("carrier_id")
    private String carrierId;

    /** 运单关联的载具信息 */
    @TableField(exist = false)
    private List<TWaybillRoute> vehicles;

    /** 运单的地址信息 */
//    @TableField(exist = false)
//    private List<TWaybillAddress> addresses;

    /** 运单的货物信息 */
    @TableField(exist = false)
    private List<TWaybillCargo> cargos;
    /** 订单的排序 */
    private int sort;

    private int status;
    /** 价格 */
    private BigDecimal price;
    /** 报价类型 1：一口价 2 ：单价*/
    private int priceType;
}
