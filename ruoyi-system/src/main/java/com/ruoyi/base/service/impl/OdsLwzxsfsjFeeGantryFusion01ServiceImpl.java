package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;
import com.ruoyi.base.mapper.OdsLwzxsfsjFeeGantryFusion01Mapper;
import com.ruoyi.base.service.IOdsLwzxsfsjFeeGantryFusion01Service;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 交易流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsLwzxsfsjFeeGantryFusion01ServiceImpl extends ServiceImpl<OdsLwzxsfsjFeeGantryFusion01Mapper, OdsLwzxsfsjFeeGantryFusion01> implements IOdsLwzxsfsjFeeGantryFusion01Service {

    @Autowired
    private OdsLwzxsfsjFeeGantryFusion01Mapper odsLwzxsfsjFeeGantryFusion01Mapper;

    /**
     * 查询交易流水
     *
     * @param bigId 交易流水ID
     * @return 交易流水
     */
    @Override
    public OdsLwzxsfsjFeeGantryFusion01 selectOdsLwzxsfsjFeeGantryFusion01ById(String bigId) {
        return odsLwzxsfsjFeeGantryFusion01Mapper.selectOdsLwzxsfsjFeeGantryFusion01ById(bigId);
    }

    /**
     * 查询交易流水列表
     *
     * @param odsLwzxsfsjFeeGantryFusion01 交易流水
     * @return 交易流水
     */
    @Override
    public List<OdsLwzxsfsjFeeGantryFusion01> selectOdsLwzxsfsjFeeGantryFusion01List(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
        return odsLwzxsfsjFeeGantryFusion01Mapper.selectOdsLwzxsfsjFeeGantryFusion01List(odsLwzxsfsjFeeGantryFusion01);
    }


    /**
     * 新增或者修改交易流水
     *
     * @param odsLwzxsfsjFeeGantryFusion01 交易流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsLwzxsfsjFeeGantryFusion01(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01)
    {
        if (CommonUtil.isNotBlank(odsLwzxsfsjFeeGantryFusion01.getId()))
        {
            // 修改
            odsLwzxsfsjFeeGantryFusion01Mapper.updateById(odsLwzxsfsjFeeGantryFusion01);
        }
        else
        {
            // 新增 主键
            odsLwzxsfsjFeeGantryFusion01Mapper.insert(odsLwzxsfsjFeeGantryFusion01);
        }
        return AjaxResult.success("操作成功！",odsLwzxsfsjFeeGantryFusion01.getId());
    }

    /**
     * 批量删除交易流水
     *
     * @param bigIds 需要删除的交易流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsLwzxsfsjFeeGantryFusion01ByIds(String[] bigIds)
    {
        int count = odsLwzxsfsjFeeGantryFusion01Mapper.deleteOdsLwzxsfsjFeeGantryFusion01ByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除交易流水信息
     *
     * @param bigId 交易流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsLwzxsfsjFeeGantryFusion01ById(String bigId)
    {
        int count = odsLwzxsfsjFeeGantryFusion01Mapper.deleteOdsLwzxsfsjFeeGantryFusion01ById(bigId);
        return AjaxResult.success(count);
    }



}
