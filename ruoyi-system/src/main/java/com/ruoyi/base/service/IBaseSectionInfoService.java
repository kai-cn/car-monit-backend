package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseSectionInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 路段信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseSectionInfoService extends IService<BaseSectionInfo> {
    /**
     * 查询路段信息
     *
     * @param id 路段信息ID
     * @return 路段信息
     */
    BaseSectionInfo selectBaseSectionInfoById(String id);

    /**
     * 查询路段信息列表
     *
     * @param baseSectionInfo 路段信息
     * @return 路段信息集合
     */
    List<BaseSectionInfo> selectBaseSectionInfoList(BaseSectionInfo baseSectionInfo);


    /**
     * 新增或者修改路段信息
     *
     * @param baseSectionInfo 路段信息
     * @return 结果
     */
    AjaxResult saveBaseSectionInfo(BaseSectionInfo baseSectionInfo);

    /**
     * 批量删除路段信息
     *
     * @param ids 需要删除的路段信息ID
     * @return 结果
     */
    AjaxResult deleteBaseSectionInfoByIds(String[] ids);

}
