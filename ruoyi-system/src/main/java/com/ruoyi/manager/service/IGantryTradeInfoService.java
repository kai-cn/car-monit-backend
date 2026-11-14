package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.GantryTradeInfo;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 门架交易查询Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface IGantryTradeInfoService extends IService<GantryTradeInfo> {
    /**
     * 查询门架交易查询
     *
     * @param id 门架交易查询ID
     * @return 门架交易查询
     */
    GantryTradeInfo selectGantryTradeInfoById(String id);

    /**
     * 查询门架交易查询列表
     *
     * @param gantryTradeInfo 门架交易查询
     * @return 门架交易查询集合
     */
    List<GantryTradeInfo> selectGantryTradeInfoList(GantryTradeInfo gantryTradeInfo);


    /**
     * 新增或者修改门架交易查询
     *
     * @param gantryTradeInfo 门架交易查询
     * @return 结果
     */
    AjaxResult saveGantryTradeInfo(GantryTradeInfo gantryTradeInfo);

    /**
     * 批量删除门架交易查询
     *
     * @param ids 需要删除的门架交易查询ID
     * @return 结果
     */
    AjaxResult deleteGantryTradeInfoByIds(String[] ids);

}
