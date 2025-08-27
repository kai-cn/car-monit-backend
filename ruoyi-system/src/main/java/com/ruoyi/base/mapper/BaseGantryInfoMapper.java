package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseGantryInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 门架信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseGantryInfoMapper extends BaseMapper<BaseGantryInfo> {
    /**
     * 查询门架信息
     *
     * @param id 门架信息ID
     * @return 门架信息
     */
    BaseGantryInfo selectBaseGantryInfoById(String id);

    /**
     * 查询门架信息列表
     *
     * @param baseGantryInfo 门架信息
     * @return 门架信息集合
     */
    List<BaseGantryInfo> selectBaseGantryInfoList(BaseGantryInfo baseGantryInfo);

    /**
     * 批量删除门架信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseGantryInfoByIds(String[] ids);

    /**
     * 删除门架信息
     *
     * @param id 门架信息ID
     * @return 结果
     */
    int deleteBaseGantryInfoById(String id);

}
