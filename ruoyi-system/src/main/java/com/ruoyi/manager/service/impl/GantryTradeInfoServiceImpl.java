package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.GantryTradeInfoMapper;
import com.ruoyi.manager.domain.GantryTradeInfo;
import com.ruoyi.manager.service.IGantryTradeInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架交易查询Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class GantryTradeInfoServiceImpl extends ServiceImpl<GantryTradeInfoMapper, GantryTradeInfo> implements IGantryTradeInfoService {

    @Autowired
    private GantryTradeInfoMapper gantryTradeInfoMapper;

    /**
     * 查询门架交易查询
     *
     * @param id 门架交易查询ID
     * @return 门架交易查询
     */
    @Override
    public GantryTradeInfo selectGantryTradeInfoById(String id) {
        return gantryTradeInfoMapper.selectGantryTradeInfoById(id);
    }

    /**
     * 查询门架交易查询列表
     *
     * @param gantryTradeInfo 门架交易查询
     * @return 门架交易查询
     */
    @Override
    public List<GantryTradeInfo> selectGantryTradeInfoList(GantryTradeInfo gantryTradeInfo) {
        return gantryTradeInfoMapper.selectGantryTradeInfoList(gantryTradeInfo);
    }


    /**
     * 新增或者修改门架交易查询
     *
     * @param gantryTradeInfo 门架交易查询
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveGantryTradeInfo(GantryTradeInfo gantryTradeInfo)
    {
        if (CommonUtil.isNotBlank(gantryTradeInfo.getId()))
        {
            // 修改
            gantryTradeInfoMapper.updateById(gantryTradeInfo);
        }
        else
        {
            // 新增 主键
            gantryTradeInfoMapper.insert(gantryTradeInfo);
        }
        return AjaxResult.success("操作成功！",gantryTradeInfo.getId());
    }

    /**
     * 批量删除门架交易查询
     *
     * @param ids 需要删除的门架交易查询ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteGantryTradeInfoByIds(String[] ids)
    {
        int count = gantryTradeInfoMapper.deleteGantryTradeInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除门架交易查询信息
     *
     * @param id 门架交易查询ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteGantryTradeInfoById(String id)
    {
        int count = gantryTradeInfoMapper.deleteGantryTradeInfoById(id);
        return AjaxResult.success(count);
    }



}
