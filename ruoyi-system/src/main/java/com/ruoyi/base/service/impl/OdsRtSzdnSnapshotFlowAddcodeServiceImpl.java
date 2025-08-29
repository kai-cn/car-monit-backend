package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowAddcodeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架抓拍流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Service
public class OdsRtSzdnSnapshotFlowAddcodeServiceImpl extends ServiceImpl<OdsRtSzdnSnapshotFlowAddcodeMapper, OdsRtSzdnSnapshotFlowAddcode> implements IOdsRtSzdnSnapshotFlowAddcodeService {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper odsRtSzdnSnapshotFlowAddcodeMapper;

    /**
     * 查询门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 门架抓拍流水
     */
    @Override
    public OdsRtSzdnSnapshotFlowAddcode selectOdsRtSzdnSnapshotFlowAddcodeById(String bigId) {
        return odsRtSzdnSnapshotFlowAddcodeMapper.selectOdsRtSzdnSnapshotFlowAddcodeById(bigId);
    }

    /**
     * 查询门架抓拍流水列表
     *
     * @param odsRtSzdnSnapshotFlowAddcode 门架抓拍流水
     * @return 门架抓拍流水
     */
    @Override
    public List<OdsRtSzdnSnapshotFlowAddcode> selectOdsRtSzdnSnapshotFlowAddcodeList(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode) {
        return odsRtSzdnSnapshotFlowAddcodeMapper.selectOdsRtSzdnSnapshotFlowAddcodeList(odsRtSzdnSnapshotFlowAddcode);
    }


    /**
     * 新增或者修改门架抓拍流水
     *
     * @param odsRtSzdnSnapshotFlowAddcode 门架抓拍流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveOdsRtSzdnSnapshotFlowAddcode(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode)
    {
        if (CommonUtil.isNotBlank(odsRtSzdnSnapshotFlowAddcode.getBigId()))
        {
            // 修改
            odsRtSzdnSnapshotFlowAddcodeMapper.updateById(odsRtSzdnSnapshotFlowAddcode);
        }
        else
        {
            // 新增 主键
            odsRtSzdnSnapshotFlowAddcodeMapper.insert(odsRtSzdnSnapshotFlowAddcode);
        }
        return AjaxResult.success("操作成功！",odsRtSzdnSnapshotFlowAddcode.getBigId());
    }

    /**
     * 批量删除门架抓拍流水
     *
     * @param bigIds 需要删除的门架抓拍流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteOdsRtSzdnSnapshotFlowAddcodeByIds(String[] bigIds)
    {
        int count = odsRtSzdnSnapshotFlowAddcodeMapper.deleteOdsRtSzdnSnapshotFlowAddcodeByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除门架抓拍流水信息
     *
     * @param bigId 门架抓拍流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteOdsRtSzdnSnapshotFlowAddcodeById(String bigId)
    {
        int count = odsRtSzdnSnapshotFlowAddcodeMapper.deleteOdsRtSzdnSnapshotFlowAddcodeById(bigId);
        return AjaxResult.success(count);
    }



}
