package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarConfimFree;

import java.math.BigDecimal;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCCarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;

/**
 * 确认补缴Service接口
 *
 * @author ruoyi
 * @date 2025-08-28
 */
public interface ICarConfimFreeService extends IService<CarConfimFree> {
    /**
     * 查询确认补缴
     *
     * @param id 确认补缴ID
     * @return 确认补缴
     */
    CarConfimFree selectCarConfimFreeById(String id);

    /**
     * 查询确认补缴列表
     *
     * @param carConfimFree 确认补缴
     * @return 确认补缴集合
     */
    List<CarConfimFree> selectCarConfimFreeList(CarConfimFree carConfimFree);


    /**
     * 新增或者修改确认补缴
     *
     * @param carConfimFree 确认补缴
     * @return 结果
     */
    AjaxResult saveCarConfimFree(CarConfimFree carConfimFree);

    /**
     * 批量删除确认补缴
     *
     * @param ids 需要删除的确认补缴ID
     * @return 结果
     */
    AjaxResult deleteCarConfimFreeByIds(String[] ids);

    List<CarStatisticsVO> getCarStatistics(IncomeStatisticParam param);

    CarStatisticsVO getCarConfirm(IncomeStatisticParam param);

    String selectOrgId(String carId, String id);

    /**
     * 批量查询车辆补缴记录（orgId 解析）。
     *
     * @param carIds 车辆 ID 集合
     * @return 补缴记录
     */
    List<CarConfimFree> selectOrgIdBatch(List<String> carIds);


    /**
     * 查询确认补缴
     *
     * @param exceptIds
     * @return 确认补缴
     */
    AjaxResult selectCarConfimFreeByExceptIds(String exceptIds);


    /**
     * 查询确认补缴列表
     *
     * @param carConfimFree 确认补缴
     * @return 确认补缴集合
     */
    CarConfimFree listCount(CarConfimFree carConfimFree);

    List<PCCarStatisticsVO> getPCCarStatistics(CarConfimFreeQueryRo queryRo);

    List<CarConfimFree> selectConcernedList(CarConfimFree carConfimFree);
}
