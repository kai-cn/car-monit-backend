package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarWarningRule;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 预警规则Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarWarningRuleMapper extends BaseMapper<CarWarningRule> {
    /**
     * 查询预警规则
     *
     * @param id 预警规则ID
     * @return 预警规则
     */
    CarWarningRule selectCarWarningRuleById(String id);

    /**
     * 查询预警规则列表
     *
     * @param carWarningRule 预警规则
     * @return 预警规则集合
     */
    List<CarWarningRule> selectCarWarningRuleList(CarWarningRule carWarningRule);

    /**
     * 批量删除预警规则
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarWarningRuleByIds(String[] ids);

    /**
     * 删除预警规则
     *
     * @param id 预警规则ID
     * @return 结果
     */
    int deleteCarWarningRuleById(String id);

}
