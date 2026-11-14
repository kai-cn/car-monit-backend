package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowProvcaptureAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 省界抓拍Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Service
public class OdsRtSzdnSnapshotFlowProvcaptureAddcodeServiceImpl extends ServiceImpl<OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper, OdsRtSzdnSnapshotFlowProvcaptureAddcode> implements IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService {

    @Autowired
    private OdsRtSzdnSnapshotFlowProvcaptureAddcodeMapper odsRtSzdnSnapshotFlowProvcaptureAddcodeMapper;

    /**
     * 查询省界抓拍
     *
     * @param bigId 省界抓拍ID
     * @return 省界抓拍
     */
    @Override
    public OdsRtSzdnSnapshotFlowProvcaptureAddcode selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeById(Long bigId) {
        return odsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeById(bigId);
    }

    /**
     * 查询省界抓拍列表
     *
     * @param odsRtSzdnSnapshotFlowProvcaptureAddcode 省界抓拍
     * @return 省界抓拍
     */
    @Override
    public List<OdsRtSzdnSnapshotFlowProvcaptureAddcode> selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeList(OdsRtSzdnSnapshotFlowProvcaptureAddcode odsRtSzdnSnapshotFlowProvcaptureAddcode) {
        return odsRtSzdnSnapshotFlowProvcaptureAddcodeMapper.selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeList(odsRtSzdnSnapshotFlowProvcaptureAddcode);
    }





}
