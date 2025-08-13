package com.ruoyi.system.service.impl;

import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.system.domain.SysNotice;
import com.ruoyi.system.mapper.SysNoticeMapper;
import com.ruoyi.system.service.ISysFileService;
import com.ruoyi.system.service.ISysNoticeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 公告 服务层实现
 *
 * @author ruoyi
 */
@Service
public class SysNoticeServiceImpl implements ISysNoticeService {
    @Autowired
    private SysNoticeMapper noticeMapper;

    @Autowired
    private ISysFileService fileService;


    /**
     * 查询公告信息
     *
     * @param noticeId 公告ID
     * @return 公告信息
     */
    @Override
    public SysNotice selectNoticeById(Long noticeId) {
        SysNotice sysNotice = noticeMapper.selectNoticeById(noticeId);

        return sysNotice;
    }

    /**
     * 查询公告列表
     *
     * @param notice 公告信息
     * @return 公告集合
     */
    @Override
    public List<SysNotice> selectNoticeList(SysNotice notice) {
        return noticeMapper.selectNoticeList(notice);
    }

    /**
     * 新增公告
     *
     * @param notice 公告信息
     * @return 结果
     */
    @Override
    public int insertNotice(SysNotice notice) {
        notice.setNoticeType("1");
        notice.setCreateBy(SecurityUtils.getUserId() + ""); // 创建人
        notice.setTenantId(SecurityUtils.getTenantId()); // 当前租户
        return noticeMapper.insertNotice(notice);
    }

    /**
     * 修改公告
     *
     * @param notice 公告信息
     * @return 结果
     */
    @Override
    public int updateNotice(SysNotice notice) {
        // 修改
        notice.setUpdateBy(SecurityUtils.getUserId() + ""); // 更新人
        // 处理富文本中的图片信息
        /*if (StringUtils.isNotBlank(notice.getNoticeContent())) {
            String richText = fileService.uploadBase64Picture(notice.getNoticeContent());
            if (StringUtils.isNotBlank(richText)) {
                notice.setNoticeContent(richText);
            }
        }*/
        return noticeMapper.updateNotice(notice);
    }

    /**
     * 删除公告对象
     *
     * @param noticeId 公告ID
     * @return 结果
     */
    @Override
    public int deleteNoticeById(Long noticeId) {
        return noticeMapper.deleteNoticeById(noticeId);
    }

    /**
     * 批量删除公告信息
     *
     * @param noticeIds 需要删除的公告ID
     * @return 结果
     */
    @Override
    public int deleteNoticeByIds(Long[] noticeIds) {
        return noticeMapper.deleteNoticeByIds(noticeIds);
    }

    //新增到货时间异常提的通知公告

    @Override
    public Long addDeliveryTimeAbnormal(SysNotice notice) {
        //内容相同的不重复新增 bussId存收消息人的userid
        List<SysNotice> sysNoticeList = noticeMapper.selectNoticeList(notice);
        if (sysNoticeList.size() == 0) {
            notice.setCreateBy(SecurityUtils.getUserId() + ""); // 创建人
            notice.setTenantId(SecurityUtils.getTenantId()); // 当前租户
            notice.setNoticeType("1");
            notice.setStatus("0");
            noticeMapper.insertNotice(notice);
        } else {
            notice = sysNoticeList.get(0);
        }
        return notice.getNoticeId();
    }
}
