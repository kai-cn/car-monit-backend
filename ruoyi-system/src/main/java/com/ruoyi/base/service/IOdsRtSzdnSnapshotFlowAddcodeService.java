package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;
import com.ruoyi.manager.domain.vo.bigscreen.TopTenVO;

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

    List<TopTenVO> getTopTen();

    /**
     * 按时间范围统计路段预警 Top10。
     *
     * @param startTime 开始时间（yyyy-MM-dd）
     * @param endTime   结束时间（yyyy-MM-dd）
     * @return Top10
     */
    List<TopTenVO> getTopTen(String startTime, String endTime);
}
