package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarWarningRule;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 预警规则Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarWarningRuleService extends IService<CarWarningRule> {
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
     * 新增或者修改预警规则
     *
     * @param carWarningRule 预警规则
     * @return 结果
     */
    AjaxResult saveCarWarningRule(CarWarningRule carWarningRule);

    /**
     * 批量删除预警规则
     *
     * @param ids 需要删除的预警规则ID
     * @return 结果
     */
    AjaxResult deleteCarWarningRuleByIds(String[] ids);

}
