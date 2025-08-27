package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseSectionInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 路段信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseSectionInfoMapper extends BaseMapper<BaseSectionInfo> {
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
     * 批量删除路段信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseSectionInfoByIds(String[] ids);

    /**
     * 删除路段信息
     *
     * @param id 路段信息ID
     * @return 结果
     */
    int deleteBaseSectionInfoById(String id);

}
