package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.mapper.CarWarningRuleMapper;
import com.ruoyi.manager.domain.CarWarningRule;
import com.ruoyi.manager.service.ICarWarningRuleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

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
        List<CarWarningRule> ruleList = this.selectCarWarningRuleList(new CarWarningRule());
        Map<String, Map<String, Set<String>>> map = new HashMap<>();
        if(ruleList != null && !ruleList.isEmpty()) {
            for (CarWarningRule rule : ruleList) {
                if(StringUtils.isNoneBlank(rule.getNoticeUserId(), rule.getNoticeUserId(), rule.getNoticeType())) {
                    String[] userIds = rule.getNoticeUserId().split(",");
                    String[] noticeRange = rule.getNoticeRangeId().split(",");
                    String noticeType = rule.getNoticeType().trim();
                    Set<String> notices = Arrays.stream(noticeRange)
                            .filter(s -> !s.isEmpty())
                            .map(String::trim)
                            .collect(Collectors.toSet());
                    for (String rawUserId : userIds) {
                        String userId = rawUserId.trim();
                        if (!userId.isEmpty()) {
                            // 获取或创建用户的map
                            Map<String, Set<String>> noticeMap = map.computeIfAbsent(userId, k -> new HashMap<>());
                            // 获取或创建该类型的通知set
                            Set<String> userNotices = noticeMap.computeIfAbsent(noticeType, k -> new HashSet<>());
                            userNotices.addAll(notices);
                        }
                    }
                }
            }
        }
        if(!map.isEmpty()) {
            for (Map.Entry<String, Map<String, Set<String>>> entry : map.entrySet()) {
                String userId = entry.getKey();
                redisCache.setCacheMap(Constants.CAR_WARNING_RULE + userId, entry.getValue());
            }
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
