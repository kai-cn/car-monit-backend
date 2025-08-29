package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsSzdnSection;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 路段信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsSzdnSectionMapper extends BaseMapper<OdsSzdnSection> {
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
     * 批量删除路段信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsSzdnSectionByIds(String[] ids);

    /**
     * 删除路段信息
     *
     * @param id 路段信息ID
     * @return 结果
     */
    int deleteOdsSzdnSectionById(String id);

    /**
     * 清空表
     */
    @Update("TRUNCATE TABLE ods_szdn_section")
    void truncateTable();

}
