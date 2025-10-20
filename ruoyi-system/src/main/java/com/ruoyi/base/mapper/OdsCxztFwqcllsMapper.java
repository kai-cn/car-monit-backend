package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsCxztFwqclls;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 服务区车辆流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-10-20
 */
@Repository
public interface OdsCxztFwqcllsMapper extends BaseMapper<OdsCxztFwqclls> {
    /**
     * 查询服务区车辆流水
     *
     * @param bigId 服务区车辆流水ID
     * @return 服务区车辆流水
     */
    OdsCxztFwqclls selectOdsCxztFwqcllsById(Long bigId);

    /**
     * 查询服务区车辆流水列表
     *
     * @param odsCxztFwqclls 服务区车辆流水
     * @return 服务区车辆流水集合
     */
    List<OdsCxztFwqclls> selectOdsCxztFwqcllsList(OdsCxztFwqclls odsCxztFwqclls);


}
