package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseGantrySnapshotFlow;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 门架抓拍流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseGantrySnapshotFlowService extends IService<BaseGantrySnapshotFlow> {
    /**
     * 查询门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 门架抓拍流水
     */
    BaseGantrySnapshotFlow selectBaseGantrySnapshotFlowById(String bigId);

    /**
     * 查询门架抓拍流水列表
     *
     * @param baseGantrySnapshotFlow 门架抓拍流水
     * @return 门架抓拍流水集合
     */
    List<BaseGantrySnapshotFlow> selectBaseGantrySnapshotFlowList(BaseGantrySnapshotFlow baseGantrySnapshotFlow);


    /**
     * 新增或者修改门架抓拍流水
     *
     * @param baseGantrySnapshotFlow 门架抓拍流水
     * @return 结果
     */
    AjaxResult saveBaseGantrySnapshotFlow(BaseGantrySnapshotFlow baseGantrySnapshotFlow);

    /**
     * 批量删除门架抓拍流水
     *
     * @param bigIds 需要删除的门架抓拍流水ID
     * @return 结果
     */
    AjaxResult deleteBaseGantrySnapshotFlowByIds(String[] bigIds);

}
