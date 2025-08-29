package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.DwdLcztSfzjcxx;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface DwdLcztSfzjcxxMapper extends BaseMapper<DwdLcztSfzjcxx> {
    /**
     * 查询收费站基础信息
     *
     * @param agentPk 收费站基础信息ID
     * @return 收费站基础信息
     */
    DwdLcztSfzjcxx selectDwdLcztSfzjcxxById(String agentPk);

    /**
     * 查询收费站基础信息列表
     *
     * @param dwdLcztSfzjcxx 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<DwdLcztSfzjcxx> selectDwdLcztSfzjcxxList(DwdLcztSfzjcxx dwdLcztSfzjcxx);

    /**
     * 批量删除收费站基础信息
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteDwdLcztSfzjcxxByIds(String[] agentPks);

    /**
     * 删除收费站基础信息
     *
     * @param agentPk 收费站基础信息ID
     * @return 结果
     */
    int deleteDwdLcztSfzjcxxById(String agentPk);

}
