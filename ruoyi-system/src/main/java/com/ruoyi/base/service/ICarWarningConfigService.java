package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.CarWarningConfig;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 服务区判定规则Service接口
 *
 * @author ruoyi
 * @date 2026-01-27
 */
public interface ICarWarningConfigService extends IService<CarWarningConfig> {
    /**
     * 查询服务区判定规则
     *
     * @param id 服务区判定规则ID
     * @return 服务区判定规则
     */
    CarWarningConfig selectCarWarningConfigById(String id);

    /**
     * 查询服务区判定规则列表
     *
     * @param carWarningConfig 服务区判定规则
     * @return 服务区判定规则集合
     */
    List<CarWarningConfig> selectCarWarningConfigList(CarWarningConfig carWarningConfig);


    /**
     * 新增或者修改服务区判定规则
     *
     * @param carWarningConfig 服务区判定规则
     * @return 结果
     */
    AjaxResult saveCarWarningConfig(CarWarningConfig carWarningConfig);

    /**
     * 批量删除服务区判定规则
     *
     * @param ids 需要删除的服务区判定规则ID
     * @return 结果
     */
    AjaxResult deleteCarWarningConfigByIds(String[] ids);

    /**
     * 从缓存拿到配置项
     */
    List<CarWarningConfig> getRedisCarWarningConfig();

}
