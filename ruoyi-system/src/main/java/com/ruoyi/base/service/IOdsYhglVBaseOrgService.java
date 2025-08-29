package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsYhglVBaseOrg;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 机构信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsYhglVBaseOrgService extends IService<OdsYhglVBaseOrg> {
    /**
     * 查询机构信息
     *
     * @param bigId 机构信息ID
     * @return 机构信息
     */
    OdsYhglVBaseOrg selectOdsYhglVBaseOrgById(String bigId);

    /**
     * 查询机构信息列表
     *
     * @param odsYhglVBaseOrg 机构信息
     * @return 机构信息集合
     */
    List<OdsYhglVBaseOrg> selectOdsYhglVBaseOrgList(OdsYhglVBaseOrg odsYhglVBaseOrg);


    /**
     * 新增或者修改机构信息
     *
     * @param odsYhglVBaseOrg 机构信息
     * @return 结果
     */
    AjaxResult saveOdsYhglVBaseOrg(OdsYhglVBaseOrg odsYhglVBaseOrg);

    /**
     * 批量删除机构信息
     *
     * @param bigIds 需要删除的机构信息ID
     * @return 结果
     */
    AjaxResult deleteOdsYhglVBaseOrgByIds(String[] bigIds);

}
