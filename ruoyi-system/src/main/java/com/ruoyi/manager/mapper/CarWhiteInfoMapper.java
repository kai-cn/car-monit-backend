package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarWhiteInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车俩白名单Mapper接口
 *
 * @author ruoyi
 * @date 2025-09-12
 */
@Repository
public interface CarWhiteInfoMapper extends BaseMapper<CarWhiteInfo> {
    /**
     * 查询车俩白名单
     *
     * @param id 车俩白名单ID
     * @return 车俩白名单
     */
    CarWhiteInfo selectCarWhiteInfoById(String id);

    /**
     * 查询车俩白名单列表
     *
     * @param carWhiteInfo 车俩白名单
     * @return 车俩白名单集合
     */
    List<CarWhiteInfo> selectCarWhiteInfoList(CarWhiteInfo carWhiteInfo);

    /**
     * 批量删除车俩白名单
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarWhiteInfoByIds(String[] ids);

    /**
     * 删除车俩白名单
     *
     * @param id 车俩白名单ID
     * @return 结果
     */
    int deleteCarWhiteInfoById(String id);

}
