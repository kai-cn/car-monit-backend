package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseFeeStationExitMapper;
import com.ruoyi.base.domain.BaseFeeStationExit;
import com.ruoyi.base.service.IBaseFeeStationExitService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站出口流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseFeeStationExitServiceImpl extends ServiceImpl<BaseFeeStationExitMapper, BaseFeeStationExit> implements IBaseFeeStationExitService {

    @Autowired
    private BaseFeeStationExitMapper baseFeeStationExitMapper;

    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    @Override
    public BaseFeeStationExit selectBaseFeeStationExitById(String bigId) {
        return baseFeeStationExitMapper.selectBaseFeeStationExitById(bigId);
    }

    /**
     * 查询收费站出口流水列表
     *
     * @param baseFeeStationExit 收费站出口流水
     * @return 收费站出口流水
     */
    @Override
    public List<BaseFeeStationExit> selectBaseFeeStationExitList(BaseFeeStationExit baseFeeStationExit) {
        return baseFeeStationExitMapper.selectBaseFeeStationExitList(baseFeeStationExit);
    }


    /**
     * 新增或者修改收费站出口流水
     *
     * @param baseFeeStationExit 收费站出口流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseFeeStationExit(BaseFeeStationExit baseFeeStationExit)
    {
        if (CommonUtil.isNotBlank(baseFeeStationExit.getId()))
        {
            // 修改
            baseFeeStationExitMapper.updateById(baseFeeStationExit);
        }
        else
        {
            // 新增 主键
            baseFeeStationExitMapper.insert(baseFeeStationExit);
        }
        return AjaxResult.success("操作成功！",baseFeeStationExit.getId());
    }

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的收费站出口流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseFeeStationExitByIds(String[] bigIds)
    {
        int count = baseFeeStationExitMapper.deleteBaseFeeStationExitByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费站出口流水信息
     *
     * @param bigId 收费站出口流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseFeeStationExitById(String bigId)
    {
        int count = baseFeeStationExitMapper.deleteBaseFeeStationExitById(bigId);
        return AjaxResult.success(count);
    }



}
