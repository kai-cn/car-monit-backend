package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseSfzjcxx;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费站基础信息位置Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseSfzjcxxService extends IService<BaseSfzjcxx> {
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
     * 新增或者修改收费站基础信息位置
     *
     * @param baseSfzjcxx 收费站基础信息位置
     * @return 结果
     */
    AjaxResult saveBaseSfzjcxx(BaseSfzjcxx baseSfzjcxx);

    /**
     * 批量删除收费站基础信息位置
     *
     * @param agentPks 需要删除的收费站基础信息位置ID
     * @return 结果
     */
    AjaxResult deleteBaseSfzjcxxByIds(String[] agentPks);

}
