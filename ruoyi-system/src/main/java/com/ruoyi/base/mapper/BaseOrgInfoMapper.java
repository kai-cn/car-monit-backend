package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseOrgInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 机构信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseOrgInfoMapper extends BaseMapper<BaseOrgInfo> {
    /**
     * 查询机构信息
     *
     * @param bigId 机构信息ID
     * @return 机构信息
     */
    BaseOrgInfo selectBaseOrgInfoById(String bigId);

    /**
     * 查询机构信息列表
     *
     * @param baseOrgInfo 机构信息
     * @return 机构信息集合
     */
    List<BaseOrgInfo> selectBaseOrgInfoList(BaseOrgInfo baseOrgInfo);

    /**
     * 批量删除机构信息
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseOrgInfoByIds(String[] bigIds);

    /**
     * 删除机构信息
     *
     * @param bigId 机构信息ID
     * @return 结果
     */
    int deleteBaseOrgInfoById(String bigId);

}
