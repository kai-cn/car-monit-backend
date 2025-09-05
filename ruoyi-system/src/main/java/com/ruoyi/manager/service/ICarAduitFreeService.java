package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarAduitFree;

import java.math.BigDecimal;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.domain.vo.bigscreen.incomeStatisticVO;

/**
 * 补缴处理Service接口
 *
 * @author ruoyi
 * @date 2025-08-28
 */
public interface ICarAduitFreeService extends IService<CarAduitFree> {
    /**
     * 查询补缴处理
     *
     * @param id 补缴处理ID
     * @return 补缴处理
     */
    CarAduitFree selectCarAduitFreeById(String id);

    /**
     * 查询补缴处理列表
     *
     * @param carAduitFree 补缴处理
     * @return 补缴处理集合
     */
    List<CarAduitFree> selectCarAduitFreeList(CarAduitFree carAduitFree);


    /**
     * 新增或者修改补缴处理
     *
     * @param carAduitFree 补缴处理
     * @return 结果
     */
    AjaxResult saveCarAduitFree(CarAduitFree carAduitFree);

    /**
     * 批量删除补缴处理
     *
     * @param ids 需要删除的补缴处理ID
     * @return 结果
     */
    AjaxResult deleteCarAduitFreeByIds(String[] ids);


    /**
     * 批量删除补缴处理
     *
     * @param fkId 补交ID
     * @return 结果
     */
    AjaxResult deleteCarAduitFreeByConfirmId(String fkId);


    BigDecimal getCarAudit();

    List<incomeStatisticVO> incomeStatistic(IncomeStatisticParam param);

    Integer selectAuditCount();


}
