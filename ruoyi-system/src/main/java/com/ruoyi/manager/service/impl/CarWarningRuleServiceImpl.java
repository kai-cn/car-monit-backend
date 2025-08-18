package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarWarningRuleMapper;
import com.ruoyi.manager.domain.CarWarningRule;
import com.ruoyi.manager.service.ICarWarningRuleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 预警规则Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarWarningRuleServiceImpl extends ServiceImpl<CarWarningRuleMapper, CarWarningRule> implements ICarWarningRuleService {

    @Autowired
    private CarWarningRuleMapper carWarningRuleMapper;

    /**
     * 查询预警规则
     *
     * @param id 预警规则ID
     * @return 预警规则
     */
    @Override
    public CarWarningRule selectCarWarningRuleById(String id) {
        return carWarningRuleMapper.selectCarWarningRuleById(id);
    }

    /**
     * 查询预警规则列表
     *
     * @param carWarningRule 预警规则
     * @return 预警规则
     */
    @Override
    public List<CarWarningRule> selectCarWarningRuleList(CarWarningRule carWarningRule) {
        return carWarningRuleMapper.selectCarWarningRuleList(carWarningRule);
    }


    /**
     * 新增或者修改预警规则
     *
     * @param carWarningRule 预警规则
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarWarningRule(CarWarningRule carWarningRule)
    {
        if (CommonUtil.isNotBlank(carWarningRule.getId()))
        {
            // 修改
            carWarningRuleMapper.updateById(carWarningRule);
        }
        else
        {
            // 新增 主键
            carWarningRuleMapper.insert(carWarningRule);
        }
        return AjaxResult.success("操作成功！",carWarningRule.getId());
    }

    /**
     * 批量删除预警规则
     *
     * @param ids 需要删除的预警规则ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarWarningRuleByIds(String[] ids)
    {
        int count = carWarningRuleMapper.deleteCarWarningRuleByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除预警规则信息
     *
     * @param id 预警规则ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarWarningRuleById(String id)
    {
        int count = carWarningRuleMapper.deleteCarWarningRuleById(id);
        return AjaxResult.success(count);
    }



}
