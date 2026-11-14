package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsSzdnGantry;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 门架信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsSzdnGantryService extends IService<OdsSzdnGantry> {
    /**
     * 查询门架信息
     *
     * @param id 门架信息ID
     * @return 门架信息
     */
    OdsSzdnGantry selectOdsSzdnGantryById(String id);

    /**
     * 查询门架信息列表
     *
     * @param odsSzdnGantry 门架信息
     * @return 门架信息集合
     */
    List<OdsSzdnGantry> selectOdsSzdnGantryList(OdsSzdnGantry odsSzdnGantry);


    /**
     * 新增或者修改门架信息
     *
     * @param odsSzdnGantry 门架信息
     * @return 结果
     */
    AjaxResult saveOdsSzdnGantry(OdsSzdnGantry odsSzdnGantry);

    /**
     * 批量删除门架信息
     *
     * @param ids 需要删除的门架信息ID
     * @return 结果
     */
    AjaxResult deleteOdsSzdnGantryByIds(String[] ids);

    void truncateTable();


    /**
     * 查询门架信息列表
     *
     * @param odsSzdnGantry 门架信息
     * @return 门架信息集合
     */
    List<OdsSzdnGantry> selectOdsSzdnGantryListNew(OdsSzdnGantry odsSzdnGantry);

}
