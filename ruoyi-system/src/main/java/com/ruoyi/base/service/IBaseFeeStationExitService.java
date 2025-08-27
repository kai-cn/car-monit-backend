package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseFeeStationExit;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费站出口流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseFeeStationExitService extends IService<BaseFeeStationExit> {
    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    BaseFeeStationExit selectBaseFeeStationExitById(String bigId);

    /**
     * 查询收费站出口流水列表
     *
     * @param baseFeeStationExit 收费站出口流水
     * @return 收费站出口流水集合
     */
    List<BaseFeeStationExit> selectBaseFeeStationExitList(BaseFeeStationExit baseFeeStationExit);


    /**
     * 新增或者修改收费站出口流水
     *
     * @param baseFeeStationExit 收费站出口流水
     * @return 结果
     */
    AjaxResult saveBaseFeeStationExit(BaseFeeStationExit baseFeeStationExit);

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的收费站出口流水ID
     * @return 结果
     */
    AjaxResult deleteBaseFeeStationExitByIds(String[] bigIds);

}
