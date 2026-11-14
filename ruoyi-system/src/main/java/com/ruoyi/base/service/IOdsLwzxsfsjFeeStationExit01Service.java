package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 收费站出口流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsLwzxsfsjFeeStationExit01Service extends IService<OdsLwzxsfsjFeeStationExit01> {
    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    OdsLwzxsfsjFeeStationExit01 selectOdsLwzxsfsjFeeStationExit01ById(String bigId);

    /**
     * 查询收费站出口流水列表
     *
     * @param odsLwzxsfsjFeeStationExit01 收费站出口流水
     * @return 收费站出口流水集合
     */
    List<OdsLwzxsfsjFeeStationExit01> selectOdsLwzxsfsjFeeStationExit01List(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01);


    /**
     * 新增或者修改收费站出口流水
     *
     * @param odsLwzxsfsjFeeStationExit01 收费站出口流水
     * @return 结果
     */
    AjaxResult saveOdsLwzxsfsjFeeStationExit01(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01);

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的收费站出口流水ID
     * @return 结果
     */
    AjaxResult deleteOdsLwzxsfsjFeeStationExit01ByIds(String[] bigIds);

}
