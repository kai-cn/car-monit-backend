package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarAduitFree;

import java.math.BigDecimal;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCIncomeStaticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
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


    CarStatisticsVO getCarAudit(IncomeStatisticParam param);

    List<incomeStatisticVO> incomeStatistic(IncomeStatisticParam param);

    /**
     * 批量统计车辆补缴次数。
     *
     * @param carIds 车辆 ID 集合
     * @return 按车辆聚合的补缴次数
     */
    List<com.ruoyi.manager.domain.vo.bigscreen.CarIdCountVO> countByCarIds(List<String> carIds);

    Integer selectAuditCount(IncomeStatisticParam param);

    List<PCIncomeStaticsVO> getPCIncomeStatics(CarConfimFreeQueryRo queryRo);

    List<CarConfimFree> incomeDetailList(CarConfimFree carConfimFree);
}
