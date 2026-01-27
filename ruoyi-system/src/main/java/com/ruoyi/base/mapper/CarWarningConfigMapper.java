package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.CarWarningConfig;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 服务区判定规则Mapper接口
 *
 * @author ruoyi
 * @date 2026-01-27
 */
@Repository
public interface CarWarningConfigMapper extends BaseMapper<CarWarningConfig> {
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
     * 批量删除服务区判定规则
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarWarningConfigByIds(String[] ids);

    /**
     * 删除服务区判定规则
     *
     * @param id 服务区判定规则ID
     * @return 结果
     */
    int deleteCarWarningConfigById(String id);

}
