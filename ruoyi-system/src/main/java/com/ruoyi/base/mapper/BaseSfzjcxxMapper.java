package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseSfzjcxx;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站基础信息位置Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseSfzjcxxMapper extends BaseMapper<BaseSfzjcxx> {
    /**
     * 查询收费站基础信息位置
     *
     * @param agentPk 收费站基础信息位置ID
     * @return 收费站基础信息位置
     */
    BaseSfzjcxx selectBaseSfzjcxxById(String agentPk);

    /**
     * 查询收费站基础信息位置列表
     *
     * @param baseSfzjcxx 收费站基础信息位置
     * @return 收费站基础信息位置集合
     */
    List<BaseSfzjcxx> selectBaseSfzjcxxList(BaseSfzjcxx baseSfzjcxx);

    /**
     * 批量删除收费站基础信息位置
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseSfzjcxxByIds(String[] agentPks);

    /**
     * 删除收费站基础信息位置
     *
     * @param agentPk 收费站基础信息位置ID
     * @return 结果
     */
    int deleteBaseSfzjcxxById(String agentPk);

}
