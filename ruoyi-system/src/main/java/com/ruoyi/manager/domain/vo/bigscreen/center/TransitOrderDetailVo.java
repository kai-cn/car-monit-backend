package com.ruoyi.manager.domain.vo.bigscreen.center;

import com.ruoyi.manager.domain.TWaybillRoute;
//import com.ruoyi.manager.domain.dto.order.AddressDto;
import lombok.Data;

import java.util.List;

@Data
public class TransitOrderDetailVo {

    /**
     * 运单序号
     */
    private Integer orderNo;

    /** 订单类型 */
    private Integer orderType;

    /** 承运公司 */
    private String carrierCompanyId;

    /** 承运公司名称 */
    private String carrierCompany;

    /**
     * 起运点
     */
//    private AddressDto startPosInfo;

    /**
     * 目的地
     */
//    private AddressDto endPosInfo;

    /**
     * 经纬度
     */
    private List<TrackPoint> trackPointList;

    private List<TWaybillRoute> vehicles;


}
