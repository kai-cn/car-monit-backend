package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.GantryCarMapper;
import com.ruoyi.manager.domain.GantryCar;
import com.ruoyi.manager.service.IGantryCarService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架拍识查询Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class GantryCarServiceImpl extends ServiceImpl<GantryCarMapper, GantryCar> implements IGantryCarService {

    @Autowired
    private GantryCarMapper gantryCarMapper;

    /**
     * 查询门架拍识查询
     *
     * @param id 门架拍识查询ID
     * @return 门架拍识查询
     */
    @Override
    public GantryCar selectGantryCarById(String id) {
        return gantryCarMapper.selectGantryCarById(id);
    }

    /**
     * 查询门架拍识查询列表
     *
     * @param gantryCar 门架拍识查询
     * @return 门架拍识查询
     */
    @Override
    public List<GantryCar> selectGantryCarList(GantryCar gantryCar) {
        return gantryCarMapper.selectGantryCarList(gantryCar);
    }


    /**
     * 新增或者修改门架拍识查询
     *
     * @param gantryCar 门架拍识查询
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveGantryCar(GantryCar gantryCar)
    {
        if (CommonUtil.isNotBlank(gantryCar.getId()))
        {
            // 修改
            gantryCarMapper.updateById(gantryCar);
        }
        else
        {
            // 新增 主键
            gantryCarMapper.insert(gantryCar);
        }
        return AjaxResult.success("操作成功！",gantryCar.getId());
    }

    /**
     * 批量删除门架拍识查询
     *
     * @param ids 需要删除的门架拍识查询ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteGantryCarByIds(String[] ids)
    {
        int count = gantryCarMapper.deleteGantryCarByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除门架拍识查询信息
     *
     * @param id 门架拍识查询ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteGantryCarById(String id)
    {
        int count = gantryCarMapper.deleteGantryCarById(id);
        return AjaxResult.success(count);
    }



}
