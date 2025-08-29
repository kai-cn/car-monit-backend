package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.domain.vo.bigscreen.CarAuditVO;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 补缴处理Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Repository
public interface CarAduitFreeMapper extends BaseMapper<CarAduitFree> {
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
     * 批量删除补缴处理
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarAduitFreeByIds(String[] ids);

    /**
     * 删除补缴处理
     *
     * @param id 补缴处理ID
     * @return 结果
     */
    int deleteCarAduitFreeById(String id);

    List<CarAuditVO> getCarAudit();
}
