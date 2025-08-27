package com.ruoyi.manager.service.impl;

import cn.hutool.json.JSONUtil;
import com.ruoyi.common.constant.CacheConstants;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.dto.*;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseInfoVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderAndEnterpriseVo;
import com.ruoyi.manager.domain.vo.bigscreen.center.OrderDetailVo;
import com.ruoyi.manager.service.IBigScreenService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
public class BigScreenServiceImpl implements IBigScreenService {

    @Autowired
    private RedisCache redisCache;

    @Override
    public List<OrderAndEnterpriseInfoVo> orderAndEnterpriseInfo(BigScreenParam bigScreenParam) {
        String cacheKey = bigScreenParam.getType() == 1 ? CacheConstants.ORDER_INFO_POSITION : CacheConstants.ENTERPRISE_INFO_POSITION;
        List<OrderAndEnterpriseInfoVo> orderInfoList = returnCenterStatistics(bigScreenParam, cacheKey, OrderAndEnterpriseInfoVo.class, true);
        if(CollectionUtils.isEmpty(orderInfoList)){
            return Collections.emptyList();
        }
        return orderInfoList.stream()
                .filter(v -> {
                    String[] split = bigScreenParam.getCode().split("-");
                    if(split.length == 3){
                        return v.getAreaCode().equals(Integer.valueOf(split[2]));
                    }
                    return true;
                })
                .filter(k -> {
                    if(bigScreenParam.getOrderType() != null){
                        return bigScreenParam.getOrderType().equals(k.getType());
                    }
                    return true;
                })
                .collect(Collectors.toList());
    }

    @Override
    public List<OrderAndEnterpriseVo> returnOrderAndEnterprise(BigScreenParam bigScreenParam) {
        String cacheKey = bigScreenParam.getType() == 1 ? CacheConstants.ORDER_POSITION : CacheConstants.ENTERPRISE_POSITION;
        List<OrderAndEnterpriseVo> orderInfoList = returnCenterStatistics(bigScreenParam, cacheKey, OrderAndEnterpriseVo.class, false);
        if(CollectionUtils.isEmpty(orderInfoList)){
            return Collections.emptyList();
        }

        Map<Integer, OrderAndEnterpriseVo> resultMap = orderInfoList.stream()
                .collect(Collectors.toMap(
                        OrderAndEnterpriseVo::getAreaCode,
                        vo -> {
                            OrderAndEnterpriseVo newVo = new OrderAndEnterpriseVo();
                            newVo.setName(vo.getName());
                            newVo.setValue(vo.getValue());
                            newVo.setDateTime(vo.getDateTime());
                            newVo.setCoord(vo.getCoord());
                            newVo.setAreaCode(vo.getAreaCode());
                            return newVo;
                        },
                        (vo1, vo2) -> {
                            vo1.setValue(vo1.getValue() + vo2.getValue());
                            return vo1;
                        }
                ));
        return new ArrayList<>(resultMap.values());
    }

    @Override
    public OrderDetailVo returnOrderDetail(BigScreenParam bigScreenParam) {
        String cacheObject = redisCache.getCacheObject(CacheConstants.ORDER_DETAIL + bigScreenParam.getId());
        return JSONUtil.toBean(cacheObject, OrderDetailVo.class);
    }


    /**
     * 通用方式，获取redis中数据数据
     * @param bigScreenParam
     * @param clazz
     * @return
     * @param <T>
     */
    private <T> List<T> returnCenterStatistics(BigScreenParam bigScreenParam, String key, Class<T> clazz, Boolean isDay) {
        // 获取开始时间到结束时间月份集合
        List<String> monthsBetween = DateUtils.getMonthsBetween(bigScreenParam.getStartTime(), bigScreenParam.getEndTime());

        // 从redis中获取数据
        List<Object> multiCacheValue;

        String[] split = bigScreenParam.getCode().split("-");
        // 查询省级下所有数据
        if(split.length == 1){
            multiCacheValue = redisCache.getDataByMonthWithScan(key, monthsBetween, split[0], null, isDay);
        } else if(split.length == 2){
            // 查询市级别以下所有数据
            multiCacheValue = redisCache.getDataByMonthWithScan(key, monthsBetween, split[0], split[1], isDay);
        } else {
            // 查询具体区数据
            multiCacheValue = getMultiMonthHashField(key, monthsBetween, split[0], split[1], split[2], isDay);
        }

        return convertObj(multiCacheValue, clazz);
    }


    /**
     * 转换对象
     * @param multiCacheValue
     * @param clazz
     * @return
     * @param <T>
     */
    private <T> List<T> convertObj(List<Object> multiCacheValue, Class<T> clazz){
        if(CollectionUtils.isEmpty(multiCacheValue)){
            return null;
        }

        List<T> resultList = new ArrayList<>();
        // 从redis获取到的数据 转成对象
        for (Object obj : multiCacheValue) {
            if (obj != null) {
                // 将Object转为String，再转为AmountStatisticsVo
                String jsonStr = obj.toString();
                if(JSONUtil.isJsonArray(jsonStr)){
                    List<T> list = JSONUtil.toList(JSONUtil.parseArray(jsonStr), clazz);
                    resultList.addAll(list);
                } else {
                    T vo = JSONUtil.toBean(jsonStr, clazz);
                    resultList.add(vo);
                }
            }
        }
        return resultList;
    }

    /**
     * 获取hash值
     * @param prefix
     * @param yearMonths
     * @param field
     * @return
     */
    public List<Object> getMultiMonthHashField(String prefix, List<String> yearMonths, String provinceCode, String cityCode, String field, Boolean isDay) {
        List<Object> results = new ArrayList<>();
        if(isDay){
            results = redisCache.getDataByMonthWithScan(prefix, yearMonths, provinceCode, cityCode, isDay);
        } else {
            for (String yearMonth : yearMonths) {
                String key = prefix + yearMonth + ":" + provinceCode + ":" + cityCode;
                Object value = redisCache.getCacheMapValue(key, field);
                if (value != null) {
                    results.add(value);
                }
            }
        }
        return results;
    }



}
