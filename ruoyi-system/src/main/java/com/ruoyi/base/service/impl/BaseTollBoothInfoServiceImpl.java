package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseTollBoothInfoMapper;
import com.ruoyi.base.domain.BaseTollBoothInfo;
import com.ruoyi.base.service.IBaseTollBoothInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费所基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseTollBoothInfoServiceImpl extends ServiceImpl<BaseTollBoothInfoMapper, BaseTollBoothInfo> implements IBaseTollBoothInfoService {

    @Autowired
    private BaseTollBoothInfoMapper baseTollBoothInfoMapper;

    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    @Override
    public BaseTollBoothInfo selectBaseTollBoothInfoById(String agentPk) {
        return baseTollBoothInfoMapper.selectBaseTollBoothInfoById(agentPk);
    }

    /**
     * 查询收费所基础信息列表
     *
     * @param baseTollBoothInfo 收费所基础信息
     * @return 收费所基础信息
     */
    @Override
    public List<BaseTollBoothInfo> selectBaseTollBoothInfoList(BaseTollBoothInfo baseTollBoothInfo) {
        return baseTollBoothInfoMapper.selectBaseTollBoothInfoList(baseTollBoothInfo);
    }


    /**
     * 新增或者修改收费所基础信息
     *
     * @param baseTollBoothInfo 收费所基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseTollBoothInfo(BaseTollBoothInfo baseTollBoothInfo)
    {
        if (CommonUtil.isNotBlank(baseTollBoothInfo.getId()))
        {
            // 修改
            baseTollBoothInfoMapper.updateById(baseTollBoothInfo);
        }
        else
        {
            // 新增 主键
            baseTollBoothInfoMapper.insert(baseTollBoothInfo);
        }
        return AjaxResult.success("操作成功！",baseTollBoothInfo.getId());
    }

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的收费所基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseTollBoothInfoByIds(String[] agentPks)
    {
        int count = baseTollBoothInfoMapper.deleteBaseTollBoothInfoByIds(agentPks);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费所基础信息信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseTollBoothInfoById(String agentPk)
    {
        int count = baseTollBoothInfoMapper.deleteBaseTollBoothInfoById(agentPk);
        return AjaxResult.success(count);
    }



}
