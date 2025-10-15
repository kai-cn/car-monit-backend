package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.ZdataTrailFittingMapper;
import com.ruoyi.base.domain.ZdataTrailFitting;
import com.ruoyi.base.service.IZdataTrailFittingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 车辆出入口拟合轨迹Service业务层处理
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Service
public class ZdataTrailFittingServiceImpl extends ServiceImpl<ZdataTrailFittingMapper, ZdataTrailFitting> implements IZdataTrailFittingService {

    @Autowired
    private ZdataTrailFittingMapper zdataTrailFittingMapper;

    /**
     * 查询车辆出入口拟合轨迹
     *
     * @param cid 车辆出入口拟合轨迹ID
     * @return 车辆出入口拟合轨迹
     */
    @Override
    public ZdataTrailFitting selectZdataTrailFittingById(String cid) {
        return zdataTrailFittingMapper.selectZdataTrailFittingById(cid);
    }

    /**
     * 查询车辆出入口拟合轨迹列表
     *
     * @param zdataTrailFitting 车辆出入口拟合轨迹
     * @return 车辆出入口拟合轨迹
     */
    @Override
    public List<ZdataTrailFitting> selectZdataTrailFittingList(ZdataTrailFitting zdataTrailFitting) {
        return zdataTrailFittingMapper.selectZdataTrailFittingList(zdataTrailFitting);
    }






}
