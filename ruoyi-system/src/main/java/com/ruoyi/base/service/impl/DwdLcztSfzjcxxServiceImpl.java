package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.DwdLcztSfzjcxxMapper;
import com.ruoyi.base.domain.DwdLcztSfzjcxx;
import com.ruoyi.base.service.IDwdLcztSfzjcxxService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class DwdLcztSfzjcxxServiceImpl extends ServiceImpl<DwdLcztSfzjcxxMapper, DwdLcztSfzjcxx> implements IDwdLcztSfzjcxxService {

    @Autowired
    private DwdLcztSfzjcxxMapper dwdLcztSfzjcxxMapper;

    /**
     * 查询收费站基础信息
     *
     * @param agentPk 收费站基础信息ID
     * @return 收费站基础信息
     */
    @Override
    public DwdLcztSfzjcxx selectDwdLcztSfzjcxxById(String agentPk) {
        return dwdLcztSfzjcxxMapper.selectDwdLcztSfzjcxxById(agentPk);
    }

    /**
     * 查询收费站基础信息列表
     *
     * @param dwdLcztSfzjcxx 收费站基础信息
     * @return 收费站基础信息
     */
    @Override
    public List<DwdLcztSfzjcxx> selectDwdLcztSfzjcxxList(DwdLcztSfzjcxx dwdLcztSfzjcxx) {
        return dwdLcztSfzjcxxMapper.selectDwdLcztSfzjcxxList(dwdLcztSfzjcxx);
    }


    /**
     * 新增或者修改收费站基础信息
     *
     * @param dwdLcztSfzjcxx 收费站基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveDwdLcztSfzjcxx(DwdLcztSfzjcxx dwdLcztSfzjcxx)
    {
        if (CommonUtil.isNotBlank(dwdLcztSfzjcxx.getAgentPk()))
        {
            // 修改
            dwdLcztSfzjcxxMapper.updateById(dwdLcztSfzjcxx);
        }
        else
        {
            // 新增 主键
            dwdLcztSfzjcxxMapper.insert(dwdLcztSfzjcxx);
        }
        return AjaxResult.success("操作成功！",dwdLcztSfzjcxx.getAgentPk());
    }

    /**
     * 批量删除收费站基础信息
     *
     * @param agentPks 需要删除的收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteDwdLcztSfzjcxxByIds(String[] agentPks)
    {
        int count = dwdLcztSfzjcxxMapper.deleteDwdLcztSfzjcxxByIds(agentPks);
        return AjaxResult.success(count);
    }

    @Override
    public void truncateTable() {
        dwdLcztSfzjcxxMapper.truncateTable();
    }

    /**
     * 删除收费站基础信息信息
     *
     * @param agentPk 收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteDwdLcztSfzjcxxById(String agentPk)
    {
        int count = dwdLcztSfzjcxxMapper.deleteDwdLcztSfzjcxxById(agentPk);
        return AjaxResult.success(count);
    }



}
