package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsSzdnGantryMapper;
import com.ruoyi.base.domain.OdsSzdnGantry;
import com.ruoyi.base.service.IOdsSzdnGantryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsSzdnGantryServiceImpl extends ServiceImpl<OdsSzdnGantryMapper, OdsSzdnGantry> implements IOdsSzdnGantryService {

    @Autowired
    private OdsSzdnGantryMapper odsSzdnGantryMapper;

    /**
     * 查询门架信息
     *
     * @param id 门架信息ID
     * @return 门架信息
     */
    @Override
    public OdsSzdnGantry selectOdsSzdnGantryById(String id) {
        return odsSzdnGantryMapper.selectOdsSzdnGantryById(id);
    }

    /**
     * 查询门架信息列表
     *
     * @param odsSzdnGantry 门架信息
     * @return 门架信息
     */
    @Override
    public List<OdsSzdnGantry> selectOdsSzdnGantryList(OdsSzdnGantry odsSzdnGantry) {
        return odsSzdnGantryMapper.selectOdsSzdnGantryList(odsSzdnGantry);
    }


    /**
     * 新增或者修改门架信息
     *
     * @param odsSzdnGantry 门架信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsSzdnGantry(OdsSzdnGantry odsSzdnGantry)
    {
        if (CommonUtil.isNotBlank(odsSzdnGantry.getId()))
        {
            // 修改
            odsSzdnGantryMapper.updateById(odsSzdnGantry);
        }
        else
        {
            // 新增 主键
            odsSzdnGantryMapper.insert(odsSzdnGantry);
        }
        return AjaxResult.success("操作成功！",odsSzdnGantry.getId());
    }

    /**
     * 批量删除门架信息
     *
     * @param ids 需要删除的门架信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsSzdnGantryByIds(String[] ids)
    {
        int count = odsSzdnGantryMapper.deleteOdsSzdnGantryByIds(ids);
        return AjaxResult.success(count);
    }

    @Override
    public void truncateTable() {
        odsSzdnGantryMapper.truncateTable();
    }

    /**
     * 删除门架信息信息
     *
     * @param id 门架信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsSzdnGantryById(String id)
    {
        int count = odsSzdnGantryMapper.deleteOdsSzdnGantryById(id);
        return AjaxResult.success(count);
    }


    /**
     * 查询门架信息列表
     *
     * @param odsSzdnGantry 门架信息
     * @return 门架信息集合
     */
    public List<OdsSzdnGantry> selectOdsSzdnGantryListNew(OdsSzdnGantry odsSzdnGantry){
        return odsSzdnGantryMapper.selectOdsSzdnGantryListNew(odsSzdnGantry);
    }



}
