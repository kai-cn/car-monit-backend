package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsSzdnGantryIp;
import com.ruoyi.base.mapper.OdsSzdnGantryIpMapper;
import com.ruoyi.base.service.IOdsSzdnGantryIpService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 省界设备ipService业务层处理
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Service
public class OdsSzdnGantryIpServiceImpl extends ServiceImpl<OdsSzdnGantryIpMapper, OdsSzdnGantryIp> implements IOdsSzdnGantryIpService {

    @Autowired
    private OdsSzdnGantryIpMapper odsSzdnGantryIpMapper;

    /**
     * 查询省界设备ip
     *
     * @param id 省界设备ipID
     * @return 省界设备ip
     */
    @Override
    public OdsSzdnGantryIp selectOdsSzdnGantryIpById(Long id) {
        return odsSzdnGantryIpMapper.selectOdsSzdnGantryIpById(id);
    }

    /**
     * 查询省界设备ip列表
     *
     * @param odsSzdnGantryIp 省界设备ip
     * @return 省界设备ip
     */
    @Override
    public List<OdsSzdnGantryIp> selectOdsSzdnGantryIpList(OdsSzdnGantryIp odsSzdnGantryIp) {
        return odsSzdnGantryIpMapper.selectOdsSzdnGantryIpList(odsSzdnGantryIp);
    }





}
