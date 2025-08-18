package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.GantryCar;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 门架拍识查询Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface GantryCarMapper extends BaseMapper<GantryCar> {
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
     * 批量删除门架拍识查询
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteGantryCarByIds(String[] ids);

    /**
     * 删除门架拍识查询
     *
     * @param id 门架拍识查询ID
     * @return 结果
     */
    int deleteGantryCarById(String id);

}
