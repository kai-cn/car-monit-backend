package com.ruoyi.manager.service;

import com.ruoyi.manager.domain.dto.BigScreenParam;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseInfoVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderDetailVo;

import java.util.List;

public interface IBigScreenService {

    /**
     * 订单信息
     * @param bigScreenParam
     * @return
     */
    List<OrderAndEnterpriseInfoVo> orderAndEnterpriseInfo(BigScreenParam bigScreenParam);

    /**
     * 订单聚合数据
     * @param bigScreenParam
     * @return
     */
    List<OrderAndEnterpriseVo> returnOrderAndEnterprise(BigScreenParam bigScreenParam);

    /**
     * 订单详情
     * @param bigScreenParam
     * @return
     */
    OrderDetailVo returnOrderDetail(BigScreenParam bigScreenParam);

}
