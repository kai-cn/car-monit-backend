package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.DwdLcztFwqjcxxMapper;
import com.ruoyi.base.domain.DwdLcztFwqjcxx;
import com.ruoyi.base.service.IDwdLcztFwqjcxxService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 服务区基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class DwdLcztFwqjcxxServiceImpl extends ServiceImpl<DwdLcztFwqjcxxMapper, DwdLcztFwqjcxx> implements IDwdLcztFwqjcxxService {

    @Autowired
    private DwdLcztFwqjcxxMapper dwdLcztFwqjcxxMapper;

    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    @Override
    public DwdLcztFwqjcxx selectDwdLcztFwqjcxxById(String agentPk) {
        return dwdLcztFwqjcxxMapper.selectDwdLcztFwqjcxxById(agentPk);
    }

    /**
     * 查询服务区基础信息列表
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 服务区基础信息
     */
    @Override
    public List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxList(DwdLcztFwqjcxx dwdLcztFwqjcxx) {
        return dwdLcztFwqjcxxMapper.selectDwdLcztFwqjcxxList(dwdLcztFwqjcxx);
    }


    /**
     * 新增或者修改服务区基础信息
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveDwdLcztFwqjcxx(DwdLcztFwqjcxx dwdLcztFwqjcxx)
    {
        if (CommonUtil.isNotBlank(dwdLcztFwqjcxx.getAgentPk()))
        {
            // 修改
            dwdLcztFwqjcxxMapper.updateById(dwdLcztFwqjcxx);
        }
        else
        {
            // 新增 主键
            dwdLcztFwqjcxxMapper.insert(dwdLcztFwqjcxx);
        }
        return AjaxResult.success("操作成功！",dwdLcztFwqjcxx.getAgentPk());
    }

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的服务区基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteDwdLcztFwqjcxxByIds(String[] agentPks)
    {
        int count = dwdLcztFwqjcxxMapper.deleteDwdLcztFwqjcxxByIds(agentPks);
        return AjaxResult.success(count);
    }

    @Override
    public void truncateTable() {
        dwdLcztFwqjcxxMapper.truncateTable();
    }

    /**
     * 删除服务区基础信息信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteDwdLcztFwqjcxxById(String agentPk)
    {
        int count = dwdLcztFwqjcxxMapper.deleteDwdLcztFwqjcxxById(agentPk);
        return AjaxResult.success(count);
    }


    /**
     * 查询服务区基础信息列表
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 服务区基础信息集合
     */
    public List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxListNew(DwdLcztFwqjcxx dwdLcztFwqjcxx){
        return dwdLcztFwqjcxxMapper.selectDwdLcztFwqjcxxListNew(dwdLcztFwqjcxx);
    }



}
