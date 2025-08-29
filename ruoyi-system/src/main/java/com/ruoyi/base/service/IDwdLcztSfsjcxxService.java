package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.DwdLcztSfsjcxx;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费所基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IDwdLcztSfsjcxxService extends IService<DwdLcztSfsjcxx> {
    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    DwdLcztSfsjcxx selectDwdLcztSfsjcxxById(String agentPk);

    /**
     * 查询收费所基础信息列表
     *
     * @param dwdLcztSfsjcxx 收费所基础信息
     * @return 收费所基础信息集合
     */
    List<DwdLcztSfsjcxx> selectDwdLcztSfsjcxxList(DwdLcztSfsjcxx dwdLcztSfsjcxx);


    /**
     * 新增或者修改收费所基础信息
     *
     * @param dwdLcztSfsjcxx 收费所基础信息
     * @return 结果
     */
    AjaxResult saveDwdLcztSfsjcxx(DwdLcztSfsjcxx dwdLcztSfsjcxx);

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的收费所基础信息ID
     * @return 结果
     */
    AjaxResult deleteDwdLcztSfsjcxxByIds(String[] agentPks);

}
