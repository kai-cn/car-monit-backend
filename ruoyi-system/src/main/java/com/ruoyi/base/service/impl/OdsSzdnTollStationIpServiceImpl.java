package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsSzdnTollStationIp;
import com.ruoyi.base.mapper.OdsSzdnTollStationIpMapper;
import com.ruoyi.base.service.IOdsSzdnTollStationIpService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 收费站ipService业务层处理
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Service
public class OdsSzdnTollStationIpServiceImpl extends ServiceImpl<OdsSzdnTollStationIpMapper, OdsSzdnTollStationIp> implements IOdsSzdnTollStationIpService {

    @Autowired
    private OdsSzdnTollStationIpMapper odsSzdnTollStationIpMapper;

    /**
     * 查询收费站ip
     *
     * @param id 收费站ipID
     * @return 收费站ip
     */
    @Override
    public OdsSzdnTollStationIp selectOdsSzdnTollStationIpById(Long id) {
        return odsSzdnTollStationIpMapper.selectOdsSzdnTollStationIpById(id);
    }

    /**
     * 查询收费站ip列表
     *
     * @param odsSzdnTollStationIp 收费站ip
     * @return 收费站ip
     */
    @Override
    public List<OdsSzdnTollStationIp> selectOdsSzdnTollStationIpList(OdsSzdnTollStationIp odsSzdnTollStationIp) {
        return odsSzdnTollStationIpMapper.selectOdsSzdnTollStationIpList(odsSzdnTollStationIp);
    }


}
