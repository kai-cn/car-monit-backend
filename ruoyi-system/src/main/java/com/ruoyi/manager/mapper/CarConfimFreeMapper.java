package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

/**
 * 确认补缴Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Repository
public interface CarConfimFreeMapper extends BaseMapper<CarConfimFree> {
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
     * 批量删除确认补缴
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarConfimFreeByIds(String[] ids);

    /**
     * 删除确认补缴
     *
     * @param id 确认补缴ID
     * @return 结果
     */
    int deleteCarConfimFreeById(String id);

    List<CarStatisticsVO> getCarStatistics(IncomeStatisticParam param);

    CarStatisticsVO getCarConfirm(IncomeStatisticParam param);

    String selectOrgId(@Param("carId") String carId, @Param("id") String id);

    /**
     * 批量查询车辆对应的补缴记录（用于消除 exceptRecordList 的逐行查询）。
     *
     * @param carIds 车辆 ID 集合
     * @return 补缴记录（仅填充 carId/id/orgId/exceptIds）
     */
    List<CarConfimFree> selectOrgIdBatch(@Param("carIds") List<String> carIds);

    List<CarConfimFree> selectCarConfimFreeByExceptIds(List<String> exceptIds);


    /**
     * 查询确认补缴
     *
     * @param carConfimFree
     * @return 确认补缴
     */
    CarConfimFree listCount(CarConfimFree carConfimFree);

    List<CarConfimFree> getPCCarStatistics(CarConfimFreeQueryRo queryRo);

    List<CarConfimFree> selectConcernedList(CarConfimFree carConfimFree);
}
