package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsSzdnTollStationIp;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 收费站ipMapper接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Repository
public interface OdsSzdnTollStationIpMapper extends BaseMapper<OdsSzdnTollStationIp> {
    /**
     * 查询收费站ip
     *
     * @param id 收费站ipID
     * @return 收费站ip
     */
    OdsSzdnTollStationIp selectOdsSzdnTollStationIpById(Long id);

    /**
     * 查询收费站ip列表
     *
     * @param odsSzdnTollStationIp 收费站ip
     * @return 收费站ip集合
     */
    List<OdsSzdnTollStationIp> selectOdsSzdnTollStationIpList(OdsSzdnTollStationIp odsSzdnTollStationIp);


}
