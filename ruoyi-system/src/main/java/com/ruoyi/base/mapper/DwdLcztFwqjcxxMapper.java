package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.DwdLcztFwqjcxx;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 服务区基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface DwdLcztFwqjcxxMapper extends BaseMapper<DwdLcztFwqjcxx> {
    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    DwdLcztFwqjcxx selectDwdLcztFwqjcxxById(String agentPk);

    /**
     * 查询服务区基础信息列表
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 服务区基础信息集合
     */
    List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxList(DwdLcztFwqjcxx dwdLcztFwqjcxx);

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteDwdLcztFwqjcxxByIds(String[] agentPks);

    /**
     * 删除服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 结果
     */
    int deleteDwdLcztFwqjcxxById(String agentPk);

}
