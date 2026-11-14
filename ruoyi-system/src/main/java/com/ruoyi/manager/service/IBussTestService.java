package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.BussTest;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 业务测试Service接口
 *
 * @author ruoyi
 * @date 2024-09-06
 */
public interface IBussTestService extends IService<BussTest> {
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
     * 新增或者修改业务测试
     *
     * @param bussTest 业务测试
     * @return 结果
     */
    AjaxResult saveBussTest(BussTest bussTest);

    /**
     * 批量删除业务测试
     *
     * @param ids 需要删除的业务测试ID
     * @return 结果
     */
    AjaxResult deleteBussTestByIds(String[] ids);

}
