package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseOrgInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 机构信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseOrgInfoService extends IService<BaseOrgInfo> {
    /**
     * 查询机构信息
     *
     * @param bigId 机构信息ID
     * @return 机构信息
     */
    BaseOrgInfo selectBaseOrgInfoById(String bigId);

    /**
     * 查询机构信息列表
     *
     * @param baseOrgInfo 机构信息
     * @return 机构信息集合
     */
    List<BaseOrgInfo> selectBaseOrgInfoList(BaseOrgInfo baseOrgInfo);


    /**
     * 新增或者修改机构信息
     *
     * @param baseOrgInfo 机构信息
     * @return 结果
     */
    AjaxResult saveBaseOrgInfo(BaseOrgInfo baseOrgInfo);

    /**
     * 批量删除机构信息
     *
     * @param bigIds 需要删除的机构信息ID
     * @return 结果
     */
    AjaxResult deleteBaseOrgInfoByIds(String[] bigIds);

}
