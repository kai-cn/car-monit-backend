package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsSzdnGantry;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 门架信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsSzdnGantryMapper extends BaseMapper<OdsSzdnGantry> {
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
     * 批量删除门架信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsSzdnGantryByIds(String[] ids);

    /**
     * 删除门架信息
     *
     * @param id 门架信息ID
     * @return 结果
     */
    int deleteOdsSzdnGantryById(String id);

    @Update("TRUNCATE TABLE ods_szdn_gantry")
    void truncateTable();


    /**
     * 查询门架信息列表
     *
     * @param odsSzdnGantry 门架信息
     * @return 门架信息集合
     */
    List<OdsSzdnGantry> selectOdsSzdnGantryListNew(OdsSzdnGantry odsSzdnGantry);
}
