package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarWarningInfo;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 预警车辆Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarWarningInfoMapper extends BaseMapper<CarWarningInfo> {
    /**
     * 查询预警车辆
     *
     * @param id 预警车辆ID
     * @return 预警车辆
     */
    CarWarningInfo selectCarWarningInfoById(String id);

    /**
     * 查询预警车辆列表
     *
     * @param carWarningInfo 预警车辆
     * @return 预警车辆集合
     */
    List<CarWarningInfo> selectCarWarningInfoList(CarWarningInfo carWarningInfo);

    /**
     * 批量删除预警车辆
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarWarningInfoByIds(String[] ids);

    /**
     * 删除预警车辆
     *
     * @param id 预警车辆ID
     * @return 结果
     */
    int deleteCarWarningInfoById(String id);

    /**
     * 批量删除预警车辆
     *
     * @param idList
     * @return 结果
     */
    int deleteCarWarningInfoByUUid(@Param("idList") List<String> idList);


    List<CarWarningInfo> selectCarWarningInfoListLimit100(CarWarningInfo carWarningInfo);
}
