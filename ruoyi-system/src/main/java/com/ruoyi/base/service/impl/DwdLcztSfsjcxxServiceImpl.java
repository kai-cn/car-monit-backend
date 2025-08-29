package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.DwdLcztSfsjcxxMapper;
import com.ruoyi.base.domain.DwdLcztSfsjcxx;
import com.ruoyi.base.service.IDwdLcztSfsjcxxService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费所基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class DwdLcztSfsjcxxServiceImpl extends ServiceImpl<DwdLcztSfsjcxxMapper, DwdLcztSfsjcxx> implements IDwdLcztSfsjcxxService {

    @Autowired
    private DwdLcztSfsjcxxMapper dwdLcztSfsjcxxMapper;

    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    @Override
    public DwdLcztSfsjcxx selectDwdLcztSfsjcxxById(String agentPk) {
        return dwdLcztSfsjcxxMapper.selectDwdLcztSfsjcxxById(agentPk);
    }

    /**
     * 查询收费所基础信息列表
     *
     * @param dwdLcztSfsjcxx 收费所基础信息
     * @return 收费所基础信息
     */
    @Override
    public List<DwdLcztSfsjcxx> selectDwdLcztSfsjcxxList(DwdLcztSfsjcxx dwdLcztSfsjcxx) {
        return dwdLcztSfsjcxxMapper.selectDwdLcztSfsjcxxList(dwdLcztSfsjcxx);
    }


    /**
     * 新增或者修改收费所基础信息
     *
     * @param dwdLcztSfsjcxx 收费所基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveDwdLcztSfsjcxx(DwdLcztSfsjcxx dwdLcztSfsjcxx)
    {
        if (CommonUtil.isNotBlank(dwdLcztSfsjcxx.getAgentPk()))
        {
            // 修改
            dwdLcztSfsjcxxMapper.updateById(dwdLcztSfsjcxx);
        }
        else
        {
            // 新增 主键
            dwdLcztSfsjcxxMapper.insert(dwdLcztSfsjcxx);
        }
        return AjaxResult.success("操作成功！",dwdLcztSfsjcxx.getAgentPk());
    }

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的收费所基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteDwdLcztSfsjcxxByIds(String[] agentPks)
    {
        int count = dwdLcztSfsjcxxMapper.deleteDwdLcztSfsjcxxByIds(agentPks);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费所基础信息信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteDwdLcztSfsjcxxById(String agentPk)
    {
        int count = dwdLcztSfsjcxxMapper.deleteDwdLcztSfsjcxxById(agentPk);
        return AjaxResult.success(count);
    }



}
