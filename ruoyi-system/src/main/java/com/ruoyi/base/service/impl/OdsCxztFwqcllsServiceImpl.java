package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.mapper.OdsCxztFwqcllsMapper;
import com.ruoyi.base.domain.OdsCxztFwqclls;
import com.ruoyi.base.service.IOdsCxztFwqcllsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 服务区车辆流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-10-20
 */
@Service
public class OdsCxztFwqcllsServiceImpl extends ServiceImpl<OdsCxztFwqcllsMapper, OdsCxztFwqclls> implements IOdsCxztFwqcllsService {

    @Autowired
    private OdsCxztFwqcllsMapper odsCxztFwqcllsMapper;

    /**
     * 查询服务区车辆流水
     *
     * @param bigId 服务区车辆流水ID
     * @return 服务区车辆流水
     */
    @Override
    public OdsCxztFwqclls selectOdsCxztFwqcllsById(Long bigId) {
        return odsCxztFwqcllsMapper.selectOdsCxztFwqcllsById(bigId);
    }

    /**
     * 查询服务区车辆流水列表
     *
     * @param odsCxztFwqclls 服务区车辆流水
     * @return 服务区车辆流水
     */
    @Override
    public List<OdsCxztFwqclls> selectOdsCxztFwqcllsList(OdsCxztFwqclls odsCxztFwqclls) {
        return odsCxztFwqcllsMapper.selectOdsCxztFwqcllsList(odsCxztFwqclls);
    }




}
