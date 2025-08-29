package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.DwdLcztFwqjcxx;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 服务区基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IDwdLcztFwqjcxxService extends IService<DwdLcztFwqjcxx> {
    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    DwdLcztFwqjcxx selectDwdLcztFwqjcxxById(String agentPk);

    /**
     * 查询服务区基础信息列表
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 服务区基础信息集合
     */
    List<DwdLcztFwqjcxx> selectDwdLcztFwqjcxxList(DwdLcztFwqjcxx dwdLcztFwqjcxx);


    /**
     * 新增或者修改服务区基础信息
     *
     * @param dwdLcztFwqjcxx 服务区基础信息
     * @return 结果
     */
    AjaxResult saveDwdLcztFwqjcxx(DwdLcztFwqjcxx dwdLcztFwqjcxx);

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的服务区基础信息ID
     * @return 结果
     */
    AjaxResult deleteDwdLcztFwqjcxxByIds(String[] agentPks);

}
