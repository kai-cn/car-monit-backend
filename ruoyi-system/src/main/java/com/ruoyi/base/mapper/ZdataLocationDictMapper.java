package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.ZdataLocationDict;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车辆位置Mapper接口
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Repository
public interface ZdataLocationDictMapper extends BaseMapper<ZdataLocationDict> {
    /**
     * 查询车辆位置
     *
     * @param id 车辆位置ID
     * @return 车辆位置
     */
    ZdataLocationDict selectZdataLocationDictById(Long id);

    /**
     * 查询车辆位置列表
     *
     * @param zdataLocationDict 车辆位置
     * @return 车辆位置集合
     */
    List<ZdataLocationDict> selectZdataLocationDictList(ZdataLocationDict zdataLocationDict);



}
