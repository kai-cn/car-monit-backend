package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsSzdnSection;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 路段信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsSzdnSectionService extends IService<OdsSzdnSection> {
    /**
     * 查询路段信息
     *
     * @param id 路段信息ID
     * @return 路段信息
     */
    OdsSzdnSection selectOdsSzdnSectionById(String id);

    /**
     * 查询路段信息列表
     *
     * @param odsSzdnSection 路段信息
     * @return 路段信息集合
     */
    List<OdsSzdnSection> selectOdsSzdnSectionList(OdsSzdnSection odsSzdnSection);


    /**
     * 新增或者修改路段信息
     *
     * @param odsSzdnSection 路段信息
     * @return 结果
     */
    AjaxResult saveOdsSzdnSection(OdsSzdnSection odsSzdnSection);

    /**
     * 批量删除路段信息
     *
     * @param ids 需要删除的路段信息ID
     * @return 结果
     */
    AjaxResult deleteOdsSzdnSectionByIds(String[] ids);

    /**
     * 清空表数据
     */
    void truncateTable();


    /**
     * 查询路段信息列表
     *
     * @param odsSzdnSection 路段信息
     * @return 路段信息集合
     */
    List<OdsSzdnSection> selectOdsSzdnSectionListNew(OdsSzdnSection odsSzdnSection);

}
