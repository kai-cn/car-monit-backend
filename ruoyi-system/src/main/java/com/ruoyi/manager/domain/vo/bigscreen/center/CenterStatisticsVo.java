package com.ruoyi.manager.domain.vo.bigscreen.center;

import com.ruoyi.manager.domain.vo.bigscreen.BaseBigScreenVo;
import lombok.Data;

@Data
public class CenterStatisticsVo extends BaseBigScreenVo {

    /**
     * 入住企业已发单数
     */
    private Integer enterpriseReceiptNum;

    /**
     * 平台已接单数
     */
    private Integer platformReceiptNum;

    /**
     * 平台完成数
     */
    private Integer platformCompleteNum;

    /**
     * 订单未完成数
     */
    private Integer unfinishedOrderNum;
}
