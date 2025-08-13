package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.BussTestMapper;
import com.ruoyi.manager.domain.BussTest;
import com.ruoyi.manager.service.IBussTestService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 业务测试Service业务层处理
 *
 * @author ruoyi
 * @date 2024-09-06
 */
@Service
public class BussTestServiceImpl extends ServiceImpl<BussTestMapper, BussTest> implements IBussTestService {

    @Autowired
    private BussTestMapper bussTestMapper;

    /**
     * 查询业务测试
     *
     * @param id 业务测试ID
     * @return 业务测试
     */
    @Override
    public BussTest selectBussTestById(String id) {
        return bussTestMapper.selectBussTestById(id);
    }

    /**
     * 查询业务测试列表
     *
     * @param bussTest 业务测试
     * @return 业务测试
     */
    @Override
    public List<BussTest> selectBussTestList(BussTest bussTest) {
        return bussTestMapper.selectBussTestList(bussTest);
    }


    /**
     * 新增或者修改业务测试
     *
     * @param bussTest 业务测试
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBussTest(BussTest bussTest)
    {
        if (CommonUtil.isNotBlank(bussTest.getId()))
        {
            // 修改
            bussTestMapper.updateById(bussTest);
        }
        else
        {
            // 新增 主键
            bussTestMapper.insert(bussTest);
        }
        return AjaxResult.success("操作成功！",bussTest.getId());
    }

    /**
     * 批量删除业务测试
     *
     * @param ids 需要删除的业务测试ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBussTestByIds(String[] ids)
    {
        int count = bussTestMapper.deleteBussTestByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除业务测试信息
     *
     * @param id 业务测试ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBussTestById(String id)
    {
        int count = bussTestMapper.deleteBussTestById(id);
        return AjaxResult.success(count);
    }



}
