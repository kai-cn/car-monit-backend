package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 门架抓拍流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsRtSzdnSnapshotFlowAddcodeService extends IService<OdsRtSzdnSnapshotFlowAddcode> {
    /**
     * 查询门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 门架抓拍流水
     */
    OdsRtSzdnSnapshotFlowAddcode selectOdsRtSzdnSnapshotFlowAddcodeById(String bigId);

    /**
     * 查询门架抓拍流水列表
     *
     * @param odsRtSzdnSnapshotFlowAddcode 门架抓拍流水
     * @return 门架抓拍流水集合
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectOdsRtSzdnSnapshotFlowAddcodeList(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);


    /**
     * 新增或者修改门架抓拍流水
     *
     * @param odsRtSzdnSnapshotFlowAddcode 门架抓拍流水
     * @return 结果
     */
    AjaxResult saveOdsRtSzdnSnapshotFlowAddcode(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 批量删除门架抓拍流水
     *
     * @param bigIds 需要删除的门架抓拍流水ID
     * @return 结果
     */
    AjaxResult deleteOdsRtSzdnSnapshotFlowAddcodeByIds(String[] bigIds);

}
