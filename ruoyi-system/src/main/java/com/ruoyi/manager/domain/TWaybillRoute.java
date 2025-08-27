package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
//import com.ruoyi.manager.domain.model.PositionModel;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

@Data
@EqualsAndHashCode(callSuper = false)
@TableName("t_waybill_route")
public class TWaybillRoute {
    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private String id;

    /**
     * 运单表 id
     */
    private String waybillId;

    /**
     * 车牌号或船只 MMSI
     */
    private String vehicleNo;

    /**
     * 装载重量
     */
    private BigDecimal loadWeight;

    /**
     * 运输趟数
     */
    private Integer tripNum;

    /**
     * 航次号
     */
    private String voyageNo;

    /**
     * 预计出发时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date etdTime;

    /**
     * 预计结束时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date etaTime;

    @JsonProperty(value = "transportStatus")
    private int carStatus;

//    /**
//     * 轨迹信息
//     */
//    @TableField(exist = false)
//    private List<PositionModel> tracks;

    private boolean isCar;
}
