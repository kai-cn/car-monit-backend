package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsYhglVBaseOrgMapper;
import com.ruoyi.base.domain.OdsYhglVBaseOrg;
import com.ruoyi.base.service.IOdsYhglVBaseOrgService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 机构信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsYhglVBaseOrgServiceImpl extends ServiceImpl<OdsYhglVBaseOrgMapper, OdsYhglVBaseOrg> implements IOdsYhglVBaseOrgService {

    @Autowired
    private OdsYhglVBaseOrgMapper odsYhglVBaseOrgMapper;

    /**
     * 查询机构信息
     *
     * @param bigId 机构信息ID
     * @return 机构信息
     */
    @Override
    public OdsYhglVBaseOrg selectOdsYhglVBaseOrgById(String bigId) {
        return odsYhglVBaseOrgMapper.selectOdsYhglVBaseOrgById(bigId);
    }

    /**
     * 查询机构信息列表
     *
     * @param odsYhglVBaseOrg 机构信息
     * @return 机构信息
     */
    @Override
    public List<OdsYhglVBaseOrg> selectOdsYhglVBaseOrgList(OdsYhglVBaseOrg odsYhglVBaseOrg) {
        return odsYhglVBaseOrgMapper.selectOdsYhglVBaseOrgList(odsYhglVBaseOrg);
    }


    /**
     * 新增或者修改机构信息
     *
     * @param odsYhglVBaseOrg 机构信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsYhglVBaseOrg(OdsYhglVBaseOrg odsYhglVBaseOrg)
    {
        if (CommonUtil.isNotBlank(odsYhglVBaseOrg.getBigId()))
        {
            // 修改
            odsYhglVBaseOrgMapper.updateById(odsYhglVBaseOrg);
        }
        else
        {
            // 新增 主键
            odsYhglVBaseOrgMapper.insert(odsYhglVBaseOrg);
        }
        return AjaxResult.success("操作成功！",odsYhglVBaseOrg.getBigId());
    }

    /**
     * 批量删除机构信息
     *
     * @param bigIds 需要删除的机构信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsYhglVBaseOrgByIds(String[] bigIds)
    {
        int count = odsYhglVBaseOrgMapper.deleteOdsYhglVBaseOrgByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除机构信息信息
     *
     * @param bigId 机构信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsYhglVBaseOrgById(String bigId)
    {
        int count = odsYhglVBaseOrgMapper.deleteOdsYhglVBaseOrgById(bigId);
        return AjaxResult.success(count);
    }



}
