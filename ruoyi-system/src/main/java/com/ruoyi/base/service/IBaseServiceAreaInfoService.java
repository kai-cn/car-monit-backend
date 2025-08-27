package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseServiceAreaInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 服务区基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseServiceAreaInfoService extends IService<BaseServiceAreaInfo> {
    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    BaseServiceAreaInfo selectBaseServiceAreaInfoById(String agentPk);

    /**
     * 查询服务区基础信息列表
     *
     * @param baseServiceAreaInfo 服务区基础信息
     * @return 服务区基础信息集合
     */
    List<BaseServiceAreaInfo> selectBaseServiceAreaInfoList(BaseServiceAreaInfo baseServiceAreaInfo);


    /**
     * 新增或者修改服务区基础信息
     *
     * @param baseServiceAreaInfo 服务区基础信息
     * @return 结果
     */
    AjaxResult saveBaseServiceAreaInfo(BaseServiceAreaInfo baseServiceAreaInfo);

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的服务区基础信息ID
     * @return 结果
     */
    AjaxResult deleteBaseServiceAreaInfoByIds(String[] agentPks);

}
