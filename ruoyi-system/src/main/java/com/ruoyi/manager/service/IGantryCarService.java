package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.GantryCar;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 门架拍识查询Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface IGantryCarService extends IService<GantryCar> {
    /**
     * 查询门架拍识查询
     *
     * @param id 门架拍识查询ID
     * @return 门架拍识查询
     */
    GantryCar selectGantryCarById(String id);

    /**
     * 查询门架拍识查询列表
     *
     * @param gantryCar 门架拍识查询
     * @return 门架拍识查询集合
     */
    List<GantryCar> selectGantryCarList(GantryCar gantryCar);


    /**
     * 新增或者修改门架拍识查询
     *
     * @param gantryCar 门架拍识查询
     * @return 结果
     */
    AjaxResult saveGantryCar(GantryCar gantryCar);

    /**
     * 批量删除门架拍识查询
     *
     * @param ids 需要删除的门架拍识查询ID
     * @return 结果
     */
    AjaxResult deleteGantryCarByIds(String[] ids);

}
