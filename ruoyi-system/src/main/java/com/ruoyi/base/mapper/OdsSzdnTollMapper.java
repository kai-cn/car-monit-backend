package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsSzdnToll;
import org.apache.ibatis.annotations.Update;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsSzdnTollMapper extends BaseMapper<OdsSzdnToll> {
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
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsSzdnTollByIds(String[] ids);

    /**
     * 删除收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 结果
     */
    int deleteOdsSzdnTollById(String id);

    @Update("TRUNCATE TABLE ods_szdn_toll")
    void truncateTable();
}
