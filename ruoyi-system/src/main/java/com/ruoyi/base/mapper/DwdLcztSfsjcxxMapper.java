package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.DwdLcztSfsjcxx;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费所基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface DwdLcztSfsjcxxMapper extends BaseMapper<DwdLcztSfsjcxx> {
    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    DwdLcztSfsjcxx selectDwdLcztSfsjcxxById(String agentPk);

    /**
     * 查询收费所基础信息列表
     *
     * @param dwdLcztSfsjcxx 收费所基础信息
     * @return 收费所基础信息集合
     */
    List<DwdLcztSfsjcxx> selectDwdLcztSfsjcxxList(DwdLcztSfsjcxx dwdLcztSfsjcxx);

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteDwdLcztSfsjcxxByIds(String[] agentPks);

    /**
     * 删除收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 结果
     */
    int deleteDwdLcztSfsjcxxById(String agentPk);

}
