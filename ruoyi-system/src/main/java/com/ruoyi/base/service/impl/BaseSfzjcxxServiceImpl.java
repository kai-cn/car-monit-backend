package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseSfzjcxxMapper;
import com.ruoyi.base.domain.BaseSfzjcxx;
import com.ruoyi.base.service.IBaseSfzjcxxService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站基础信息位置Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseSfzjcxxServiceImpl extends ServiceImpl<BaseSfzjcxxMapper, BaseSfzjcxx> implements IBaseSfzjcxxService {

    @Autowired
    private BaseSfzjcxxMapper baseSfzjcxxMapper;

    /**
     * 查询收费站基础信息位置
     *
     * @param agentPk 收费站基础信息位置ID
     * @return 收费站基础信息位置
     */
    @Override
    public BaseSfzjcxx selectBaseSfzjcxxById(String agentPk) {
        return baseSfzjcxxMapper.selectBaseSfzjcxxById(agentPk);
    }

    /**
     * 查询收费站基础信息位置列表
     *
     * @param baseSfzjcxx 收费站基础信息位置
     * @return 收费站基础信息位置
     */
    @Override
    public List<BaseSfzjcxx> selectBaseSfzjcxxList(BaseSfzjcxx baseSfzjcxx) {
        return baseSfzjcxxMapper.selectBaseSfzjcxxList(baseSfzjcxx);
    }


    /**
     * 新增或者修改收费站基础信息位置
     *
     * @param baseSfzjcxx 收费站基础信息位置
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseSfzjcxx(BaseSfzjcxx baseSfzjcxx)
    {
        if (CommonUtil.isNotBlank(baseSfzjcxx.getId()))
        {
            // 修改
            baseSfzjcxxMapper.updateById(baseSfzjcxx);
        }
        else
        {
            // 新增 主键
            baseSfzjcxxMapper.insert(baseSfzjcxx);
        }
        return AjaxResult.success("操作成功！",baseSfzjcxx.getId());
    }

    /**
     * 批量删除收费站基础信息位置
     *
     * @param agentPks 需要删除的收费站基础信息位置ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseSfzjcxxByIds(String[] agentPks)
    {
        int count = baseSfzjcxxMapper.deleteBaseSfzjcxxByIds(agentPks);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费站基础信息位置信息
     *
     * @param agentPk 收费站基础信息位置ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseSfzjcxxById(String agentPk)
    {
        int count = baseSfzjcxxMapper.deleteBaseSfzjcxxById(agentPk);
        return AjaxResult.success(count);
    }



}
