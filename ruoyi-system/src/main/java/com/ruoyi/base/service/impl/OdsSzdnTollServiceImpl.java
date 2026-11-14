package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsSzdnTollMapper;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.service.IOdsSzdnTollService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费站基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsSzdnTollServiceImpl extends ServiceImpl<OdsSzdnTollMapper, OdsSzdnToll> implements IOdsSzdnTollService {

    @Autowired
    private OdsSzdnTollMapper odsSzdnTollMapper;

    /**
     * 查询收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 收费站基础信息
     */
    @Override
    public OdsSzdnToll selectOdsSzdnTollById(String id) {
        return odsSzdnTollMapper.selectOdsSzdnTollById(id);
    }

    /**
     * 查询收费站基础信息列表
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 收费站基础信息
     */
    @Override
    public List<OdsSzdnToll> selectOdsSzdnTollList(OdsSzdnToll odsSzdnToll) {
        return odsSzdnTollMapper.selectOdsSzdnTollList(odsSzdnToll);
    }


    /**
     * 新增或者修改收费站基础信息
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsSzdnToll(OdsSzdnToll odsSzdnToll)
    {
        if (CommonUtil.isNotBlank(odsSzdnToll.getId()))
        {
            // 修改
            odsSzdnTollMapper.updateById(odsSzdnToll);
        }
        else
        {
            // 新增 主键
            odsSzdnTollMapper.insert(odsSzdnToll);
        }
        return AjaxResult.success("操作成功！",odsSzdnToll.getId());
    }

    /**
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsSzdnTollByIds(String[] ids)
    {
        int count = odsSzdnTollMapper.deleteOdsSzdnTollByIds(ids);
        return AjaxResult.success(count);
    }

    @Override
    public void truncateTable() {
        odsSzdnTollMapper.truncateTable();
    }

    /**
     * 删除收费站基础信息信息
     *
     * @param id 收费站基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsSzdnTollById(String id)
    {
        int count = odsSzdnTollMapper.deleteOdsSzdnTollById(id);
        return AjaxResult.success(count);
    }

    /**
     * 查询收费站基础信息列表
     *
     * @param odsSzdnToll 收费站基础信息
     * @return 收费站基础信息集合
     */
    public List<OdsSzdnToll> selectOdsSzdnTollListNew(OdsSzdnToll odsSzdnToll){
        return odsSzdnTollMapper.selectOdsSzdnTollListNew(odsSzdnToll);
    }

}
