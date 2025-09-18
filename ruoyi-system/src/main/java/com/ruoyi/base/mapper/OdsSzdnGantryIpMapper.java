package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsSzdnGantryIp;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 省界设备ipMapper接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Repository
public interface OdsSzdnGantryIpMapper extends BaseMapper<OdsSzdnGantryIp> {
    /**
     * 查询省界设备ip
     *
     * @param id 省界设备ipID
     * @return 省界设备ip
     */
    OdsSzdnGantryIp selectOdsSzdnGantryIpById(Long id);

    /**
     * 查询省界设备ip列表
     *
     * @param odsSzdnGantryIp 省界设备ip
     * @return 省界设备ip集合
     */
    List<OdsSzdnGantryIp> selectOdsSzdnGantryIpList(OdsSzdnGantryIp odsSzdnGantryIp);


}
