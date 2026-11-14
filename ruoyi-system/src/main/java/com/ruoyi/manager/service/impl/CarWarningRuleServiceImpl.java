package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.CarWarningRule;
import com.ruoyi.manager.mapper.CarWarningRuleMapper;
import com.ruoyi.manager.service.ICarWarningRuleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

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

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询预警规则
     *
     * @param id 预警规则ID
     * @return 预警规则
     */
    @Override
    public CarWarningRule selectCarWarningRuleById(String id) {
        CarWarningRule carWarningRule = carWarningRuleMapper.selectCarWarningRuleById(id);
        return carWarningRule;
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
        cacheWarningRule();
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
        cacheWarningRule();
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
        cacheWarningRule();
        return AjaxResult.success(count);
    }


    private void cacheWarningRule() {
        //先删除
        Collection<String> keys = redisCache.keys(Constants.CAR_WARNING_RULE + "*");
        if(keys != null && !keys.isEmpty()) {
            for (String key : keys) {
                redisCache.deleteObject(key);
            }
        }
        List<CarWarningRule> ruleList = this.selectCarWarningRuleList(new CarWarningRule());
        if(ruleList != null && !ruleList.isEmpty()) {
            for (CarWarningRule rule : ruleList) {
                if(StringUtils.isNoneBlank(rule.getNoticeUserId(), rule.getNoticeRangeId(), rule.getNoticeType())) {
                    String noticeType = CommonUtil.isNull(rule.getNoticeType()); // 预警方式
                    String[] userIds = CommonUtil.deleteEnd(rule.getNoticeUserId()).split(","); // 通知人员
                    String[] noticeRangeIds = CommonUtil.deleteEnd(rule.getNoticeRangeId()).split(","); // 预警范围id
                    for (String rawUserId : userIds) {
                        String userId = CommonUtil.isNull(rawUserId);
                        if (CommonUtil.isNotBlank(userId) && noticeRangeIds.length > 0) {
                            List<String> ruleListValue = new ArrayList<>();
                            // 如果
                            String redisKey = Constants.CAR_WARNING_RULE + userId + "type" + noticeType;
                            Object oldObject = redisCache.getCacheObject(redisKey);
                            if (null != oldObject) {
                                ruleListValue = (List) oldObject;
                            }
                            for (String noticeRangeId : noticeRangeIds) {
                                ruleListValue.add(CommonUtil.isNull(noticeRangeId));
                            }
                            redisCache.setCacheObject(redisKey, ruleListValue);
                        }
                    }
                }
            }
        }
    }


}
