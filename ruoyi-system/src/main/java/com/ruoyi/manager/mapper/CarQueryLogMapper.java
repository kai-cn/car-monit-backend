package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarQueryLog;
import com.ruoyi.manager.domain.vo.QueryLogVO;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 查询日志Mapper接口
 *
 * @author fzq
 * @date 2025-12-22
 */
@Repository
public interface CarQueryLogMapper extends BaseMapper<CarQueryLog> {
    /**
     * 查询查询日志
     *
     * @param id 查询日志ID
     * @return 查询日志
     */
    CarQueryLog selectCarQueryLogById(String id);

    /**
     * 查询查询日志列表
     *
     * @param carQueryLog 查询日志
     * @return 查询日志集合
     */
    List<CarQueryLog> selectCarQueryLogList(CarQueryLog carQueryLog);

    /**
     * 批量删除查询日志
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarQueryLogByIds(String[] ids);

    /**
     * 删除查询日志
     *
     * @param id 查询日志ID
     * @return 结果
     */
    int deleteCarQueryLogById(String id);
	
	List<CarQueryLog> getCarStatics(QueryLogVO queryLogVO);
}
