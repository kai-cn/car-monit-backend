package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.ZdataLocationDictMapper;
import com.ruoyi.base.domain.ZdataLocationDict;
import com.ruoyi.base.service.IZdataLocationDictService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 车辆位置Service业务层处理
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Service
public class ZdataLocationDictServiceImpl extends ServiceImpl<ZdataLocationDictMapper, ZdataLocationDict> implements IZdataLocationDictService {

    @Autowired
    private ZdataLocationDictMapper zdataLocationDictMapper;

    /**
     * 查询车辆位置
     *
     * @param id 车辆位置ID
     * @return 车辆位置
     */
    @Override
    public ZdataLocationDict selectZdataLocationDictById(Long id) {
        return zdataLocationDictMapper.selectZdataLocationDictById(id);
    }

    /**
     * 查询车辆位置列表
     *
     * @param zdataLocationDict 车辆位置
     * @return 车辆位置
     */
    @Override
    public List<ZdataLocationDict> selectZdataLocationDictList(ZdataLocationDict zdataLocationDict) {
        return zdataLocationDictMapper.selectZdataLocationDictList(zdataLocationDict);
    }





}
