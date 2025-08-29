package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsLwzxsfsjFeeStationExit01Mapper;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01;
import com.ruoyi.base.service.IOdsLwzxsfsjFeeStationExit01Service;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站出口流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsLwzxsfsjFeeStationExit01ServiceImpl extends ServiceImpl<OdsLwzxsfsjFeeStationExit01Mapper, OdsLwzxsfsjFeeStationExit01> implements IOdsLwzxsfsjFeeStationExit01Service {

    @Autowired
    private OdsLwzxsfsjFeeStationExit01Mapper odsLwzxsfsjFeeStationExit01Mapper;

    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    @Override
    public OdsLwzxsfsjFeeStationExit01 selectOdsLwzxsfsjFeeStationExit01ById(String bigId) {
        return odsLwzxsfsjFeeStationExit01Mapper.selectOdsLwzxsfsjFeeStationExit01ById(bigId);
    }

    /**
     * 查询收费站出口流水列表
     *
     * @param odsLwzxsfsjFeeStationExit01 收费站出口流水
     * @return 收费站出口流水
     */
    @Override
    public List<OdsLwzxsfsjFeeStationExit01> selectOdsLwzxsfsjFeeStationExit01List(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01) {
        return odsLwzxsfsjFeeStationExit01Mapper.selectOdsLwzxsfsjFeeStationExit01List(odsLwzxsfsjFeeStationExit01);
    }


    /**
     * 新增或者修改收费站出口流水
     *
     * @param odsLwzxsfsjFeeStationExit01 收费站出口流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsLwzxsfsjFeeStationExit01(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01)
    {
        if (CommonUtil.isNotBlank(odsLwzxsfsjFeeStationExit01.getBigId()))
        {
            // 修改
            odsLwzxsfsjFeeStationExit01Mapper.updateById(odsLwzxsfsjFeeStationExit01);
        }
        else
        {
            // 新增 主键
            odsLwzxsfsjFeeStationExit01Mapper.insert(odsLwzxsfsjFeeStationExit01);
        }
        return AjaxResult.success("操作成功！",odsLwzxsfsjFeeStationExit01.getBigId());
    }

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的收费站出口流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsLwzxsfsjFeeStationExit01ByIds(String[] bigIds)
    {
        int count = odsLwzxsfsjFeeStationExit01Mapper.deleteOdsLwzxsfsjFeeStationExit01ByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费站出口流水信息
     *
     * @param bigId 收费站出口流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsLwzxsfsjFeeStationExit01ById(String bigId)
    {
        int count = odsLwzxsfsjFeeStationExit01Mapper.deleteOdsLwzxsfsjFeeStationExit01ById(bigId);
        return AjaxResult.success(count);
    }



}
