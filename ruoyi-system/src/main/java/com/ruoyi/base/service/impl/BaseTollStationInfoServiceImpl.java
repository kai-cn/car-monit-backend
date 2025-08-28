package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.BaseTollStationInfo;
import com.ruoyi.base.mapper.BaseTollStationInfoMapper;
import com.ruoyi.base.service.IBaseTollStationInfoService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseTollStationInfoServiceImpl extends ServiceImpl<BaseTollStationInfoMapper, BaseTollStationInfo> implements IBaseTollStationInfoService {

    @Autowired
    private BaseTollStationInfoMapper baseTollStationInfoMapper;

    /**
     * 查询收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 收费站基础信息
     */
    @Override
    public BaseTollStationInfo selectBaseTollStationInfoById(String id) {
        return baseTollStationInfoMapper.selectBaseTollStationInfoById(id);
    }

    /**
     * 查询收费站基础信息列表
     *
     * @param baseTollStationInfo 收费站基础信息
     * @return 收费站基础信息
     */
    @Override
    public List<BaseTollStationInfo> selectBaseTollStationInfoList(BaseTollStationInfo baseTollStationInfo) {
        return baseTollStationInfoMapper.selectBaseTollStationInfoList(baseTollStationInfo);
    }


    /**
     * 新增或者修改收费站基础信息
     *
     * @param baseTollStationInfo 收费站基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseTollStationInfo(BaseTollStationInfo baseTollStationInfo)
    {
        if (CommonUtil.isNotBlank(baseTollStationInfo.getId()))
        {
            // 修改
            baseTollStationInfoMapper.updateById(baseTollStationInfo);
        }
        else
        {
            // 新增 主键
            baseTollStationInfo.setDelFlag("0");
            baseTollStationInfo.setCreateTime(DateUtils.getTimestamp());
            baseTollStationInfo.setUpdateTime(DateUtils.getTimestamp());
            baseTollStationInfo.setCreateBy(1L);

            baseTollStationInfoMapper.insert(baseTollStationInfo);
        }
        return AjaxResult.success("操作成功！",baseTollStationInfo.getId());
    }

    /**
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseTollStationInfoByIds(String[] ids)
    {
        int count = baseTollStationInfoMapper.deleteBaseTollStationInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费站基础信息信息
     *
     * @param id 收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseTollStationInfoById(String id)
    {
        int count = baseTollStationInfoMapper.deleteBaseTollStationInfoById(id);
        return AjaxResult.success(count);
    }



}
