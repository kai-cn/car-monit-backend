package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.BussTest;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 业务测试Mapper接口
 *
 * @author ruoyi
 * @date 2024-09-06
 */
@Repository
public interface BussTestMapper extends BaseMapper<BussTest> {
    /**
     * 查询业务测试
     *
     * @param id 业务测试ID
     * @return 业务测试
     */
    BussTest selectBussTestById(String id);

    /**
     * 查询业务测试列表
     *
     * @param bussTest 业务测试
     * @return 业务测试集合
     */
    List<BussTest> selectBussTestList(BussTest bussTest);

    /**
     * 批量删除业务测试
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteBussTestByIds(String[] ids);

    /**
     * 删除业务测试
     *
     * @param id 业务测试ID
     * @return 结果
     */
    int deleteBussTestById(String id);

}
