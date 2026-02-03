package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseConfigServiceArea;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 服务区Mapper接口
 *
 * @author ruoyi
 * @date 2026-02-02
 */
@Repository
public interface BaseConfigServiceAreaMapper extends BaseMapper<BaseConfigServiceArea> {
    /**
     * 查询服务区
     *
     * @param fwqbm 服务区ID
     * @return 服务区
     */
    BaseConfigServiceArea selectBaseConfigServiceAreaById(String fwqbm);

    /**
     * 查询服务区列表
     *
     * @param baseConfigServiceArea 服务区
     * @return 服务区集合
     */
    List<BaseConfigServiceArea> selectBaseConfigServiceAreaList(BaseConfigServiceArea baseConfigServiceArea);

    /**
     * 批量删除服务区
     *
     * @param fwqbms 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseConfigServiceAreaByIds(String[] fwqbms);

    /**
     * 删除服务区
     *
     * @param fwqbm 服务区ID
     * @return 结果
     */
    int deleteBaseConfigServiceAreaById(String fwqbm);

}
