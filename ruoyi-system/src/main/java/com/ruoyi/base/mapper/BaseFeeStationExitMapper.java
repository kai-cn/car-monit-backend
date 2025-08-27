package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseFeeStationExit;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站出口流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseFeeStationExitMapper extends BaseMapper<BaseFeeStationExit> {
    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    BaseFeeStationExit selectBaseFeeStationExitById(String bigId);

    /**
     * 查询收费站出口流水列表
     *
     * @param baseFeeStationExit 收费站出口流水
     * @return 收费站出口流水集合
     */
    List<BaseFeeStationExit> selectBaseFeeStationExitList(BaseFeeStationExit baseFeeStationExit);

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseFeeStationExitByIds(String[] bigIds);

    /**
     * 删除收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 结果
     */
    int deleteBaseFeeStationExitById(String bigId);

}
