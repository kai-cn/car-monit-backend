package com.ruoyi.quartz.task;

import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.*;
import com.ruoyi.base.service.forest.HttpBaseInfoApiService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.redis.RedisCache;
import lombok.extern.log4j.Log4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.util.List;

@Log4j
@Component("vehicleMonitoringTask")
public class VehicleMonitoringTask {

    @Resource
    private HttpBaseInfoApiService httpBaseInfoApiService;

    @Autowired
    private IOdsSzdnSectionService odsSzdnSectionService;
    @Autowired
    private IOdsYhglVBaseOrgService odsYhglVBaseOrgService;
    @Autowired
    private IOdsSzdnGantryService odsSzdnGantryService;
    @Autowired
    private IOdsSzdnTollService odsSzdnTollService;
    @Autowired
    private IDwdLcztSfzjcxxService dwdLcztSfzjcxxService;
    @Autowired
    private IDwdLcztFwqjcxxService dwdLcztFwqjcxxService;
    @Autowired
    private IDwdLcztSfsjcxxService dwdLcztSfsjcxxService;
    @Autowired
    private RedisCache redisCache;


    /**
     * 同步机构信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncOrgInfo() {
        List<OdsYhglVBaseOrg> list = httpBaseInfoApiService.getOrgInfoList();
        this.odsYhglVBaseOrgService.truncateTable();
        this.odsYhglVBaseOrgService.saveBatch(list);
    }


    /**
     * 同步路段信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSectionInfo(){
        List<OdsSzdnSection> list = httpBaseInfoApiService.getSectionInfoList();
        // 清空数据  mybatis-plus 安全机制 会对delete语句没有where条件的进行拦截
        // 抛出 Prohibition of full table deletion
        // 使用 注解 @Update  绕够MP的安全检测
        this.odsSzdnSectionService.truncateTable();
        // 全量新增数据
        this.odsSzdnSectionService.saveBatch(list);
        redisCache.setCacheList(Constants.SECTION_LIST, list);
    }



    /**
     * 同步门架信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncGantryInfo(){
        List<OdsSzdnGantry> list = httpBaseInfoApiService.getGantryInfoList();
        this.odsSzdnGantryService.truncateTable();
        this.odsSzdnGantryService.saveBatch(list);
    }


    /**
     * 同步服务区信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncServiceAreaInfoInfo(){
        List<DwdLcztFwqjcxx> list = httpBaseInfoApiService.getServiceAreaInfoList();
        this.dwdLcztFwqjcxxService.truncateTable();
        this.dwdLcztFwqjcxxService.saveBatch(list);
    }

    /**
     * 同步收费所信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncTollBoothInfoInfo(){
        List<DwdLcztSfsjcxx> list = httpBaseInfoApiService.getTollBoothInfoList();
        this.dwdLcztSfsjcxxService.truncateTable();
        this.dwdLcztSfsjcxxService.saveBatch(list);
    }

    /**
     * 同步收费站基础信息位置
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSfzjcxxInfoInfo(){
        List<DwdLcztSfzjcxx> list = httpBaseInfoApiService.getSfzjcxxInfoList();
        this.dwdLcztSfzjcxxService.truncateTable();
        this.dwdLcztSfzjcxxService.saveBatch(list);
    }

    /**
     * 同步收费站信息
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncTollStationInfo(){
        List<OdsSzdnToll> list = httpBaseInfoApiService.getTollStationInfoList();
        this.odsSzdnTollService.truncateTable();
        this.odsSzdnTollService.saveBatch(list);
    }



}
