package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsSzdnSectionMapper;
import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.service.IOdsSzdnSectionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 路段信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsSzdnSectionServiceImpl extends ServiceImpl<OdsSzdnSectionMapper, OdsSzdnSection> implements IOdsSzdnSectionService {

    @Autowired
    private OdsSzdnSectionMapper odsSzdnSectionMapper;

    /**
     * 查询路段信息
     *
     * @param id 路段信息ID
     * @return 路段信息
     */
    @Override
    public OdsSzdnSection selectOdsSzdnSectionById(String id) {
        return odsSzdnSectionMapper.selectOdsSzdnSectionById(id);
    }

    /**
     * 查询路段信息列表
     *
     * @param odsSzdnSection 路段信息
     * @return 路段信息
     */
    @Override
    public List<OdsSzdnSection> selectOdsSzdnSectionList(OdsSzdnSection odsSzdnSection) {
        return odsSzdnSectionMapper.selectOdsSzdnSectionList(odsSzdnSection);
    }


    /**
     * 新增或者修改路段信息
     *
     * @param odsSzdnSection 路段信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsSzdnSection(OdsSzdnSection odsSzdnSection)
    {
        if (CommonUtil.isNotBlank(odsSzdnSection.getId()))
        {
            // 修改
            odsSzdnSectionMapper.updateById(odsSzdnSection);
        }
        else
        {
            // 新增 主键
            odsSzdnSectionMapper.insert(odsSzdnSection);
        }
        return AjaxResult.success("操作成功！",odsSzdnSection.getId());
    }

    /**
     * 批量删除路段信息
     *
     * @param ids 需要删除的路段信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsSzdnSectionByIds(String[] ids)
    {
        int count = odsSzdnSectionMapper.deleteOdsSzdnSectionByIds(ids);
        return AjaxResult.success(count);
    }

    @Override
    public void truncateTable() {
        odsSzdnSectionMapper.truncateTable();
    }

    /**
     * 删除路段信息信息
     *
     * @param id 路段信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsSzdnSectionById(String id)
    {
        int count = odsSzdnSectionMapper.deleteOdsSzdnSectionById(id);
        return AjaxResult.success(count);
    }


    /**
     * 查询路段信息列表
     *
     * @param odsSzdnSection 路段信息
     * @return 路段信息集合
     */
    public List<OdsSzdnSection> selectOdsSzdnSectionListNew(OdsSzdnSection odsSzdnSection){
        return odsSzdnSectionMapper.selectOdsSzdnSectionListNew(odsSzdnSection);
    }



}
