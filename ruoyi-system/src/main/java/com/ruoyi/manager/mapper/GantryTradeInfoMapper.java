package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.GantryTradeInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 门架交易查询Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface GantryTradeInfoMapper extends BaseMapper<GantryTradeInfo> {
    /**
     * 查询门架交易查询
     *
     * @param id 门架交易查询ID
     * @return 门架交易查询
     */
    GantryTradeInfo selectGantryTradeInfoById(String id);

    /**
     * 查询门架交易查询列表
     *
     * @param gantryTradeInfo 门架交易查询
     * @return 门架交易查询集合
     */
    List<GantryTradeInfo> selectGantryTradeInfoList(GantryTradeInfo gantryTradeInfo);

    /**
     * 批量删除门架交易查询
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteGantryTradeInfoByIds(String[] ids);

    /**
     * 删除门架交易查询
     *
     * @param id 门架交易查询ID
     * @return 结果
     */
    int deleteGantryTradeInfoById(String id);

}
