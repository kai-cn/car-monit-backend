package com.ruoyi.base.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.base.domain.OdsSzdnTollStationIp;

import java.util.List;

/**
 * 收费站ipService接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
public interface IOdsSzdnTollStationIpService extends IService<OdsSzdnTollStationIp> {
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
