package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsSzdnToll;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费站基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsSzdnTollService extends IService<OdsSzdnToll> {
    /**
     * 查询收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 收费站基础信息
     */
    OdsSzdnToll selectOdsSzdnTollById(String id);

    /**
     * 查询收费站基础信息列表
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<OdsSzdnToll> selectOdsSzdnTollList(OdsSzdnToll odsSzdnToll);


    /**
     * 新增或者修改收费站基础信息
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 结果
     */
    AjaxResult saveOdsSzdnToll(OdsSzdnToll odsSzdnToll);

    /**
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的收费站基础信息ID
     * @return 结果
     */
    AjaxResult deleteOdsSzdnTollByIds(String[] ids);

    void truncateTable();


    /**
     * 查询收费站基础信息列表
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<OdsSzdnToll> selectOdsSzdnTollListNew(OdsSzdnToll odsSzdnToll);

}
