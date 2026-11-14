package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.DwdLcztSfzjcxx;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 收费站基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IDwdLcztSfzjcxxService extends IService<DwdLcztSfzjcxx> {
    /**
     * 查询收费站基础信息
     *
     * @param agentPk 收费站基础信息ID
     * @return 收费站基础信息
     */
    DwdLcztSfzjcxx selectDwdLcztSfzjcxxById(String agentPk);

    /**
     * 查询收费站基础信息列表
     *
     * @param dwdLcztSfzjcxx 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<DwdLcztSfzjcxx> selectDwdLcztSfzjcxxList(DwdLcztSfzjcxx dwdLcztSfzjcxx);


    /**
     * 新增或者修改收费站基础信息
     *
     * @param dwdLcztSfzjcxx 收费站基础信息
     * @return 结果
     */
    AjaxResult saveDwdLcztSfzjcxx(DwdLcztSfzjcxx dwdLcztSfzjcxx);

    /**
     * 批量删除收费站基础信息
     *
     * @param agentPks 需要删除的收费站基础信息ID
     * @return 结果
     */
    AjaxResult deleteDwdLcztSfzjcxxByIds(String[] agentPks);

    void truncateTable();

}
